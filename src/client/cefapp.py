import logging
import numpy as np
from pubsub import pub
import cefpyco
from multiprocessing import Process
from piece import Piece
from pieces_manager import PiecesManager
from block import State


PROTOCOL = 'ccnx:/BitTorrent'
CHUNK_SIZE = 1024 * 4
MAX_PIECE=1000


class CefAppConsumer(Process):
    last_log_line = ""
    def __init__(self, pieces_manager,
                 pipeline=1000, timeout_limit=10):
        Process.__init__(self)
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()
        self.pieces_manager: PiecesManager = pieces_manager
        self.pieces: [Piece] = pieces_manager.pieces
        self.name: [str] = '/'.join([PROTOCOL,
                                     self.pieces_manager.torrent.info_hash_str])
        self.info_hash = self.pieces_manager.torrent.info_hash_str
        self.number_of_pieces = self.pieces_manager.number_of_pieces
        self.piece_length = self.pieces_manager.torrent.piece_length
        self.chunk_count = self.piece_length // CHUNK_SIZE

        self.timeout_count = 0
        self.timeout_limit = timeout_limit

        self.pipeline = pipeline
        self.req_flag = np.zeros(self.number_of_pieces)
        # test
        self.interests = []
        self.data_size = 0

    def run(self):
        self.on_start()
        while self.pieces_manager.complete_pieces != self.number_of_pieces:
            packet = self.cef_handle.receive()
            if packet.is_failed:
                self.on_rcv_failed()
            elif packet.name.split('/')[2] == self.info_hash:
                self.on_rcv_succeeded(packet)
        if self.pieces_manager.complete_pieces == self.number_of_pieces:
            return True
        else:
            return False

    def on_start(self):
        count = min(MAX_PIECE, len(self.pieces))
        for piece_index in range(count):
            interest = self.create_interest(piece_index, 0)
            name, chunk = interest
            self.req_flag[piece_index] = 1
            self.cef_handle.send_interest(name, chunk)

    def create_interest(self, index, chunk_num):
        name = '/'.join([self.name, str(index)])
        interest = (name, chunk_num)
        return interest

    def search_next_piece(self):
        for piece_index in range(len(self.pieces)):
            if self.req_flag[piece_index] == 1 or self.pieces[piece_index].is_full:
                continue
            return piece_index
        return None

    def search_empty_block(self, piece_index):
        piece = self.pieces[piece_index]
        for index in range(piece.number_of_blocks):
            if piece.blocks[index].state != State.FULL:
                return  index
        return None

    def on_rcv_failed(self):
        logging.debug("receive failed")
        self.req_flag = np.zeros(self.pieces_manager.number_of_pieces)

        self.send_with_pipeline()

    def on_rcv_succeeded(self, packet):
        piece_index = int(packet.name.split('/')[-1])
        chunk = packet.chunk_num

        piece_data = (piece_index, chunk*CHUNK_SIZE, packet.payload)
        self.pieces_manager.receive_block_piece(piece_data)

        if self.pieces[piece_index].is_full:
            self.display_progression()
            next_piece_index = self.search_next_piece()
            if next_piece_index is None:
                return
            interest = self.create_interest(next_piece_index, 0)
            self.req_flag[next_piece_index] = 1
        else:
            if chunk == packet.end_chunk_num:
                chunk = self.search_empty_block(piece_index)
                interest = self.create_interest(piece_index, chunk)
            else:
                interest = self.create_interest(piece_index, chunk + 1)

        name, chunk = interest
        self.cef_handle.send_interest(name, chunk)

    def send_with_pipeline(self):
        count = 0
        for piece in self.pieces:
            if count >= MAX_PIECE:
                break

            if piece.is_full:
                continue

            if piece.blocks[0].state == State.FULL:
                chunk = self.search_empty_block(piece.piece_index)
                if chunk is None:
                    continue
                interest = self.create_interest(piece.piece_index, chunk)
                name, chunk = interest
                self.cef_handle.send_interest(name, chunk)
                count += 1
            else:
                interest = self.create_interest(piece.piece_index, 0)
                name, _ = interest
                self.cef_handle.send_interest(name, 0)
                count += 1

    def display_progression(self):

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            print(current_log_line)

        self.last_log_line = current_log_line

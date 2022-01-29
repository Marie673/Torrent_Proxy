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
MAX_PIECE=10


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
        self.data_size = 0

    def run(self):
        self.get_first_chunk()
        while self.pieces_manager.complete_pieces != self.number_of_pieces:
            packet = self.cef_handle.receive()
            if packet.is_failed:
                self.on_rcv_failed()
            elif packet.name.split('/')[2] == self.info_hash:
                self.on_rcv_succeeded(packet)
            # self.display_progression()
        if self.pieces_manager.complete_pieces == self.number_of_pieces:
            return True
        else:
            return False

    def create_interest(self, index):
        return '/'.join([self.name, str(index)])

    def get_first_chunk(self):
        count = 0
        for piece_index in range(self.number_of_pieces):
            piece = self.pieces[piece_index]

            # have first chunk
            if piece.is_full or piece.blocks[0].state == State.FULL:
                continue

            interest = self.create_interest(piece_index)
            self.cef_handle.send_interest(interest, 0)
            count += 1

            if count > MAX_PIECE:
                return

    def get_follow_pieces(self, piece_index):
        piece = self.pieces[piece_index]
        for chunk in range(len(piece.blocks)):
            if piece.blocks[chunk].state == State.FULL:
                continue
            interest = self.create_interest(piece_index)
            self.cef_handle.send_interest(interest, chunk)

    def on_rcv_failed(self):
        logging.debug("receive failed")
        count = 0
        for piece_index in range(self.number_of_pieces):
            piece = self.pieces[piece_index]
            if piece.is_full:
                continue

            # have first chunk
            # proxy have a piece
            if piece.blocks[0].state == State.FULL:
                interest = self.create_interest(piece_index)
                self.get_follow_pieces(piece_index)
                logging.debug("get follow pieces")
                count += 1
            else:
                # send first chunk interest
                interest = self.create_interest(piece_index)
                self.cef_handle.send_interest(interest, 0)
                logging.debug("send first chunk")
                count += 1

            if count > MAX_PIECE:
                break

    def on_rcv_succeeded(self, packet):
        piece_index = int(packet.name.split('/')[-1])
        chunk = packet.chunk_num

        piece = (piece_index, chunk*CHUNK_SIZE, packet.payload)
        print("{} {} {}".format(piece_index, chunk, chunk*CHUNK_SIZE))
        self.pieces_manager.receive_block_piece(piece)

        if chunk == 0:
            self.get_follow_pieces(piece_index)
        else:
            if self.pieces[piece_index].is_full:
                self.get_first_chunk()

    def display_progression(self):

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            print(current_log_line)

        self.last_log_line = current_log_line

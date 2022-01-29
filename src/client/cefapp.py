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
MAX_PIECE=30


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

    def send_interests(self):
        for interest in self.interests:
            name, chunk_num = interest
            self.cef_handle.send_interest(name, chunk_num)
        self.interests = []

    def create_interest(self, index, chunk_num):
        name = '/'.join([self.name, str(index)])
        interest = (name, chunk_num)
        return interest

    def get_first_chunk(self):
        for piece_index in range(self.number_of_pieces):
            piece = self.pieces[piece_index]

            # have first chunk
            if piece.is_full or piece.blocks[0].state == State.FULL:
                continue

            interest = self.create_interest(piece_index, 0)
            self.interests.append(interest)

            if len(self.interests) >= MAX_PIECE:
                self.send_interests()
                return

    def get_follow_pieces(self, piece_index):
        piece = self.pieces[piece_index]
        for chunk in range(len(piece.blocks)):
            if piece.blocks[chunk].state == State.FULL:
                continue
            interest = self.create_interest(piece_index, chunk)
            self.interests.append(interest)

    def on_rcv_failed(self):
        logging.debug("receive failed")
        req_piece = 0
        for piece_index in range(self.number_of_pieces):
            piece = self.pieces[piece_index]
            if piece.is_full:
                continue

            # have first chunk
            # proxy have a piece
            if piece.blocks[0].state == State.FULL:
                self.get_follow_pieces(piece_index)
                req_piece += 1
                logging.debug("get follow pieces")
            else:
                # send first chunk interest
                interest = self.create_interest(piece_index, 0)
                self.interests.append(interest)
                req_piece += 1
                logging.debug("send first chunk")

            if req_piece >= MAX_PIECE:
                self.send_interests()
                return

    def on_rcv_succeeded(self, packet):
        piece_index = int(packet.name.split('/')[-1])
        chunk = packet.chunk_num

        piece = (piece_index, chunk*CHUNK_SIZE, packet.payload)
        self.pieces_manager.receive_block_piece(piece)

        if chunk == 0:
            self.get_follow_pieces(piece_index)
        else:
            if self.pieces[piece_index].is_full:
                self.get_first_chunk()
            else:
                self.get_follow_pieces(piece_index)

    def display_progression(self):

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            print(current_log_line)

        self.last_log_line = current_log_line

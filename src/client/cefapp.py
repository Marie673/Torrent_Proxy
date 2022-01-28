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
MAX_PIECE=5


class CefAppConsumer(Process):
    def __init__(self, pieces_manager,
                 pipeline=1000, timeout_limit=10):
        Process.__init__(self)
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()
        self.pieces_manager: PiecesManager = pieces_manager
        self.pieces: [Piece] = pieces_manager.pieces
        self.name: [str] = '/'.join([PROTOCOL,
                                     self.pieces_manager.torrent.info_hash_str])
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
            elif packet.name.split('/')[:3] == self.name:
                self.on_rcv_succeeded(packet)

        if self.pieces_manager.complete_pieces == self.number_of_pieces:
            return True
        else:
            return False

    def create_interest(self, index):
        return '/'.join([self.name, str(index)])

    def get_first_chunk(self):
        for piece_index in range(self.number_of_pieces):
            piece = self.pieces[piece_index]
            if piece.is_full or piece.blocks[0].state == State.FULL:
                continue
            interest = self.create_interest(piece_index)
            self.cef_handle.send_interest(interest, 0)

    def on_rcv_failed(self):
        for piece_index in range(self.number_of_pieces):
            piece = self.pieces[piece_index]
            if piece.is_full:
                continue
            for chunk in range(self.chunk_count):
                block = piece.blocks[chunk]
                if block.state == State.FULL:
                    continue
                else:
                    interest = self.create_interest(piece_index)
                    self.cef_handle.send_interest(interest, chunk)

    def on_rcv_succeeded(self, packet):
        piece_index = packet.name.split('/')[-1]
        chunk_num = packet.chunk_num
        piece = (piece_index, chunk_num*CHUNK_SIZE, packet.payload)
        self.pieces_manager.receive_block_piece(piece)

        if chunk_num != packet.end_chunk_num:
            self.cef_handle.send_interest(packet.name, chunk_num + 1)
        else:
            self.get_first_chunk()
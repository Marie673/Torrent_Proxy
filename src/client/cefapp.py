import logging
import numpy as np
from pubsub import pub
import cefpyco
from multiprocessing import Process
from piece import Piece
from pieces_manager import PiecesManager


PROTOCOL = 'ccnx:/BitTorrent'
CHUNK_SIZE = 1024 * 4
MAX_PIECE=30


class CefAppConsumer(Process):
    def __init__(self, pieces_manager,
                 pipeline=1000, timeout_limit=10):
        Process.__init__(self)
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()

        self.pieces_manager: PiecesManager = pieces_manager
        self.name: [str] = '/'.join([PROTOCOL,
                                     self.pieces_manager.torrent.info_hash_str])

        self.chunk_count = self.pieces_manager.torrent.piece_length // CHUNK_SIZE

        self.timeout_count = 0
        self.timeout_limit = timeout_limit

        self.rcv_tail_index = None
        self.req_tail_index = None
        self.req_flag = None
        self.pipeline = pipeline

        # test
        self.data_size = 0

    def run(self):
        self.on_start()

        while self.timeout_count < self.timeout_limit and self.continues_to_run():
            packet = self.cef_handle.receive()
            if packet.is_failed:
                # info.timeout_count += 1
                self.on_rcv_failed()
            elif packet.name.split('/')[2] == self.pieces_manager.torrent.info_hash_str:
                self.on_rcv_succeeded(packet)
        if self.pieces_manager.number_of_pieces == self.pieces_manager.complete_pieces:
            print("success download")
            return True
        else:
            return False

    def on_start(self):
        for index in range(MAX_PIECE):
            interest = '/'.join([self.name, str(index)])
            self.cef_handle.send_interest(interest, 0)
            print(interest)

    def get_first_chunks(self):
        for piece in self.pieces_manager.pieces:
            index = piece.piece_index
            if piece.is_full:
                continue
            piece.update_block_status()

            interest = '/'.join([self.name, str(index)])
            self.cef_handle.send_interest(interest, 0)
            return

    def get_follow_pieces(self, piece_index):
        for chunk in range(1, self.chunk_count):
            interest = '/'.join([self.name, str(piece_index)])
            self.cef_handle.send_interest(interest, chunk)

    def continues_to_run(self):
        return self.pieces_manager.number_of_pieces != self.pieces_manager.complete_pieces

    def on_rcv_failed(self):
        self.get_first_chunks()

    def on_rcv_succeeded(self, packet):
        piece_index = int(packet.name.split('/')[-1])
        piece_offset = packet.chunk_num * CHUNK_SIZE
        piece_data = packet.payload
        piece = piece_index, piece_offset, piece_data

        self.pieces_manager.receive_block_piece(piece)

        if piece_index == 0:
            self.get_follow_pieces(piece_index)
        else:
            self.pieces_manager.pieces[piece_index].update_block_status()
            self.get_first_chunks()

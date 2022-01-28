import logging
import numpy as np
from pubsub import pub
import cefpyco
from multiprocessing import Process
from piece import Piece
from pieces_manager import PiecesManager


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
        self.name: [str] = '/'.join([PROTOCOL,
                                     self.pieces_manager.torrent.info_hash_str])
        self.number_of_pieces = self.pieces_manager.number_of_pieces
        self.piece_length = self.pieces_manager.torrent.piece_length
        self.chunk_count = self.piece_length // CHUNK_SIZE

        self.timeout_count = 0
        self.timeout_limit = timeout_limit

        self.rcv_tail_index = None
        self.req_tail_index = None
        self.pipeline = pipeline

        self.req_flag = np.zeros(self.number_of_pieces)
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
            self.req_flag[index] = 1
            for chunk in range(self.chunk_count):
                self.cef_handle.send_interest(interest, chunk)
                print("{} Chunk={}".format(interest, chunk))

    def send_next_interest(self):
        for index in range(self.number_of_pieces):
            if self.req_flag[index] == 1:
                continue
            interest = '/'.join([self.name, str(index)])
            for chunk in range(self.chunk_count):
                self.cef_handle.send_interest(interest, chunk)
                print("{} Chunk={}".format(interest, chunk))
            return

    def continues_to_run(self):
        return self.pieces_manager.number_of_pieces != self.pieces_manager.complete_pieces

    def on_rcv_failed(self):
        self.reset_req_status()

    def on_rcv_succeeded(self, packet):
        # logging.debug("{} Chunk={}".format(packet.name, packet.chunk_num))
        piece_index = int(packet.name.split('/')[-1])
        piece_offset = packet.chunk_num * CHUNK_SIZE
        piece_data = packet.payload
        piece = piece_index, piece_offset, piece_data
        self.pieces_manager.receive_block_piece(piece)

        if self.pieces_manager.bitfield[piece_index] == 1:
            self.send_next_interest()

    def reset_req_status(self):
        self.req_flag = self.pieces_manager.bitfield

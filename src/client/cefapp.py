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
        self.number_of_pieces = self.pieces_manager.number_of_pieces
        self.piece_length = self.pieces_manager.torrent.piece_length
        self.chunk_count = self.piece_length // CHUNK_SIZE
        self.all_block_count = self.number_of_pieces * self.chunk_count

        self.timeout_count = 0
        self.timeout_limit = timeout_limit

        self.rcv_tail_index = None
        self.req_tail_index = None
        self.req_flag = np.zeros(self.all_block_count)
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
        self.req_flag = np.zeros(self.all_block_count)
        self.rcv_tail_index = 0
        self.req_tail_index = 0
        self.send_interests_with_pipeline()

    def send_interests_with_pipeline(self):
        to_index = min(self.all_block_count, self.req_tail_index + self.pipeline)
        for i in range(self.req_tail_index, to_index):
            index = i // self.piece_length
            chunk = (i % self.piece_length) // CHUNK_SIZE
            if self.pieces_manager.pieces[index].is_full: continue
            interest = '/'.join([self.name, str(index)])
            self.cef_handle.send_interest(interest, chunk)
            self.req_flag[i] = 1

    def send_next_interest(self):
        while self.req_tail_index < self.all_block_count and self.pieces_manager.bitfield[self.rcv_tail_index]:
            self.req_tail_index += 1
        while (self.req_tail_index < self.all_block_count and
                self.pieces_manager.bitfield[self.req_tail_index] or self.req_flag[self.req_tail_index]):
            self.req_tail_index += 1
        if self.req_tail_index < self.all_block_count:
            index = self.req_tail_index //self.piece_length
            chunk = (self.req_tail_index % self.piece_length) // CHUNK_SIZE
            interest = '/'.join([self.name, str(index)])
            self.cef_handle.send_interest(interest, chunk)

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

        self.send_next_interest()

    def reset_req_status(self):
        self.req_flag = np.zeros(self.all_block_count)
        self.req_tail_index = self.rcv_tail_index
        while self.req_tail_index < self.all_block_count \
                and self.pieces_manager.bitfield[self.req_tail_index]:
            self.req_tail_index += 1
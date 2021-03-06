import logging
import time

import numpy
from pubsub import pub
import cefpyco
from multiprocessing import Process
from piece import Piece
from pieces_manager import PiecesManager
from block import State


PROTOCOL = 'ccnx:/BitTorrent'
CHUNK_SIZE = 1024 * 4
MAX_PIECE=50


class CefAppConsumer:
    last_log_line = ""
    def __init__(self, pieces_manager,
                 pipeline=1000, timeout_limit=10):
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()

        self.pieces_manager: PiecesManager = pieces_manager
        self.pieces: [Piece] = pieces_manager.pieces
        self.info_hash = self.pieces_manager.torrent.info_hash_str
        self.number_of_pieces = self.pieces_manager.number_of_pieces
        self.piece_length = self.pieces_manager.torrent.piece_length
        self.chunk_num = self.piece_length // CHUNK_SIZE

        self.name: [str] = '/'.join([PROTOCOL,
                                     self.pieces_manager.torrent.info_hash_str])

        self.bitfield = [0 for _ in range(self.number_of_pieces)]
        # test
        self.data_size = 0

    def run(self):
        self.on_start()
        while self.pieces_manager.complete_pieces != self.number_of_pieces:
            packet = self.cef_handle.receive(timeout_ms=1000)
            if packet.is_failed:
                self.on_rcv_failed()
            elif packet.name.split('/')[2] == self.info_hash:
                self.on_rcv_succeeded(packet)
        if self.pieces_manager.complete_pieces == self.number_of_pieces:
            return True
        else:
            return False

    def create_interest(self, index):
        name = '/'.join([self.name, str(index)])
        return name

    def on_start(self):
        for piece in self.pieces:
            index = piece.piece_index
            name = self.create_interest(index)
            self.cef_handle.send_interest(name, 0)
            if index >= MAX_PIECE:
                break
        self.get_piece(0)

    def get_piece(self, index):
        name = self.create_interest(index)
        for chunk in range(self.chunk_num):
            # logging.debug("{} {}".format(name, chunk))
            self.cef_handle.send_interest(name, chunk)

    def on_rcv_failed(self):
        logging.debug("on rcv failed")

        for piece in self.pieces:
            if piece.is_full:
                continue
            self.get_piece(piece.piece_index)
            return

    def on_rcv_succeeded(self, packet):
        piece_index = int(packet.name.split('/')[-1])
        chunk = packet.chunk_num

        if chunk == 0:
            self.bitfield[piece_index] = 1
            if piece_index + MAX_PIECE < self.number_of_pieces:
                name = self.create_interest(piece_index + MAX_PIECE)
                self.cef_handle.send_interest(name, 0)
        # logging.debug("{} {}".format(piece_index, chunk*CHUNK_SIZE))
        piece_data = (piece_index, chunk*CHUNK_SIZE, packet.payload)
        self.pieces_manager.receive_block_piece(piece_data)

        self.display_progression()

        if chunk == packet.end_chunk_num:
            next_piece_index = piece_index + 1
            if next_piece_index < self.number_of_pieces:
                self.get_piece(next_piece_index)

    def display_progression(self):

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            logging.info(current_log_line)

        self.last_log_line = current_log_line

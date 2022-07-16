import logging
import queue
import threading
import time
from queue import Queue
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor
import cefpyco
import bitstring

from piece import Piece
from pieces_manager import PiecesManager
from torrent import Torrent

PROTOCOL = 'ccnx:/BitTorrent'
CHUNK_SIZE = 1024 * 4
MAX_PIECE = 1
TIME_OUT = 5


class BitfieldThread(Thread):
    def __init__(self, torrent: Torrent):
        super().__init__()
        self.torrent = torrent
        self.info_hash = self.torrent.info_hash_str
        self.bitfield = bitstring.BitArray(self.torrent.number_of_pieces)
        self.health: bool = True

        self.name = '/'.join([PROTOCOL, self.info_hash, 'bitfield'])

        self.healthy = True

    def run(self) -> None:
        pre_time = time.time()
        while self.health:
            now_time = time.time()
            if now_time - pre_time > 5:
                self.do_update()
                pre_time = time.time()

    def get_bitfield(self, packet):
        chunk = packet.chunk_num
        end_chunk_num = packet.end_chunk_num
        payload: bytes = packet.payload
        bs = bitstring.BitArray(payload)

        self.bitfield.overwrite(bs=bs, pos=CHUNK_SIZE * chunk)

        if chunk != end_chunk_num:
            CefAppConsumer.cef_handle.send_interest(name=self.name, chunk_num=chunk + 1)

    def do_update(self):
        CefAppConsumer.cef_handle.send_interest(name=self.name, chunk_num=0)
        return


class Interest(Thread):
    def __init__(self, piece: Piece, name):
        super(Interest, self).__init__()
        self.piece = piece
        self.name = name

        self.last_receive_chunk = -1
        self.last_call_time = time.time()

        self.end_chunk_num = None

        self.healthy = True

    def run(self) -> None:
        print('test')
        CefAppConsumer.cef_handle.send_interest(self.name, 0)
        while (not self.piece.is_full) and self.healthy:
            now_time = time.time()
            if now_time - self.last_call_time > 5:
                self.get_next_chunk()

    def get_next_chunk(self):
        chunk = self.last_receive_chunk + 1

        CefAppConsumer.cef_handle.send_interest(self.name, chunk)
        print(self.name, chunk)
        self.last_call_time = time.time()

    def receive_piece(self, packet):
        chunk = packet.chunk_num
        self.last_receive_chunk = chunk
        self.end_chunk_num = packet.end_chunk_num

        piece_offset = chunk * CHUNK_SIZE
        piece_data = packet.payload
        if self.piece.is_full:
            return
        CefAppConsumer.data_size += len(piece_data)
        self.piece.set_block(piece_offset, piece_data)
        if chunk == self.end_chunk_num:
            return
        self.get_next_chunk()


class CefAppConsumer:
    cef_handle = cefpyco.CefpycoHandle()
    last_log_line = ""
    data_size = 0

    def __init__(self, pieces_manager):

        CefAppConsumer.cef_handle.begin()
        self.pieces_manager: PiecesManager = pieces_manager
        self.pieces: [Piece] = pieces_manager.pieces

        self.info_hash = self.pieces_manager.torrent.info_hash_str
        self.number_of_pieces = self.pieces_manager.number_of_pieces
        self.piece_length = self.pieces_manager.torrent.piece_length
        self.chunk_num = self.piece_length // CHUNK_SIZE

        self.name: [str] = '/'.join([PROTOCOL,
                                     self.pieces_manager.torrent.info_hash_str])

        self.bitfield = [0 for _ in range(self.number_of_pieces)]
        self.proxy_bitfield = BitfieldThread(self.pieces_manager.torrent)
        self.thread = {}
        # test
        self.data_size = 0

    def run(self):
        self.proxy_bitfield.start()
        self.on_start()

        start_time = prog_time = time.time()
        try:
            while self.pieces_manager.complete_pieces != self.number_of_pieces:
                packet = CefAppConsumer.cef_handle.receive(timeout_ms=2000)
                if packet.is_failed:
                    self.on_rcv_failed()
                else:
                    self.on_rcv_succeeded(packet)
                now_time = time.time()
                if (now_time - prog_time) > 1:
                    text = "\033[2J--------------------------------------------------------------------------\n" + \
                           str(now_time - start_time) + "[sec]\n" + \
                           str(CefAppConsumer.data_size) + "\n" + \
                           "completed | {}/{} pieces".format(
                               self.pieces_manager.complete_pieces,
                               self.pieces_manager.number_of_pieces) + '\n' + \
                           "------------------------------------------------------------------------------"
                    # print(text)
                    prog_time = now_time

            if self.pieces_manager.complete_pieces == self.number_of_pieces:
                return True
            else:
                return False

        except KeyboardInterrupt:
            for t in self.thread.values():
                t.healthy = False
            for t in threading.enumerate():
                t.join()

    def create_request_interest(self, index):
        name = '/'.join([self.name, 'request', str(index)])
        return name

    def on_start(self):
        for piece in self.pieces:
            if threading.active_count() > MAX_PIECE + 1:
                break
            name = '/'.join([PROTOCOL, self.info_hash, 'request', str(piece.piece_index)])
            if piece.piece_index in self.thread:
                continue
            else:
                t = Interest(piece, name)
                t.start()
                self.thread[name] = t

    def on_rcv_failed(self):
        logging.debug("on rcv failed")
        self.on_start()

    def on_rcv_succeeded(self, packet):
        name = packet.name
        prefix = name.split('/')
        '''
        prefix[0] = ccnx:
        prefix[1] = BitTorrent:
        prefix[2] = info_hash
        prefix[3] = message　-> request, bitfield
        prefix[4] = peace_index
        '''
        if prefix[2] != self.info_hash:
            logging.info('missing info_hash')

        message = prefix[3]
        if message == 'request':
            self.handle_request(packet)
        elif message == 'bitfield':
            self.proxy_bitfield.get_bitfield(packet)
        else:
            pass

    def handle_request(self, packet):
        print('test1')
        name = packet.name
        prefix = name.split('/')
        piece_index = int(prefix[4])
        print(packet.name)
        t = self.thread[name]
        t.receive_piece(packet)
        self.pieces_manager.receive_block_piece(piece_index)

    def display_progression(self):

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            logging.info(current_log_line)

        self.last_log_line = current_log_line

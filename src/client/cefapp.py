import logging
import time
from queue import Queue
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor
import cefpyco

from piece import Piece
from pieces_manager import PiecesManager
from torrent import Torrent

PROTOCOL = 'ccnx:/BitTorrent'
CHUNK_SIZE = 1024 * 4
MAX_PIECE = 500

cef_handle = cefpyco.CefpycoHandle()
cef_handle.begin()


class BitfieldThread(Thread):
    def __init__(self, torrent: Torrent):
        super().__init__()
        self.torrent = torrent
        self.info_hash = self.torrent.info_hash_str
        self.bitfield = [0 for _ in range(self.torrent.number_of_pieces)]
        self.health: bool = True
        self.queue = Queue()

        self.name = '/'.join([PROTOCOL, self.info_hash, 'bitfield'])
        self.end_chunk_num = -1

        self.packet = None

    def run(self) -> None:
        pre_time = time.time()
        while self.health:
            now_time = time.time()
            if now_time - pre_time > 5:
                self.do_update()
                print(self.bitfield)
                pre_time - time.time()

    def do_update(self):
        if self.end_chunk_num == -1:
            cef_handle.send_interest(name=self.name, chunk_num=0)
            packet = self.queue.get(timeout=5)
            self.queue.task_done()

            self.end_chunk_num = packet.end_chunk_num
            for i in range(CHUNK_SIZE):
                self.bitfield[i] = packet.payload[i]

        for chunk in range(self.end_chunk_num):
            cef_handle.send_interest(name=self.name, chunk_num=chunk)
            packet = self.queue.get()
            self.queue.task_done()

            chunk = packet.chunk_num
            for i in range(chunk*CHUNK_SIZE, (chunk+1)*CHUNK_SIZE):
                self.bitfield[i] = packet.payload[i]


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
        self.proxy_bitfield = BitfieldThread(self.pieces_manager.torrent)
        # test
        self.data_size = 0

    def run(self):
        self.proxy_bitfield.start()
        piece_thread = ThreadPoolExecutor(max_workers=MAX_PIECE)
        while True:
            packet = cef_handle.receive(timeout_ms=1000)
            if packet.is_failed:
                continue
            else:
                self.on_rcv_succeeded(packet)




        self.on_start()
        start_time = prog_time = time.time()
        while self.pieces_manager.complete_pieces != self.number_of_pieces:
            now_time = time.time()
            if (now_time - prog_time) > 1:
                text = "\033[2J--------------------------------------------------------------------------\n" + \
                       self.pieces_manager.str_bitfield() + '\n' + \
                       str(now_time - start_time) + "[sec]\n" + \
                       "completed | {}/{} pieces".format(self.pieces_manager.complete_pieces,
                                                         self.pieces_manager.number_of_pieces) + '\n' + \
                       "------------------------------------------------------------------------------"
                print(text)
                prog_time = now_time

            packet = self.cef_handle.receive(timeout_ms=1000)
            if packet.is_failed:
                self.on_rcv_failed()
            elif packet.name.split('/')[2] == self.info_hash:
                self.on_rcv_succeeded(packet)
        if self.pieces_manager.complete_pieces == self.number_of_pieces:
            return True
        else:
            return False


    def create_request_interest(self, index):
        name = '/'.join([self.name, 'request', str(index)])
        return name

    def on_start(self):
        for piece in self.pieces:
            index = piece.piece_index
            name = self.create_request_interest(index)
            self.cef_handle.send_interest(name, 0)
            if index >= MAX_PIECE:
                break
        self.get_piece(0)

    def get_bitfield(self):
        name = '/'.join([PROTOCOL, 'bitfield'])
        self.cef_handle.send_interest(name, 0)

        packet = self.cef_handle.receive()

    def handle_bitfield(self, packet):
        chunk = packet.chunk_num

        if chunk == 0:
            end_chunk_num = packet.end_chunk_num
            for num in range(1, end_chunk_num):
                self.cef_handle.send_interest(name=packet.name, chunk_num=num)

    def get_piece(self, index):
        name = self.create_request_interest(index)
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
        name = packet.name
        prefix = name.split('/')
        '''
        prefix[0] = ccnx:
        prefix[1] = BitTorrent:
        prefix[2] = message　-> request, bitfield
        prefix[3] = peace_index
        '''

        message = prefix[2]
        if message == 'request':
            pass
        elif message == 'bitfield':
            self.proxy_bitfield.queue.put(packet)
        else:
            pass

    def handle_request(self, packet):
        piece_index = int(packet.name.split('/')[-1])
        chunk = packet.chunk_num

        if chunk == 0:
            self.bitfield[piece_index] = 1
            if piece_index + MAX_PIECE < self.number_of_pieces:
                name = self.create_request_interest(piece_index + MAX_PIECE)
                self.cef_handle.send_interest(name, 0)
        # logging.debug("{} {}".format(piece_index, chunk*CHUNK_SIZE))
        piece_data = (piece_index, chunk * CHUNK_SIZE, packet.payload)
        self.pieces_manager.receive_block_piece(piece_data)

        # self.display_progression()

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

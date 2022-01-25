import time
import cefpyco
import logging
from pubsub import pub
import multiprocessing
from multiprocessing import Manager, Process, Queue

import downloader
import torrent

BLOCK_SIZE = 4096

PATH = ["/home/marie/Torrent_Proxy/test/1M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/100M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/1G.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10G.dummy.torrent"]


class Cef(object):
    def __init__(self):
        self.torrent = {}
        for path in PATH:
            t = torrent.Torrent()
            t.load_from_path(path)
            self.torrent[t.info_hash] = t

        self.runners = {}
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

        """
        実験用
        """
        self.queues = {}

    def send_interest(self, name, chunk_num=0):
        self.handle.send_interest(name, chunk_num)
        logging.debug('Send interest: {}'.format(name))

    def send_data(self, name, payload):
        # cache_time = 6000 # 50秒
        cache_time = 360000 # 1時間
        chunk_num = 0
        end_chunk_num = len(payload) // BLOCK_SIZE
        while payload:
            chunk = payload[:BLOCK_SIZE]
            self.handle.send_data(name=name, payload=chunk,
                                  chunk_num=chunk_num, end_chunk_num=end_chunk_num, cache_time=cache_time)
            payload = payload[BLOCK_SIZE:]
            chunk_num += 1

    def queue_manager(self, info_hash):
        piece_q: Queue = self.queues[info_hash][1]
        while True:
            piece = piece_q.get()
            index, payload = piece
            index = str(index)

            if index is None or payload is None:
                continue

            name = 'ccnx:/BitTorrent/' + info_hash + '/' + index
            self.send_data(name, payload)

    def handle_interest(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')
        info_hash = prefix[2]
        index = prefix[3]

        """実験用"""
        if info_hash not in self.queues or info_hash not in self.runners:
            logging.debug('create instance: {}'.format(info_hash))

            if info_hash not in self.torrent:
                return
            else:
                torrent = self.torrent[info_hash]

            request_q = Queue()
            piece_q = Queue()
            q = [request_q, piece_q]

            run_process = downloader.Run(torrent, q)
            run_process.start()

            self.queues[info_hash] = q
            self.runners[info_hash] = run_process

            q_manager = Process(target=self.queue_manager, args=(info_hash,))
            q_manager.start()

            logging.debug('downloader started')

        if info_hash in self.queues and info_hash in self.runners:
            queue = self.queues[info_hash]
            queue[0].put(int(index))
        """"""

    def handle_piece(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')
        index = prefix[4]
        pub.sendMessage('PiecesManager.Piece', piece=(index, 0, info.payload))

    def handle_torrent(self, info):
        prefix = info.name.split('/')
        uuid = prefix[4]
        interest = '/'.join(['ccnx:', uuid, 'BitTorrent', 'torrent'])
        logging.debug('send Interest: {}'.format(interest))
        self.send_interest(interest)

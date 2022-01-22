import time

import downloader

import cefpyco
import logging
from pubsub import pub
import multiprocessing
from multiprocessing import Manager, Process, Queue


BLOCK_SIZE = 4096


class Cef(object):
    def __init__(self, jikken):
        self.jikken = jikken
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

        chunk_num = 0
        end_chunk_num = len(payload) // BLOCK_SIZE
        while payload:
            chunk = payload[:BLOCK_SIZE]
            self.handle.send_data(name, chunk, chunk_num, end_chunk_num)
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

            name = 'ccnx:/BitTorrent/' + info_hash + '/request/' + index
            self.send_data(name, payload)


    def is_torrent(self, info: cefpyco.core.CcnPacketInfo):
        d = downloader.Run(info.payload)
        runner = downloader.Run(d)
        name = info.name.split('/')
        info_hash = name[4]
        self.runners[info_hash] = runner

        # threading.Thread(target=runner.start).start()

    def handle_request(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')
        info_hash = prefix[2]
        index = prefix[4]

        """実験用"""
        if info_hash not in self.runners:
            logging.debug('create instance: {}'.format(info_hash))

            request_q = Queue()
            piece_q = Queue()
            q = [request_q, piece_q]

            run_process = downloader.Run(q, self.jikken)
            run_process.start()

            self.queues[info_hash] = q
            self.runners[info_hash] = run_process

            q_manager = Process(target=self.queue_manager(info_hash))
            q_manager.start()

            logging.debug('downloader started')

        if info_hash in self.queues:
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

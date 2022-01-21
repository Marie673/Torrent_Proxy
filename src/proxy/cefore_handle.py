import time

import downloader

import cefpyco
import logging
from pubsub import pub
import multiprocessing
from multiprocessing import Manager, Process, Queue


class Cef(object):
    def __init__(self):
        self.runners = {}
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

        """
        実験用
        """
        self.pieces = {}

    def send_interest(self, name, chunk_num=0):
        self.handle.send_interest(name, chunk_num)
        logging.debug('Send interest: {}'.format(name))

    def send_data(self, name, payload, chunk_num=-1):
        chunk_num = 0
        end_chunk_num = len(payload) // 1024
        while payload:
            chunk = payload[:1024]
            self.handle.send_data(name, chunk, chunk_num, end_chunk_num)
            payload = payload[1024:]
            chunk_num += 1

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

        BITFIELD = 0
        PIECES = 1
        """実験用"""
        if info_hash not in self.runners and index == '0':
            logging.debug('create instance: {}'.format(info_hash))

            manager = Manager()
            m_list = manager.list([manager.list(), manager.list()])

            run_process = downloader.Run(m_list)
            run_process.start()

            self.pieces[info_hash] = m_list
            self.runners[info_hash] = run_process

            logging.debug('downloader started')
        """"""

        if info_hash in self.pieces:
            runner = self.runners[info_hash]
            m_list = self.pieces[info_hash]
            bitfield = m_list[BITFIELD]
            pieces  = m_list[PIECES]

            if bitfield[int(index)]:
                piece = pieces[int(index)]
                self.send_data(info.name, piece)

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

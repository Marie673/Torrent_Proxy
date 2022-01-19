import downloader

import cefpyco
import logging
import threading
from pubsub import pub


class Cef(object):
    def __init__(self):
        self.runners = {}
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

        """
        実験用
        """


    def send_interest(self, name, chunk_num=0):
        self.handle.send_interest(name, chunk_num)
        logging.debug('Send interest: {}'.format(name))

    def send_data(self, name, payload, chunk_num=-1):
        self.handle.send_data(name, payload, chunk_num)
        logging.debug('Send data: {}'.format(name))

    def is_torrent(self, info: cefpyco.core.CcnPacketInfo):
        d = downloader.Run(info.payload)
        print(d)
        runner = downloader.Run(d)
        name = info.name.split('/')
        info_hash = name[4]
        self.runners[info_hash] = runner

        threading.Thread(target=runner.start).start()

    def handle_request(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')
        info_hash = prefix[2]
        index = prefix[4]

        """実験用"""
        if info_hash not in self.runners.values() and index == '0':
            runner = downloader.Run()
            self.runners[info_hash] = runner
        """"""

        if info_hash in self.runners.values():
            runner: downloader.Run = self.runners[info_hash]
            if runner.pieces_manager.bitfield[index]:
                piece = runner.pieces_manager.pieces[index]
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

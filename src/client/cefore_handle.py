import torrent

import cefpyco
import logging
from pubsub import pub


class Cef(object):
    def __init__(self, torrent: torrent.Torrent):
        self.torrent = torrent

        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

    def send_interest(self, name, chunk_num=0):
        self.handle.send_interest(name, chunk_num)
        logging.debug('Send interest: {}'.format(name))

    def send_data(self, name, payload, chunk_num=-1):
        self.handle.send_data(name, payload, chunk_num)
        logging.debug('Send data: {}'.format(name))

    def handle_piece(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')
        index = prefix[4]
        pub.sendMessage('PiecesManager.Piece', piece=(index, 0, info.payload))

    def handle_torrent(self, info):
        with open(self.torrent.path, 'rb') as file:
            data = file.read()
        self.send_data(info.name, data)

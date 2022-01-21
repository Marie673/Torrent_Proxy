import torrent

import cefpyco
import logging
from pubsub import pub


class Cef(object):
    def __init__(self, torrent: torrent.Torrent):
        self.torrent = torrent

        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/client0')

    def send_interest(self, name, chunk_num=0):
        self.handle.send_interest(name, chunk_num)
        # logging.debug('Send interest: {}'.format(name))

    def send_data(self, name, payload, chunk_num=-1):
        self.handle.send_data(name, payload, chunk_num)
        # logging.debug('Send data: {}'.format(name))

    def handle_piece(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')
        index = int(prefix[4])
        chunk_num = info.chunk_num
        offset = chunk_num * 1024
        print(info.chunk_num)


        pub.sendMessage('PiecesManager.Piece', piece=(index, offset, info.payload))

    def handle_torrent(self, info):
        with open(self.torrent.path, 'rb') as file:
            data = file.read()
        self.send_data(info.name, data)

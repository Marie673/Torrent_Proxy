import logging

import cefpyco.core

import cefore_handle
import torrent

from threading import Thread


class CefManager(Thread):
    def __init__(self, torrent: torrent.Torrent):
        Thread.__init__(self)
        self.torrent = torrent
        self.cef = cefore_handle.Cef(self.torrent)

        self.is_active = True

    def run(self):
        while self.is_active:
            info = self.cef.handle.receive()
            if info.is_succeeded:
                self._process_new_message(info)

    def _process_new_message(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')

        if info.is_interest:
            logging.debug('Received Interest')

            if prefix[3] == 'torrent':
                self.cef.handle_torrent(info)

        if info.is_data:
            logging.debug('Received Data')
            self.cef.handle_piece(info)

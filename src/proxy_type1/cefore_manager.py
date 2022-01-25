import logging
import cefpyco.core

import cefore_handle
from threading import Thread


class CefManager(object):
    def __init__(self, jikken):
        self.cef = cefore_handle.Cef(jikken)

        self.is_active = True

    def run(self):
        logging.debug('Start cef manager')
        while self.is_active:
            info = self.cef.handle.receive()
            if info.is_succeeded:
                self._process_new_message(info)

    def _process_new_message(self, info: cefpyco.core.CcnPacketInfo):
        prefix = info.name.split('/')

        if info.is_interest:
            # logging.debug('Received Interest')

            self.cef.handle_request(info)

        if info.is_data:
            logging.debug('Received Data')

            if prefix[1] != 'BitTorrent':
                self.cef.is_torrent(info)
                return

import logging
import os.path
import sys
from multiprocessing import Queue
import cefpyco

import bittorrent_process
from torrent import Torrent

PATH = ["/home/marie/Torrent_Proxy/test/1M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/100M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/1G.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10G.dummy.torrent"]

SIZE = 1024 * 4

torrent = []
bittorrent_process_queues = []


class CefManager(object):
    def __init__(self):
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccn:/BitTorrent')

    def listening(self):
        while True:
            packet = self.handle.receive()
            if packet.is_failed:
                continue
            if packet.is_interest:
                self.handle_interest(packet)

    def handle_interest(self, packet):

        # parse interest name
        prefix = packet.name.split("/")
        info_hash = prefix[2]
        piece_index = int(prefix[3])

        if prefix[0] != 'ccnx:' and prefix[1] != 'BitTorrent':
            return

        if info_hash not in bittorrent_process_queues:
            if info_hash not in torrent:
                return
            else:
                self.create_new_bittorrent_process(info_hash)

        queue: Queue = bittorrent_process_queues[info_hash]
        queue.put(piece_index)

    @staticmethod
    def create_new_bittorrent_process(self, info_hash):
        queue = Queue()
        bittorrent_process_queues[info_hash] = queue

        process = bittorrent_process.Run(torrent[info_hash], queue)
        process.start()

    def send_piece_data(self, info_hash, index):
        pass

    def queue_manager(self):
        for info_hash, queue in bittorrent_process_queues:
            while not queue.empty():
                index = queue.get()
                self.send_piece_data(info_hash, index)



def main():
    cef_manager = CefManager()
    try:
        cef_manager.listening()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()

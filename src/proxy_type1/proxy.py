import logging
import os.path
import sys
import cefpyco
from multiprocessing import Queue

import cefore_manager
import downloader
import torrent

PATH = ["/home/marie/Torrent_Proxy/test/1M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/100M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/1G.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10G.dummy.torrent"]


class Run(object):
    def __init__(self):
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

        self.torrent = {}
        for path in PATH:
            t = torrent.Torrent()
            t.load_from_path(path)
            self.torrent[t.info_hash_str] = t

        self.download_process = {}
        self.request_q = {}
        self.piece_q = {}

    def create_new_process(self, info_hash):
        request_q = Queue()
        piece_q = Queue()
        self.request_q[info_hash] = request_q
        self.piece_q[info_hash] = piece_q
        queue = [request_q, piece_q]
        process = downloader.Run(self.torrent[info_hash], queue)
        self.request_q[info_hash] = request_q
        self.piece_q[info_hash] = piece_q
        self.download_process[info_hash] = process
        process.start()
        print('new process is running')

    def handle_interest(self, packet):
        print("interest: {} chunk = {}".format(packet.name), packet.chunk_num)
        prefix = packet.name.split("/")
        info_hash = prefix[2]
        piece_index = int(prefix[3])

        if info_hash not in self.download_process:
            self.create_new_process(info_hash)

        self.request_q[info_hash].put(piece_index)

    def start(self):
        while True:
            packet = self.handle.receive()
            if packet.is_failed:
                continue
            if packet.is_interest:
                self.handle_interest(packet)



def main():

    run = Run()
    try:
        run.start()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()

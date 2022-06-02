import logging
import os
import os.path
import sys
import time
from multiprocessing import Queue
import cefpyco

import downloader
from torrent import Torrent

HOME = os.environ['HOME']
PATH = [
        HOME + "/bittorrent/10M.dummy.torrent",
        HOME + "/bittorrent/100M.dummy.torrent",
        HOME + "/bittorrent/1024.dummy.torrent"
        ]


SIZE = 1024 * 4


class Run(object):
    def __init__(self):
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

        self.torrent = {}
        for path in PATH:
            t = Torrent()
            t.load_from_path(path)
            self.torrent[t.info_hash_str] = t

        self.download_process = {}
        self.request_q = {}
        self.piece_q = {}

    def create_new_process(self, info_hash):
        request_q = Queue()
        self.request_q[info_hash] = request_q

        process = downloader.Run(self.torrent[info_hash], request_q)
        process.start()

        self.download_process[info_hash] = process
        print('new process is running')

    def send_file(self, info, file_name):
        name = info.name
        chunk = info.chunk_num

        file_size = os.path.getsize(file_name)
        end_chunk_num = file_size // SIZE - 1
        cache_time = 10000
        seek = chunk * SIZE

        with open(file_name, "rb") as file:
            file.seek(seek)
            payload = file.read(SIZE)
            # logging.debug("name:{} chunk:{}".format(name, chunk))
            self.handle.send_data(name=name, payload=payload,
                                  chunk_num=chunk, end_chunk_num=end_chunk_num, cache_time=cache_time)

    def handle_interest(self, packet):
        prefix = packet.name.split("/")
        info_hash = prefix[2]
        piece_index = int(prefix[3])
        if prefix[0] != 'ccnx:' and prefix[1] != 'BitTorrent':
            return

        with open('~/exp/test.dat', mode='a') as file:
            text = 'interest:' + info_hash + ":" + \
                   str(piece_index) + ":" + packet.chunk_num + ":" + \
                   time.time()
            file.write(text)

        tmp_path = '/'.join(['tmp', info_hash, str(piece_index)])
        if os.path.exists(tmp_path):
            self.send_file(packet, tmp_path)
            with open('~/exp/test.dat', mode='a') as file:
                text = 'data:' + info_hash + ":" + \
                       str(piece_index) + ":" + packet.chunk_num + ":" + \
                       time.time()
                file.write(text)
            return

        if info_hash not in self.download_process:
            self.create_new_process(info_hash)
            self.request_q[info_hash].put(piece_index)
        else:
            if packet.chunk_num == 0:
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

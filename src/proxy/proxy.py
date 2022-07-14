import logging
import os
import os.path
import sys
import time
from multiprocessing import Queue

import bitstring
import cefpyco

import downloader
from torrent import Torrent

HOME = os.environ['HOME']
PATH = [
    HOME + "/torrent/torrent/128MB.dummy.torrent",
    HOME + "/torrent/torrent/256MB.dummy.torrent",
    HOME + "/torrent/torrent/512MB.dummy.torrent",
    HOME + "/torrent/torrent/1024MB.dummy.torrent",
    HOME + "/torrent/torrent/2048MB.dummy.torrent"
]
TEST_DAT = HOME + "/exp/test.dat"


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
        name = packet.name
        prefix = name.split("/")
        if prefix[0] != 'ccnx:' and prefix[1] != 'BitTorrent':
            return

        if prefix[1] == 'BitTorrent':
            info_hash = prefix[2]
            '''
            message protocol
                bitfield
                request
            '''
            message = prefix[3]
            if message == 'bitfield':
                logging.info("get bitfield message")
                torrent = self.torrent[info_hash]
                num_of_pieces = torrent.number_of_pieces
                bitfield = bitstring.BitArray(num_of_pieces)

                for i in range(num_of_pieces):
                    path = '/'.join(['tmp', info_hash, str(i)])
                    if os.path.exists(path):
                        bitfield[i] = 1
                    else:
                        bitfield[i] = 0

                bit_string = bitfield._readhex(bitfield.len, 0)
                self.handle.send_data(name=name, payload=bit_string,
                                      cache_time=0)

            if message == 'request':
                piece_index = int(prefix[4])
                with open(TEST_DAT, mode='a') as file:
                    text = 'interest,' + info_hash + "," + \
                           str(piece_index) + "," + str(packet.chunk_num) + "," + \
                           str(time.time()) + "\n"
                    file.write(text)

                tmp_path = '/'.join(['tmp', info_hash, str(piece_index)])
                if os.path.exists(tmp_path):
                    self.send_file(packet, tmp_path)
                    with open(TEST_DAT, mode='a') as file:
                        text = 'data,' + info_hash + "," + \
                               str(piece_index) + "," + str(packet.chunk_num) + "," + \
                               str(time.time()) + "\n"
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

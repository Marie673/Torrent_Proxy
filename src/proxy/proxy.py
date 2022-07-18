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
CACHE_TIME = 0

TEST_DAT = HOME + "/exp/test.dat"

SIZE = 1024 * 4


class Run(object):
    def __init__(self):
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

        self.torrent = {}
        self.bitfield = {}
        for path in PATH:
            t = Torrent()
            t.load_from_path(path)
            self.torrent[t.info_hash_str] = t
            self.bitfield[t.info_hash_str] = bitstring.BitArray(t.number_of_pieces)

        self.download_process = {}

    def create_new_process(self, info_hash):

        process = downloader.Run(self.torrent[info_hash])
        process.start()

        self.download_process[info_hash] = process
        print('new process is running')

    def send_file(self, info, file_name):
        name = info.name
        chunk = info.chunk_num

        file_size = os.path.getsize(file_name)
        end_chunk_num = file_size // SIZE - 1
        seek = chunk * SIZE

        with open(file_name, "rb") as file:
            file.seek(seek)
            payload = file.read(SIZE)
            # logging.debug("name:{} chunk:{}".format(name, chunk))
            if chunk == 0:
                print('send data', name)
            self.handle.send_data(name=name, payload=payload,
                                  chunk_num=chunk, end_chunk_num=end_chunk_num, cache_time=CACHE_TIME)

    def update_bitfield(self):
        for info_hash, bitfield in self.bitfield.items():
            num_of_pieces = self.torrent[info_hash].number_of_pieces

            for i in range(num_of_pieces):
                path = '/'.join(['tmp', info_hash, str(i)])
                if os.path.exists(path):
                    bitfield[i] = 1
                else:
                    bitfield[i] = 0

    def handle_interest(self, packet):
        name = packet.name
        prefix = name.split("/")
        if prefix[0] != 'ccnx:':
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
                bitfield = self.bitfield[info_hash]
                bitfield_bytes = bitfield.bytes
                chunk = packet.chunk_num

                size = len(bitfield_bytes)
                end_chunk_num = size // SIZE - 1

                payload = bitfield_bytes[chunk * SIZE:(chunk + 1) * SIZE]
                self.handle.send_data(name=name, payload=payload,
                                      chunk_num=chunk, end_chunk_num=end_chunk_num, cache_time=0)

            if message == 'request':
                piece_index = int(prefix[4])
                """
                #with open(TEST_DAT, mode='a') as file:
                    text = 'interest,' + info_hash + "," + \
                           str(piece_index) + "," + str(packet.chunk_num) + "," + \
                           str(time.time()) + "\n"
                    file.write(text)
                """

                tmp_path = '/'.join(['tmp', info_hash, str(piece_index)])
                if os.path.exists(tmp_path):
                    self.send_file(packet, tmp_path)
                    """
                    # with open(TEST_DAT, mode='a') as file:
                        text = 'data,' + info_hash + "," + \
                               str(piece_index) + "," + str(packet.chunk_num) + "," + \
                               str(time.time()) + "\n"
                        file.write(text)
                    """
                    return
                """    
                if info_hash not in self.download_process:
                    self.create_new_process(info_hash)
                else:
                    if packet.chunk_num == 0:
                        pass
                """

    def start(self):
        pre_time = time.time()
        # self.update_bitfield()
        while True:
            now_time = time.time()
            if now_time - pre_time > 10:
                pass
                # self.update_bitfield()

            packet = self.handle.receive()
            if packet.is_failed:
                print('failed')
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

import hashlib
import socket
import sys
import os
import bencodepy

import cefpyco

CEFORE_DIR = os.path.abspath("cefore")
bc = bencodepy.Bencode(
    encoding='utf-8',
    encoding_fallback='all',
)


def getLocalIP() -> str:
    host = socket.gethostname()
    ip = socket.gethostbyname(host)

    return ip


uuid = getLocalIP()
info_hash: bytes = b''

length = 0
piece_length = 0
piece_num = 0
source_file_name = ""


def sendData(handle: cefpyco.CefpycoHandle):
    with open(source_file_name, "rb") as source_file:

        read_data_size = 0
        for i in range(piece_num):
            source_file.seek(read_data_size)
            data = source_file.read(piece_length)
            handle.send_data("ccnx:/BitTorrent/" + str(info_hash.hex()), data, i)

            read_data_size = read_data_size + piece_length


def listener(handle: cefpyco.CefpycoHandle):
    reg = "ccnx:/BitTorrent/" + uuid + "/" + str(info_hash.hex())
    print(reg)
    handle.register(reg)
    print("start listening")
    while True:
        info = handle.receive()
        prefix = info.name.split('/')

        if info.is_interest:
            print("receive interest")
            sendData(handle)


def main():
    if len(sys.argv) != 3:
        print("Usage: {} <torrent_file> <source_file>".format(sys.argv[0]))
        exit(1)

    torrent_file_name = sys.argv[1]
    global source_file_name
    source_file_name = sys.argv[2]

    torrent_file = open(torrent_file_name, "rb").read()
    torrent_dict = bc.decode(torrent_file)
    info_dict: dict = torrent_dict['info']
    global length, piece_length, piece_num
    length = info_dict['length']
    piece_length = info_dict['piece length']
    piece_num = length // piece_length
    global info_hash
    info_hash = hashlib.sha1(bencodepy.encode(info_dict)).digest()

    with cefpyco.create_handle(enable_log=False, ceforedir=CEFORE_DIR) as handle:
        interest = "ccnx:/BitTorrent/havePiece/" + str(info_hash.hex()) + "/" + uuid

        print(interest)
        handle.send_interest(interest, 0)
        listener(handle)


if __name__ == "__main__":
    main()

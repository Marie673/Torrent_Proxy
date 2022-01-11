import sys
import bencodepy
import hashlib
import os
import cefpyco

CEFORE_DIR = os.path.abspath("cefore")
bc = bencodepy.Bencode(
    encoding='utf-8',
    encoding_fallback='all',
)


def main():
    if len(sys.argv) != 2:
        print("Usage: {} <torrent_file>".format(sys.argv[0]))
        exit(1)

    torrent_file_name = sys.argv[1]
    torrent_data = torrent_file_name.split('.')
    file_name = '.'.join(torrent_data[0:len(torrent_data) - 2])

    torrent_file = open(torrent_file_name, "rb").read()

    torrent_dict = bc.decode(torrent_file)
    info_dict: dict = torrent_dict['info']
    length: int = info_dict['length']
    piece_length: int = info_dict['piece length']
    piece_num: int = length // piece_length
    info_hash = hashlib.sha1(bencodepy.encode(info_dict)).digest()

    with cefpyco.create_handle(enable_log=False, ceforedir=CEFORE_DIR) as handle:
        handle.register("ccnx:/BitTorrent")

        path = '../download'
        os.mkdir(path)
        file_path = path + '/' + file_name
        open(file_path, "wb")

        for i in range(piece_num):
            handle.send_interest("ccnx:/BitTorrent/" + str(info_hash.hex()), i)
            info = handle.receive()
            prefix = info.name.split('/')

            if info.is_data:
                download_file = open(file_path, "ab")
                download_file.write(info.payload)


if __name__ == '__init__':
    main()

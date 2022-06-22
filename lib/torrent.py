import math
import hashlib
import time
from bcoding import bencode, bdecode
import logging
import os


class Torrent(object):
    def __init__(self):
        self.path = ''
        self.torrent = {}
        self.total_length: int = 0
        self.piece_length: int = 0
        self.pieces: int = 0
        self.info_hash: str = ''
        self.info_hash_str: str = ''
        self.peer_id: str = ''
        self.announce_list = ''
        self.file_names = []
        self.number_of_pieces: int = 0

    def load_from_bytes(self, torrent_bytes):

        contents = bdecode(torrent_bytes)

        self.torrent = contents
        self.piece_length = self.torrent['info']['piece length']
        self.pieces = self.torrent['info']['pieces']
        raw_info_hash = bencode(self.torrent['info'])
        self.info_hash = hashlib.sha1(raw_info_hash).digest()
        self.info_hash_str = str(self.info_hash.hex())
        self.peer_id = self.generate_peer_id()
        self.announce_list = self.get_trackers()
        self.init_files()
        self.number_of_pieces = math.ceil(self.total_length / self.piece_length)
        logging.debug(self.announce_list)
        logging.debug(self.file_names)

        assert (self.total_length > 0)
        assert (len(self.file_names) > 0)

        return self

    def load_from_path(self, path):
        logging.debug('start load_from_path')
        self.path = path
        with open(path, 'rb') as file:
            self.load_from_bytes(file)

        logging.debug('Success load torrent file')
        return self

    def init_files(self):
        root = self.torrent['info']['name']

        if 'files' in self.torrent['info']:
            if not os.path.exists(root):
                os.mkdir(root, 0o0766)

            for file in self.torrent['info']['files']:
                path_file = os.path.join(root, *file["path"])

                if not os.path.exists(os.path.dirname(path_file)):
                    os.makedirs(os.path.dirname(path_file))

                self.file_names.append({"path": path_file, "length": file["length"]})
                self.total_length += file["length"]

        else:
            self.file_names.append({"path": root, "length": self.torrent['info']['length']})
            self.total_length = self.torrent['info']['length']

    def get_trackers(self):
        if 'announce-list' in self.torrent:
            return self.torrent['announce-list']
        else:
            return [[self.torrent['announce']]]

    @staticmethod
    def generate_peer_id():
        seed = str(time.time())
        return hashlib.sha1(seed.encode('utf-8')).digest()

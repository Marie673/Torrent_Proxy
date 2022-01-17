import logging
from bcoding import bencode, bdecode
import cefpyco
import torrent
from cefapp import CefAppProducer
from threading import Thread
import hashlib
import math


class TorrentCef(torrent.Torrent):
    def __init__(self):
        super(TorrentCef, self).__init__()

    def load_from_bytes(self, payload: bytes):
        contents = bdecode(payload)

        self.torrent_file = contents
        self.piece_length = self.torrent_file['info']['piece length']
        self.pieces = self.torrent_file['info']['pieces']
        raw_info_hash = bencode(self.torrent_file['info'])
        self.info_hash = hashlib.sha1(raw_info_hash).digest()
        self.peer_id = self.generate_peer_id()
        self.announce_list = self.get_trackers()
        self.init_files()
        self.number_of_pieces = math.ceil(self.total_length / self.piece_length)
        logging.debug(self.announce_list)
        logging.debug(self.file_names)

        assert (self.total_length > 0)
        assert (len(self.file_names) > 0)

        return self


class Cef(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register("ccnx:/BitTorrent")
        self.torrent_dict: dict = {}

    def run(self):
        while True:
            info = self.handle.receive()
            self._process_new_message(info)

    def _process_new_message(self, info):
        name = info.name.split('/')
        if not name[0] == 'ccnx:' or not name[1]:
            logging.error('Not supported protocol: {}/{}'.format(name[0], name[0]))
            return

        if info.is_interest:
            logging.debug('Received interest')
            info_hash = name[2]
            message_id = name[3]

            # request message
            if message_id == 6:
                index = name[4]
                download_piece(info_hash, index)

            # torrentファイル取得のためのInterest送信
            if message_id == 'torrent':
                peer = name[4]
                interest = 'ccnx:/' + peer + '/BitTorrent/torrent_file' + info_hash
                self.handle.send_interest(interest)

        if info.is_data:
            if name[2] == 'BitTorrent' and name[3] == 'torrent_file':
                info_hash = name[4]
                torrent_info = TorrentCef().load_from_bytes(info.payload)

                self.torrent_dict[info_hash] = torrent_info

    def send_data(self, data: bytes):
        pass


def download_piece(info_hash, index):
    pass


def main():
    cef = Cef()
    cef.run()


if __name__ == '__main__':
    main()

import os.path
import time
from multiprocessing import Process
from threading import Thread
from src.application.bittorrent.bittorrent import BitTorrent
import bitstring
import cefpyco
import src.global_value as gv
from src.main import com_manager


from logger import logger


class InterestListener(Thread):
    def __init__(self):
        super().__init__()
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()

        self.bittorrent_dict = {}

    def run(self) -> None:
        self.cef_handle.register("ccnx:/BitTorrent")
        try:
            while True:
                try:
                    info = self.cef_handle.receive()
                    if info.is_succeeded and info.is_interest:
                        prefix = info.name.split('/')
                        """
                        prefix[0] = ccnx:
                        prefix[1] = BitTorrent
                        prefix[2] = info_hash
                        prefix[3] = piece_index
                        """
                        protocol = prefix[1]
                        info_hash = prefix[2]
                        piece_index = prefix[3]
                        req_data = (info_hash, piece_index)

                        if protocol == 'BitTorrent':
                            self.handle_bittorrent(req_data)

                except Exception as e:
                    print(e)

        except KeyboardInterrupt:
            logger.debug("Interest Listener is down")
            return

    def handle_bittorrent(self, req_data):
        (info_hash, piece_index) = req_data
        if info_hash in self.bittorrent_dict:
            b_process = self.bittorrent_dict[info_hash]
            if piece_index == 'bitfield':
                pass
            else:
                pass

        else:
            # torrentファイルを持っている前提
            torrent = # torrent file
            b_process = BitTorrent(torrent, com_manager)

    def send_data(self, info):
        pass

import os.path
import time
from threading import Thread
from src.application.bittorrent.bittorrent import BitTorrent
from src.domain.entity.torrent import Torrent
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
                        req_data = (info.name, info_hash, piece_index)

                        if protocol == 'BitTorrent':
                            self.handle_bittorrent(req_data)

                except Exception as e:
                    print(e)

        except KeyboardInterrupt:
            logger.debug("Interest Listener is down")
            return

    def handle_bittorrent(self, req_data):
        (name, info_hash, piece_index) = req_data
        if info_hash in self.bittorrent_dict:
            b_process: BitTorrent = self.bittorrent_dict[info_hash]
            if piece_index == 'bitfield':
                bitfield = b_process.bitfield
                self.send_data(name, bitfield)

            else:
                piece_index = int(piece_index)
                piece = b_process.pieces[piece_index]
                if piece.is_full:
                    piece_data = piece.get_piece()
                    self.send_data(name, piece_data)
                pass

        else:
            # torrentファイルを持っている前提
            torrent_file_name = gv.TORRENT_FILE_PATH + info_hash + ".torrent"
            torrent = Torrent(torrent_file_name)
            b_process = BitTorrent(torrent, com_manager)
            b_process.run()

            self.bittorrent_dict[info_hash] = b_process

    def send_data(self, name, data: bytes):
        size = len(data)
        end_chunk_num = size // gv.CHUNK_SIZE - 1
        for i in range(end_chunk_num + 1):
            start = i * gv.CHUNK_SIZE
            end = (i+1) * gv.CHUNK_SIZE
            if end > size:
                end = size
            payload = data[start:end]
            self.cef_handle.send_data(
                name=name,
                payload=payload,
                chunk_num=i,
                end_chunk_num=end_chunk_num,
                cache_time=60  # たしかs
            )


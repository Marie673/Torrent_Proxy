import os.path
from multiprocessing import Process
import cefpyco
import src.bt as bt

import yaml
import logging.config
from logging import getLogger
log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


CHUNK_SIZE = 1024 * 4


class InterestListener(Process):
    def __init__(self, req_list: list):
        super().__init__()
        self.req_list = req_list
        self.cef_handle = cefpyco.CefpycoHandle()
        self.cef_handle.begin()

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

                        if protocol == 'BitTorrent':

                            if piece_index == 'bitfield':
                                self.send_data(info)
                                if info_hash in self.req_list:
                                    pass
                                else:
                                    self.req_list.append(info_hash)
                            else:
                                self.send_data(info)

                except Exception as e:
                    print(e)

        except KeyboardInterrupt:
            logger.debug("Interest Listener is down")
            return

    def send_data(self, info):
        prefix = info.name.split('/')
        info_hash = prefix[2]
        piece_index = prefix[3]
        path = bt.CACHE_PATH + info_hash + "/" + piece_index
        chunk = info.chunk_num
        logger.debug(f"{path} {chunk}")

        if os.path.isfile(path):
            file_size = os.path.getsize(path)
            end_chunk_num = file_size // CHUNK_SIZE
            seeker = chunk * CHUNK_SIZE

            if piece_index == "bitfield":
                bt.m_lock.acquire()
                cache_time = 0
            else:
                cache_time = 10000
            with open(path, "rb") as file:
                file.seek(seeker)
                payload = file.read(CHUNK_SIZE)
                self.cef_handle.send_data(
                    name=info.name,
                    payload=payload,
                    chunk_num=chunk,
                    end_chunk_num=end_chunk_num,
                    cache_time=cache_time  # たしかs
                )
            if piece_index == "bitfield":
                bt.m_lock.release()
            return True
        else:
            return False

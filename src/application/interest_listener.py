import os.path
from multiprocessing import Process
import cefpyco
import src.bt as bt


CHUNK_SIZE = 1024 * 4


class InterestListener(Process):
    def __init__(self, req_list: list):
        super().__init__()
        self.req_list = req_list

    def run(self) -> None:
        with cefpyco.create_handle() as handle:
            handle.register("ccnx:/BitTorrent")
            while True:
                try:
                    info = handle.receive()
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
                                path = bt.CACHE_PATH + info_hash + "/" + piece_index
                                print(path, os.path.isfile(path))
                                bt.m_lock.acquire()
                                if os.path.isfile(path):
                                    print("test1")
                                    with open(path, "r") as file:
                                        print("test2")
                                        payload = file.read()
                                        handle.send_data(
                                            name=info.name,
                                            payload=payload,
                                            cache_time=0
                                              # たしかs
                                        )
                                bt.m_lock.release()

                                if info_hash in self.req_list:
                                    pass
                                else:
                                    self.req_list.append(info_hash)

                            else:
                                path = bt.CACHE_PATH + piece_index
                                if os.path.isfile(path):
                                    chunk = info.chunk_num

                                    file_size = os.path.getsize(path)
                                    end_chunk_num = file_size // CHUNK_SIZE - 1
                                    seeker = chunk * CHUNK_SIZE

                                    with open(path, "rb") as file:
                                        file.seek(seeker)
                                        payload = file.read(CHUNK_SIZE)
                                        handle.send_data(
                                            name=info.name,
                                            payload=payload,
                                            chunk_num=chunk,
                                            end_chunk_num=end_chunk_num,
                                            cache_time=10000  # たしかs
                                        )

                except Exception as e:
                    print(e)

from multiprocessing import Process, Queue
import cefpyco
import src.bt as bt
import src.application.bittorrent.bittorrent as bittorrent
from src.domain.entity.torrent import Torrent


class InterestListener(Process):
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    def start(self) -> None:
        with cefpyco.createHandle() as handle:
            handle.register("ccnx:/BitTorrent")
            while True :
                info = handle.receive()
                if info.is_success and info.name == "ccnx:/BitTorrent" and info.chunk_num == 0:
                    prefix = info.name.split('/')
                    """
                    prefix[0] = ccnx:
                    prefix[1] = BitTorrent
                    prefix[2] = info_hash
                    prefix[3] = piece_index
                    """
                    info_hash = prefix[2]
                    piece_index = prefix[3]
                    # TODO
                    # if ファイルが存在するかどうか:
                    #   pass
                    # else:
                    request: tuple[str, int] = (info_hash, piece_index)
                    self.queue.put(request)


                    handle.send_data("ccnx:/test", "hello", 0)
                    # break # Uncomment if publisher provides content once

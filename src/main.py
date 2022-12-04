import src.application.bittorrent.bittorrent as b
import src.application.bittorrent.communication_manager as c
from src.application.interest_listener import InterestListener
from src.domain.entity.torrent import Torrent
import src.bt as bt
from multiprocessing import Manager, Lock


m_lock = Lock()


def main():
    bt.threads = []
    req_list = Manager().list()

    com_mgr = c.CommunicationManager()
    interest_listener = InterestListener(req_list)

    com_mgr.start()
    interest_listener.start()

    paths = [
        '/evaluation/torrent/128MB.torrent',
        '/evaluation/torrent/256MB.torrent',
        '/evaluation/torrent/512MB.torrent',
        '/evaluation/torrent/1024MB.torrent',
        '/evaluation/torrent/2048MB.torrent'
    ]

    path_dict = {}
    for path in paths:
        torrent = Torrent(path)
        path_dict[torrent.info_hash_hex] = torrent

    while True:
        for req_info_hash in req_list:
            if req_info_hash in path_dict.keys():
                torrent = path_dict[req_info_hash]
                d_process = b.BitTorrent(torrent, com_mgr)
                d_process.start()
                bt.threads.append(d_process)


if __name__ == '__main__':
    main()

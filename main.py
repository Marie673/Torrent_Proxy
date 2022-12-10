#!/usr/bin/env python3
import time

import src.application.bittorrent.bittorrent as b
import src.application.bittorrent.communication_manager as c
from src.application.interest_listener import InterestListener
from src.domain.entity.torrent import Torrent
import src.bt as bt
from multiprocessing import Manager, Lock

import yaml
import logging.config
from logging import getLogger
log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


m_lock = Lock()


def main():
    bt.threads = []
    req_list = Manager().list()

    com_mgr = c.CommunicationManager()
    interest_listener = InterestListener(req_list)

    com_mgr.start()
    interest_listener.start()

    paths = [
        '/root/evaluation/torrent_file/128MB.torrent',
        '/root/evaluation/torrent_file/256MB.torrent',
        '/root/evaluation/torrent_file/512MB.torrent',
        '/root/evaluation/torrent_file/1024MB.torrent',
        '/root/evaluation/torrent_file/2048MB.torrent'
    ]

    path_dict = {}
    for path in paths:
        torrent = Torrent(path)
        path_dict[torrent.info_hash_hex] = torrent

    try:
        while True:
            for req_info_hash in req_list:
                def check(info_hash):
                    for thread in bt.threads:
                        if thread.info_hash_hex == info_hash:
                            return True
                    return False
                if check(req_info_hash):
                    continue

                if req_info_hash in path_dict.keys():
                    torrent = path_dict[req_info_hash]
                    d_process = b.BitTorrent(torrent, com_mgr)
                    d_process.start()
                    bt.threads.append(d_process)

            time.sleep(1)

    except KeyboardInterrupt:
        logger.debug("catch the KeyboadInterrupt")
        bt.thread_flag = False

        com_mgr.join()
        for t in bt.threads:
            t.join()


if __name__ == '__main__':
    main()

from multiprocessing import Process
import select
from typing import Dict

from lib.peer.peers_manager import PeersManager
from lib.piece.pieces_manager import PiecesManager
from lib.torrent import Torrent

import yaml
from logging import getLogger
import logging.config

log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


class BitTorrent(Process):
    def __init__(self):
        super().__init__()
        self.test = 0
        self.peers_manager: Dict[str, PeersManager] = {}
        self.pieces_manager: Dict[str, PiecesManager] = {}

    def run(self) -> None:
        logger.info('Process Peers Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info('Exit Process')
            return

    def loop(self):
        for peers in self.peers_manager.values():
            peers.read_message()

    def add_torrent(self, torrent: Torrent):
        peers_m = PeersManager(torrent)
        pieces_m = PiecesManager(torrent)
        info_hash = torrent.info_hash_str

        self.peers_manager[info_hash] = peers_m
        self.pieces_manager[info_hash] = pieces_m

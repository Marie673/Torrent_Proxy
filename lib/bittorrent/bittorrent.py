from multiprocessing import Process

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

    def run(self) -> None:
        logger.info('Process Peers Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info('Exit Process')
            return

    def loop(self):
        # TODO peerの数を確認してadd peerを行う

        read = [peer.socket for peers_list in self.peers_dict.values()
                for peer in peers_list]
        read_list, _, _ = select.select(read, [], [], 1)

        for sock in read_list:
            peer = self._get_peer_by_socket(sock)
            if not peer.healthy:
                self.remove_peer(peer)
                continue

            try:
                payload = self.read_from_socket(sock)
            except Exception as e:
                logger.error('Recv failed {}'.format(e.__str__()))
                self.remove_peer(peer)
                continue

            peer.read_buffer += payload

            for message in peer.get_messages():
                self._process_new_message(message, peer)

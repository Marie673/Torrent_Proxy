import errno
import select
from multiprocessing import Process
import socket

import yaml
import logging.config
from logging import getLogger

import message
import peer

log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


class PeersManager(Process):
    def __init__(self):
        super().__init__()
        self.logger = getLogger('develop')
        self.pieces_m = None
        self.cefore_m = None

        self.peers = []

    def run(self) -> None:
        logger.info('Process Peers Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info('Exit Process')
            return

    def loop(self):
        read = [peer.socket for peer in self.peers]
        read_list, _, _ = select.select(read, [], [], 1)

        for sock in read_list:
            peer = self._get_peer_by_socket(sock)
            if not peer.health:
                self.remove_peer(peer)
                continue

            try:
                payload = self._read_from_socket(sock)
            except Exception as e:
                logger.error('Recv failed {}'.format(e.__str__()))
                self.remove_peer(peer)
                continue

            peer.read_buffer += payload

            for message in peer.get_message():
                self._process_new_message(message, peer)

    def _get_peer_by_socket(self, sock):
        for peer in self.peers:
            if sock == peer.socket:
                return peer

        raise Exception('Peer not present in peer_list')

    def add_peers(self, peers) -> None:
        for peer in peers:
            if self._dohandshake(peer):
                self.peers.append(peer)
            else:
                logger.error('Error _do_handshake')

    def remove_peer(self, peer) -> None:
        if peer in self.peers:
            peer.socket.close()
            self.peers.remove(peer)

    @staticmethod
    def _read_from_socket(sock: socket.socket) -> bytes:
        data = b''

        while True:
            try:
                buff = sock.recv(4096)
                if len(buff) <= 0:
                    break

                data += buff

            except socket.error as e:
                err = e.args[0]
                if err != errno.EAGAIN or err != errno.EWOULDBLOCK:
                    logger.error('Wrong errno {}'.format(err))
                break

        return data

    @staticmethod
    def _do_handshake(self, peer, torrent):
        handshake = message.Handshake(torrent)
        peer.send_to_peer(handshake.to_bytes())
        logger.info('new peer added: {}({})'.format(peer.ip, peer.port))

    @staticmethod
    def _process_new_message(self, new_message: message.Message, peer: peer.Peer) -> None:
        if isinstance(new_message, message.Handshake) or isinstance(new_message, message.KeepAlive)
            logger.error('Handshake or KeepAlive should have already been handled')

        elif isinstance(new_message, message.Choke):


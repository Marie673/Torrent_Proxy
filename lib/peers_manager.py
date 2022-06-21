import errno
import random
import select
from multiprocessing import Process
import socket

import yaml
import logging.config
from logging import getLogger

from typing import List, Dict

from message import Message, KeepAlive, Handshake, Choke, UnChoke, Interested, \
    NotInterested, Have, BitField, Request, Piece, Cancel, Port
from peer import Peer

log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


class PeersManager(Process):
    peers_list = List[Peer]

    def __init__(self):
        super().__init__()
        self.logger = getLogger('develop')
        self.pieces_m = None
        self.cefore_m = None

        self.peers_dict: Dict[str, PeersManager.peers_list] = {}

    def run(self) -> None:
        logger.info('Process Peers Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info('Exit Process')
            return

    def loop(self):
        read = [peer.socket for peers_list in self.peers_dict.values()
                for peer in peers_list]
        read_list, _, _ = select.select(read, [], [], 1)

        for sock in read_list:
            peer = self._get_peer_by_socket(sock)
            if not peer.healthy:
                self.remove_peer(peer)
                continue

            try:
                payload = self._read_from_socket(sock)
            except Exception as e:
                logger.error('Recv failed {}'.format(e.__str__()))
                self.remove_peer(peer)
                continue

            peer.read_buffer += payload

            for message in peer.get_messages():
                self._process_new_message(message, peer)

    def get_random_peer_having_piece(self, info_hash, index):
        ready_peers = []

        peers_list = self.peers_dict[info_hash]
        for peer in peers_list:
            if peer.is_eligible() and peer.is_unchoked() and peer.am_interested() and peer.has_piece(index):
                ready_peers.append(peer)

        return random.choice(ready_peers) if ready_peers else None

    def _get_peer_by_socket(self, sock):
        for peers_list in self.peers_dict.values():
            for peer in peers_list:
                if sock == peer.socket:
                    return peer

        raise Exception('Peer not present in peer_list')

    def add_peers(self, peers, info_hash) -> None:
        for peer in peers:
            if self._do_handshake(peer, info_hash):
                self.peers_dict.setdefault(info_hash, []).append(peer)
            else:
                logger.error('Error _do_handshake')

    def remove_peer(self, peer) -> None:
        for key, peers_list in self.peers_dict.items():
            if peer in peers_list:
                self.peers_dict[key].remove(peer)

    def has_unchoked_peers(self, info_hash) -> bool:
        peers_list = self.peers_dict[info_hash]
        for peer in peers_list:
            if peer.is_unchoked():
                return True
        return False

    def unchoked_peers_count(self, info_hash):
        cpt = 0
        peers_list = self.peers_dict[info_hash]
        for peer in peers_list:
            if peer.is_unchoked():
                cpt += 1

        return cpt

    # Peerから呼び出したい?
    def peer_request_piece(self, request=None, peer=None):
        if not request or not peer:
            logger.error('empty request/peer message')

        piece_index, block_offset, block_length = request.piece_index, request.block_offset, request.block_length
        block = self.pieces_m.get_block(piece_index, block_offset, block_length)
        if block:
            piece = Piece(piece_index, block_offset, block_length, block).to_bytes()
            peer.send_to_peer(piece)
            logger.info('send piece index #{} to peer: {}'.format(piece_index, peer.ip))

    # peers_listが持っているピースを更新
    def peers_bitfield(self, info_hash, bitfield=None):
        pass

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
    def _do_handshake(peer, info_hash):
        handshake = Handshake(info_hash)
        peer.send_to_peer(handshake.to_bytes())
        logger.info('new peer added: {}({})'.format(peer.ip, peer.port))

    @staticmethod
    def _process_new_message(new_message: Message, peer: Peer) -> None:
        if isinstance(new_message, Handshake) or isinstance(new_message, KeepAlive):
            logger.error('Handshake or KeepAlive should have already been handled')

        elif isinstance(new_message, Choke):
            peer.handle_choke()

        elif isinstance(new_message, UnChoke):
            peer.handle_unchoke()

        elif isinstance(new_message, Interested):
            peer.handle_interested()

        elif isinstance(new_message, NotInterested):
            peer.handle_not_interested()

        elif isinstance(new_message, Have):
            peer.handle_have(new_message)

        elif isinstance(new_message, BitField):
            peer.handle_bitfield(new_message)

        elif isinstance(new_message, Request):
            peer.handle_request(new_message)

        elif isinstance(new_message, Piece):
            peer.handle_piece(new_message)

        elif isinstance(new_message, Cancel):
            peer.handle_cancel()

        elif isinstance(new_message, Port):
            peer.handle_port_request()

        else:
            logger.error("Unknown message")

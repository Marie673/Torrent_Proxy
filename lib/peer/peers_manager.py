import errno
import random
import socket
import select

from message import Message, KeepAlive, Handshake, Choke, UnChoke, Interested, \
    NotInterested, Have, BitField, Request, Piece, Cancel, Port
from peer import Peer
from tracker import Tracker
from lib.torrent import Torrent

import yaml
import logging.config
from logging import getLogger

log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')

MAX_PEERS_TRY_CONNECT = 200
MAX_PEERS_CONNECTED = 100


class PeersManager(object):
    def __init__(self, torrent: Torrent):
        self.torrent = torrent
        self.peers = {}

    def read_message(self):
        read = [peer.socket for peers_list in self.peers.values()
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

    def try_peer_connect(self):
        # tracker
        tracker = Tracker(self.torrent)
        addrs = tracker.get_peers_from_trackers()

        logger.info("Trying to connect to %d peer(s)" % len(addrs))

        for _, sock_addr in addrs.items():
            if len(self.peers) >= MAX_PEERS_CONNECTED:
                break

            new_peer = Peer(int(self.torrent.number_of_pieces), sock_addr.ip, sock_addr.port)
            if not new_peer.connect():
                continue

            print('Connected to %d/%d peers' % (len(self.peers), MAX_PEERS_CONNECTED))

            self.add_peers(sock_addr)

        # kademlia
        # ipfs

    def get_random_peer_having_piece(self, index):
        ready_peers = []

        for _, peer in self.peers.items():
            if peer.is_eligible() and peer.is_unchoked() and peer.am_interested() and peer.has_piece(index):
                ready_peers.append(peer)

        return random.choice(ready_peers) if ready_peers else None

    def _get_peer_by_socket(self, sock):
        for peer in self.peers:
            if sock == peer.socket:
                return peer

        raise Exception('Peer not present in peer_list')

    def exist_peer(self, peer):  # keyを返す
        if peer in self.peers:
            return True

        return False

    def add_peers(self, peer) -> None:
        if self.exist_peer(peer):
            logger.info('{} is already connected.'.format(peer.ip))
            return

        if self._do_handshake(peer):
            self.peers[peer.__hash__()] = peer
        else:
            logger.error('Error _do_handshake')

    def remove_peer(self, peer) -> None:
        if self.exist_peer(peer):
            del self.peers[peer.__hash__]

    def get_peers_socket(self):
        peers_sock = [peer.socket for peer in self.peers.values()]
        return peers_sock

    def has_unchoked_peers(self, info_hash) -> bool:
        for peer in self.peers.values():
            if peer.is_unchoked():
                return True
        return False

    def unchoked_peers_count(self):
        cpt = 0
        for peer in self.peers.values():
            if peer.is_unchoked():
                cpt += 1

        return cpt

    # Peerから呼び出したい?
    def peer_request_piece(self, request=None, peer=None):
        """
        if not request or not peer:
            logger.error('empty request/peer message')

        piece_index, block_offset, block_length = request.piece_index, request.block_offset, request.block_length
        block = self.pieces_m.get_block(piece_index, block_offset, block_length)
        if block:
            piece = Piece(piece_index, block_offset, block_length, block).to_bytes()
            peer.send_to_peer(piece)
            logger.info('send piece index #{} to peer: {}'.format(piece_index, peer.ip))
        """
    # peers_listが持っているピースを更新
    def peers_bitfield(self, info_hash, bitfield=None):
        pass

    @staticmethod
    def read_from_socket(sock: socket.socket) -> bytes:
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

    def _do_handshake(self, peer):
        info_hash = self.torrent.info_hash_str
        handshake = Handshake(info_hash)
        peer.send_to_peer(handshake.to_bytes())
        logger.info('new peer added: {}({})'.format(peer.ip, peer.port))

    def _process_new_message(self, new_message: Message, peer: Peer) -> None:
        # TODO Handshake KeepAliveも受け付けるようにする
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
            self.peer_request_piece(new_message, peer)

        elif isinstance(new_message, Piece):
            piece_index, block_offset, block = peer.handle_piece(new_message)
            # TODO Piece Managerへの登録

        elif isinstance(new_message, Cancel):
            peer.handle_cancel()

        elif isinstance(new_message, Port):
            peer.handle_port_request()

        else:
            logger.error("Unknown message")

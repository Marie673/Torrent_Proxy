import select
from threading import Thread
import socket
import errno

from src.domain.entity.peer import Peer
import src.domain.entity.message as message
import src.global_value as gv

import yaml
import logging.config
from logging import getLogger
log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


class CommunicationManager(Thread):
    def __init__(self):
        super().__init__()
        self.is_active = True
        self.peers: list[Peer] = []
    
    def run(self) -> None:
        try:
            while self.is_active and gv.thread_flag:
                read = [peer.socket for peer in self.peers]
                read_list, _, _ = select.select(read, [], [], 1)

                for sock in read_list:
                    peer = self.get_peer_by_socket(sock)
                    if not peer.healthy:
                        self.remove_peer(peer)

                    try:
                        payload = self._read_from_socket(sock)
                    except Exception as e:
                        self.remove_peer(peer)
                        logger.error(e)
                        continue

                    peer.read_buffer += payload

                    for msg in peer.get_messages():
                        self._process_new_message(msg, peer)
        except Exception as e:
            logger.error(e)
        finally:
            logger.debug("down")

    def get_peer_by_socket(self, sock) -> Peer:
        for peer in self.peers:
            if sock == peer.socket:
                return peer
        raise Exception("Peer not present in peer_list")

    def remove_peer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except Exception:
                pass
            self.peers.remove(peer)

    def remove_unhealthy_peer(self):
        for index, peer in enumerate(self.peers):
            if peer.healthy is False:
                peer.disconnect()
                del self.peers[index]

    def has_unchocked_peers(self, info_hash):
        for peer in self.peers:
            if peer.is_unchoked() and peer.info_hash is info_hash:
                return True
        return False

    @staticmethod
    def _read_from_socket(sock) -> bytes:
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
                    logging.debug("Wrong errno {}".format(err))
                break
            except Exception:
                logging.exception("Recv failed")
                break

        return data

    @staticmethod
    def _process_new_message(new_message: message.Message, peer: Peer):
        if isinstance(new_message, message.Handshake) or isinstance(new_message, message.KeepAlive):
            logging.error("Handshake or KeepALive should have already been handled")

        elif isinstance(new_message, message.Choke):
            peer.handle_choke()

        elif isinstance(new_message, message.UnChoke):
            peer.handle_unchoke()

        elif isinstance(new_message, message.Interested):
            peer.handle_interested()

        elif isinstance(new_message, message.NotInterested):
            peer.handle_not_interested()

        elif isinstance(new_message, message.Have):
            peer.handle_have(new_message)

        elif isinstance(new_message, message.BitField):
            peer.handle_bitfield(new_message)

        elif isinstance(new_message, message.Request):
            peer.handle_request(new_message)

        elif isinstance(new_message, message.Piece):
            data = peer.handle_piece(new_message)
            notice(peer.info_hash, data)

        elif isinstance(new_message, message.Cancel):
            peer.handle_cancel()

        elif isinstance(new_message, message.Port):
            peer.handle_port_request()

        else:
            logging.error("Unknown message")


def notice(info_hash, data):
    for thread in gv.threads:
        if info_hash in thread.info_hash:
            thread.receive_block_piece(data)

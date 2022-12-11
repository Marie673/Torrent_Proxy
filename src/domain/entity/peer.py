import time
import bitstring
import socket
import struct

from src.domain.entity.message import Handshake, KeepAlive, UnChoke, Interested, Piece,\
    WrongMessageException, MessageDispatcher

import yaml
import logging.config
from logging import getLogger
log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


class Peer(object):
    def __init__(self, info_hash, number_of_pieces, ip, port):
        self.info_hash = info_hash
        self.last_call = 0.0
        self.has_handshacked = False
        self.healthy = False
        self.read_buffer = b''
        self.ip = ip
        self.port = port
        self.bit_field = bitstring.BitArray(number_of_pieces)
        self.state = {
            'am_choking': True,
            'am_interested': False,
            'peer_choking': True,
            'peer_interested': False,
        }
        try:
            self.socket = self._connect()
        except Exception as e:
            print(e)
            raise e

    def __hash__(self):
        return '{}:{}'.format(self.ip, self.port)

    def _connect(self):
        try:
            sock = socket.create_connection((self.ip, self.port), timeout=2)
            sock.setblocking(False)
            logger.debug("Connected to peer ip: {} - port: {}".format(self.ip, self.port))
            self.healthy = True
            return sock

        except Exception as e:
            print("Failed to connect to peer (ip: %s - port: %s - %s)" % (self.ip, self.port, e.__str__()))
            raise e

    def disconnect(self):
        self.socket.close()

    def do_handshake(self):
        try:
            handshake = Handshake(self.info_hash)
            self.send_to_peer(handshake.to_bytes())
            return True
        except Exception as e:
            print(e)
            pass

        return False

    def send_to_peer(self, msg):
        try:
            self.socket.send(msg)
            self.last_call = time.time()
        except Exception as e:
            self.healthy = False
            logger.error("Failed to send to peer : %s" % e.__str__())

    def is_eligible(self):
        now = time.time()
        return (now - self.last_call) > 0  # 0.001

    def has_piece(self, index):
        return self.bit_field[index]

    def am_choking(self):
        return self.state['am_choking']

    def am_unchoking(self):
        return not self.am_choking()

    def is_choking(self):
        return self.state['peer_choking']

    def is_unchoked(self):
        return not self.is_choking()

    def is_interested(self):
        return self.state['peer_interested']

    def am_interested(self):
        return self.state['am_interested']

    def handle_choke(self):
        logger.debug('handle_choke - %s' % self.ip)
        self.state['peer_choking'] = True

    def handle_unchoke(self):
        logger.debug('handle_unchoke - %s' % self.ip)
        self.state['peer_choking'] = False

    def handle_interested(self):
        logger.debug('handle_interested - %s' % self.ip)
        self.state['peer_interested'] = True

        if self.am_choking():
            unchoke = UnChoke().to_bytes()
            self.send_to_peer(unchoke)

    def handle_not_interested(self):
        logger.debug('handle_not_interested - %s' % self.ip)
        self.state['peer_interested'] = False

    def handle_have(self, have):
        """
        :type have: message.Have
        """
        # logger.debug('handle_have - ip: %s - piece: %s' % (self.ip, have.piece_index))
        self.bit_field[have.piece_index] = True

        if self.is_choking() and not self.state['am_interested']:
            interested = Interested().to_bytes()
            self.send_to_peer(interested)
            self.state['am_interested'] = True

        # pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field)

    def handle_bitfield(self, bitfield):
        """
        :type bitfield: message.BitField
        """
        logger.debug('handle_bitfield - %s - %s' % (self.ip, bitfield.bitfield))
        self.bit_field = bitfield.bitfield

        if self.is_choking() and not self.state['am_interested']:
            interested = Interested().to_bytes()
            self.send_to_peer(interested)
            self.state['am_interested'] = True

        # pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field)

    # TODO 必要か考える
    def handle_request(self, request):
        """
        :type request: message.Request
        """
        logger.debug('handle_request - %s' % self.ip)
        if self.is_interested() and self.is_unchoked():
            pass
            # TODO 修正
            return request
            # pub.sendMessage('PiecesManager.PeerRequestsPiece', request=request, peer=self)

    @staticmethod
    def handle_piece(message: Piece):
        piece = (message.piece_index, message.block_offset, message.block)
        return piece

    # TODO
    def handle_cancel(self):
        logger.debug('handle_cancel - %s' % self.ip)

    # TODO
    def handle_port_request(self):
        logger.debug('handle_port_request - %s' % self.ip)

    def _handle_handshake(self):
        try:
            handshake_message = Handshake.from_bytes(self.read_buffer)
            self.has_handshacked = True
            self.read_buffer = self.read_buffer[handshake_message.total_length:]
            logger.debug('handle_handshake - %s' % self.ip)
            return True

        except Exception:
            logger.exception("First message should always be a handshake message")
            self.healthy = False

        return False

    def _handle_keep_alive(self):
        try:
            keep_alive = KeepAlive.from_bytes(self.read_buffer)
            logger.debug('handle_keep_alive - %s' % self.ip)
        except WrongMessageException:
            return False
        """
        except Exception:
            logger.exception("Error KeepALive, (need at least 4 bytes : {})".format(len(self.read_buffer)))
            return False
        """

        self.read_buffer = self.read_buffer[keep_alive.total_length:]
        return True

    def get_messages(self):
        while len(self.read_buffer) > 4 and self.healthy:
            if (not self.has_handshacked and self._handle_handshake()) or self._handle_keep_alive():
                continue

            payload_length, = struct.unpack(">I", self.read_buffer[:4])
            total_length = payload_length + 4

            if len(self.read_buffer) < total_length:
                break
            else:
                payload = self.read_buffer[:total_length]
                self.read_buffer = self.read_buffer[total_length:]

            try:
                received_message = MessageDispatcher(payload).dispatch()
                if received_message:
                    yield received_message
            except WrongMessageException as e:
                logger.exception(e.__str__())

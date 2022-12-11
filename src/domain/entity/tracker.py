import ipaddress
import requests
from bcoding import bdecode
import socket
from urllib.parse import urlparse
import errno

from src.domain.entity.message import UdpTrackerConnection, UdpTrackerAnnounce, UdpTrackerAnnounceOutput
from src.domain.entity.torrent import Torrent

import yaml
import logging.config
from logging import getLogger

log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


peer_id = '-AZ2200-6wfG2wk6wWLc'


class SockAddr:
    def __init__(self, ip, port, allowed=True):
        self.ip = ip
        self.port = port
        self.allowed = allowed

    def __hash__(self):
        return "%s:%d" % (self.ip, self.port)

    def __str__(self):
        return "%s:%d" % (self.ip, self.port)


class Tracker(object):
    def __init__(self, torrent):
        self.torrent: Torrent = torrent
        self.threads_list = []
        self.connected_peers = {}
        self.dict_sock_addr = {}

    def get_peers_from_trackers(self):
        """
        test code
        """
        s = SockAddr("10.0.1.203", 8999)
        self.dict_sock_addr[s.__hash__()] = s

        return self.dict_sock_addr
        """
        test
        """
        for i, tracker in enumerate(self.torrent.announce_list):

            tracker_url = tracker[0]

            if str.startswith(tracker_url, "http"):
                try:
                    self.http_scraper(tracker_url)
                except Exception as e:
                    logging.error("HTTP scraping failed: %s " % e.__str__())

            elif str.startswith(tracker_url, "udp"):
                try:
                    self.udp_scrapper(tracker_url)
                except Exception as e:
                    logging.error("UDP scraping failed: %s " % e.__str__())

            else:
                logging.error("unknown scheme for: %s " % tracker_url)

        return self.dict_sock_addr

    def http_scraper(self, tracker):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': peer_id,
            'uploaded': 0,
            'downloaded': 0,
            'port': 6881,
            'left': self.torrent.info.length,
            'event': 'started'
        }

        try:
            answer_tracker = requests.get(tracker, params=params, timeout=5)
            list_peers: dict = bdecode(answer_tracker.content)
            # offset = 0
            if type(list_peers['peers']) is not dict:
                '''
                    - Handles bytes form of list of peers
                    - IP address in bytes form:
                        - Size of each IP: 6 bytes
                        - The first 4 bytes are for IP address
                        - Next 2 bytes are for port number
                    - To unpack initial 4 bytes !i (big-endian, 4 bytes) is used.
                    - To unpack next 2 byets !H(big-endian, 2 bytes) is used.
                '''
                for i in range(len(list_peers['peers']) // 6):
                    ip = list_peers['peers'][i]['ip']
                    port = list_peers['peers'][i]['port']
                    s = SockAddr(ip, port)
                    self.dict_sock_addr[s.__hash__()] = s
                    """
                for _ in range(len(list_peers['peers']) // 6):
                    ip = struct.unpack_from("!i", list_peers['peers'], offset)[0]
                    ip = socket.inet_ntoa(struct.pack("!i", ip))
                    offset += 4
                    port = struct.unpack_from("!H", list_peers['peers'], offset)[0]
                    offset += 2
                    print(ip + " " + port)
                    s = SockAddr(ip, port)
                    self.dict_sock_addr[s.__hash__()] = s
                    """
            else:
                for p in list_peers['peers']:
                    s = SockAddr(p['ip'], p['port'])
                    self.dict_sock_addr[s.__hash__()] = s

        except Exception as e:
            logger.exception("HTTP scraping failed: %s" % e.__str__())

    def udp_scrapper(self, announce):
        torrent = self.torrent
        parsed = urlparse(announce)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(4)
        ip, port = socket.gethostbyname(str(parsed.hostname)), parsed.port

        if ipaddress.ip_address(ip).is_private:
            return

        tracker_connection_input = UdpTrackerConnection()
        response = self.send_message((ip, port), sock, tracker_connection_input)

        if not response:
            raise Exception("No response for UdpTrackerConnection")

        tracker_connection_output = UdpTrackerConnection()
        tracker_connection_output.from_bytes(response)

        tracker_announce_input = UdpTrackerAnnounce(torrent.info_hash, tracker_connection_output.conn_id,
                                                    torrent.peer_id)
        response = self.send_message((ip, port), sock, tracker_announce_input)

        if not response:
            raise Exception("No response for UdpTrackerAnnounce")

        tracker_announce_output = UdpTrackerAnnounceOutput()
        tracker_announce_output.from_bytes(response)

        for ip, port in tracker_announce_output.list_sock_addr:
            sock_addr = SockAddr(ip, port)

            if sock_addr.__hash__() not in self.dict_sock_addr:
                self.dict_sock_addr[sock_addr.__hash__()] = sock_addr

        print("Got %d peers" % len(self.dict_sock_addr))

    @staticmethod
    def send_message(conn, sock, tracker_message):
        message = tracker_message.to_bytes()
        trans_id = tracker_message.trans_id
        action = tracker_message.action
        size = len(message)

        sock.sendto(message, conn)

        try:
            response = Tracker.read_from_socket(sock)
        except socket.timeout as e:
            logger.debug("Timeout : %s" % e)
            return
        except Exception as e:
            logger.exception("Unexpected error when sending message : %s" % e.__str__())
            return

        if len(response) < size:
            logger.debug("Did not get full message.")

        if action != response[0:4] or trans_id != response[4:8]:
            logger.debug("Transaction or Action ID did not match")

        return response

    @staticmethod
    def read_from_socket(sock: socket) -> bytes:
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

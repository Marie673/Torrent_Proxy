import argparse
import hashlib
import socket
import sys
import threading
import urllib.parse
import cefpyco

import bencodepy
import requests

buffer_size = 1024
peer_id = '-qB4250-dYUl8lqi!FJ8'

bc = bencodepy.Bencode(
    encoding='utf-8',
    encoding_fallback='all',
)


def makeRequestURL(info_hash=None, port=None, uploaded=None, downloaded=None,
                   left=None, compact=None, event=None):
    url = '?'

    if info_hash is not None:
        url = url + 'info_hash=' + info_hash
    if peer_id is not None:
        url = url + '&peer_id=' + peer_id
    if port is not None:
        url = url + '&port=' + str(port)
    if uploaded is not None:
        url = url + '&uploaded=' + str(uploaded)
    if downloaded is not None:
        url = url + '&downloaded=' + str(downloaded)
    if left is not None:
        url = url + '&left=' + str(left)
    if compact is not None:
        url = url + '&compact=' + str(compact)
    if event is not None:
        url = url + '&event=' + event

    return url


def handShake(peer, info_hash) -> socket:
    data = b'\x13' + b'BitTorrent protocol' + b'\00\00\00\00\00\00\00\00' + \
           info_hash + peer_id.encode('utf-8')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = (peer[0], peer[1])

    sock.connect(addr)
    sock.sendall(data)

    return sock


class P2P:

    def __init__(self, ip, port):
        self.addr = (ip, port)
        self.sock = None

        self.choke_state: bool = False  # True  -> choke
        self.choked_state: bool = False  # False -> unchoke

        self.interested_state: bool = False

    def listener(self):
        while True:
            message = self.sock.recv(32 * 1024)
            if message != 0:
                m_length = int.from_bytes(message[0:3], 'big')
                if m_length == 0:
                    # keep alive
                    continue

                t_id = int.from_bytes(message[3:4], 'big')

                # choke
                if t_id == 0:
                    self.choked_state = True
                    return

                # unchoke
                if t_id == 1:
                    self.choked_state = False

                # interested
                if t_id == 2:
                    pass

                # not interested
                if t_id == 3:
                    pass

                # have
                if t_id == 4:
                    pass

                # bitfield
                if t_id == 5:
                    pass

                # request
                if t_id == 6:
                    pass

                # piece
                if t_id == 7:
                    print(message)
                    pass

                # cancel
                if t_id == 8:
                    pass

                # port
                if t_id == 9:
                    pass

    def requestPiece(self, index: int, begin: int, length: int):
        data = int(13).to_bytes(4, 'big') + \
               int(6).to_bytes(1, 'big') + \
               index.to_bytes(4, 'big') + \
               begin.to_bytes(4, 'big') + \
               length.to_bytes(4, 'big')

        self.sock.sendall(data)

    def handle(self):
        pass

class BitTorrent:

    def __init__(self, torrent_file):
        # torrent file information
        self.torrent_file = torrent_file
        self.torrent_dict: dict = bc.decode(self.torrent_file)
        self.info_dict: dict = self.torrent_dict['info']
        self.length = self.info_dict['length']
        self.piece_length = self.info_dict['piece length']
        self.piece_num: int = self.length // self.piece_length
        self.pieces_dict: dict = self.info_dict['pieces']
        # hash of piece
        self.pieces = [self.pieces_dict[i:i + 20] for i in range(0, len(self.pieces_dict), 20)]

        # analyze info
        self.info_hash = hashlib.sha1(bencodepy.encode(self.info_dict)).digest()
        self.tracker_addr = self.torrent_dict['announce'].replace("https", "http")
        self.peer_list = []

        # piece info
        self.downloaded_piece = []

    def getPeerList(self):
        url = makeRequestURL(
            info_hash=urllib.parse.quote(self.info_hash),
            port=6881,
            uploaded=0,
            downloaded=0,
            left=10000,
            compact=1,
            event="started"
        )
        url = self.tracker_addr + url

        response = requests.get(url)
        resDict = bc.decode(response.content)

        peersBytes = bytes(resDict['peers'])
        peersBytesDict = [peersBytes[i:i + 6] for i in range(0, len(peersBytes), 6)]
        for i in range(0, len(peersBytesDict)):
            b = peersBytesDict[i]
            ip = \
                str(int.from_bytes(b[0:1], 'big')) + "." + \
                str(int.from_bytes(b[1:2], 'big')) + "." + \
                str(int.from_bytes(b[2:3], 'big')) + "." + \
                str(int.from_bytes(b[3:4], 'big'))
            port = int.from_bytes(b[4:6], 'big')
            addr = [ip, port]
            self.peer_list.append(addr)

        return self.peer_list, len(self.peer_list)

    def handshake(self, sock: socket):
        data = b'\x13' + b'BitTorrent protocol' + b'\00\00\00\00\00\00\00\00' + \
               self.info_hash + peer_id.encode('utf-8')
        sock.sendall(data)

    def listener(self):
        pass


    def thread(self, addr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        self.handshake(sock)
        #

    def download(self):
        self.getPeerList()
        peer_num = len(self.peer_list)
        p2p = []
        for i in range(peer_num):
            p2p[i] = P2P(self.peer_list[i][0], self.peer_list[i][1])
            # threadに処理を投げる


# ICNのピース紹介の方法
# ICNノードの紹介方法
# 一般ピアの恩恵
# ピースの優先順位
def main():
    if len(sys.argv) != 2:
        print("Usage: {} <server port>".format(sys.argv[0]))
        exit(1)

    torrentFileName = sys.argv[1]
    torrentFile = open(torrentFileName, "rb")


if __name__ == '__main__':
    main()

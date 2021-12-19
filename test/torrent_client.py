#!/usr/bin/env python3.9
import sys
import urllib.parse
import bencodepy
import hashlib
import requests
import socket


def requestURL(info_hash=None, peer_id=None, port=None, uploaded=None, downloaded=None,
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


if __name__ == '__main__':
'''
    torrentFile = open(sys.argv[1], "rb")
    bc = bencodepy.Bencode(
        encoding='utf-8',
        encoding_fallback='all',
    )
    torrentDict = bc.decode(torrentFile.read())
    infoDict = dict(torrentDict['info'])
    # print(infoDict)
    piecesDict = infoDict['pieces']

    pieces = [piecesDict[i:i + 20] for i in range(0, len(piecesDict), 20)]
'''
    info_hash = hashlib.sha1(bencodepy.encode(infoDict)).digest()
    print('\033[32m' + 'Hash of Torrent: ' + '\033[0m' + info_hash.hex())

    url = requestURL(
        info_hash=urllib.parse.quote(info_hash),
        peer_id="-qB4250-dYUl8lqi!FJ8",
        port=6881,
        uploaded=0,
        downloaded=0,
        left=10000,
        compact=1,
        event="started"
    )
    url = torrentDict['announce'].replace("https", "http") + url
    print('\033[32m' + 'url: ' + '\033[0m' + url)

    print('\nwaiting to receive peer info ...\n')

   # response = requests.get(url)
   # resDict = bc.decode(response.content)

    peersBytes = bytes(resDict['peers'])
    peersBytesDict = [peersBytes[i:i + 6] for i in range(0, len(peersBytes), 6)]
    peers = []
    for i in range(0, len(peersBytesDict)):
        b = peersBytesDict[i]
        ip = \
            str(int.from_bytes(b[0:1], 'big')) + "." + \
            str(int.from_bytes(b[1:2], 'big')) + "." + \
            str(int.from_bytes(b[2:3], 'big')) + "." + \
            str(int.from_bytes(b[3:4], 'big'))
        port = int.from_bytes(b[4:6], 'big')
        addr = [ip, port]
        peers.append(addr)
    print('peer list: ')
    print(peers)
    print('\n')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = (peers[0][0], peers[0][1])
    print('connecting to ' + str(addr) + '\n')
    sock.connect(addr)

    data = b'\x13' + b'BitTorrent protocol' + b'\00\00\00\00\00\00\00\00' + \
           info_hash + b'-qB4250-dYUl8lqi!FJ8'

    print('send data (binary) ...')
    print('\033[42m' + data.hex() + '\033[0m' + '\n')

    sock.sendall(data)
    m = sock.recv(1024)
    print('receive data ...')
    print(m)

    messageLength = 13
    messageID = 6
    index = 9101
    begin = 0
    length = 16 * 1024

    while True:
        message = sock.recv(32 * 1024)
        if message != 0:
            m_length = int.from_bytes(message[0:3], 'big')
            t_id = int.from_bytes(message[3:4], 'big')
            if t_id == 0:
                pass
            if t_id == 1:
                data = messageLength.to_bytes(4, 'big')
                data += messageID.to_bytes(1, 'big')
                data += index.to_bytes(4, 'big')
                data += begin.to_bytes(4, 'big')
                data += length.to_bytes(4, 'big')

                sock.sendall(data)
                pass
            if t_id == 2:
                pass
            if t_id == 3:
                pass
            if t_id == 4:
                pass
            if t_id == 5:
                data = messageLength.to_bytes(4, 'big')
                data += messageID.to_bytes(1, 'big')
                data += index.to_bytes(4, 'big')
                data += begin.to_bytes(4, 'big')
                data += length.to_bytes(4, 'big')

                sock.sendall(data)
                pass
            if t_id == 6:
                pass
            if t_id == 7:
                print(message)
                pass
            if t_id == 8:
                pass
            if t_id == 9:
                pass

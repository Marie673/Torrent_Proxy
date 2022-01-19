import sys

import cefpyco
from threading import Thread
import socket


class Cef(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        self.handle.register('ccnx:/BitTorrent')

    def run(self):
        while True:
            info = self.handle.receive()
            if info.is_succeeded:
                print('get info')


class P2P(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.socket: socket.socket = None
        self.ip = '127.0.0.1'
        self.port = 10000

    def connect(self):
        try:
            self.socket = socket.create_connection((self.ip, self.port))
            self.socket.setblocking(False)
        except Exception as e:
            print('failed to connect to peer %s' % e)

    def run(self):
        self.connect()
        while True:
            payload = self.socket.recv(4096)
            print(payload)

def main():
    cef = Cef()
    p2p = P2P()

    try:
        cef.start()
        p2p.start()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()

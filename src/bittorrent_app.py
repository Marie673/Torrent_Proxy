import socket
import sys

buffer_size = 1024
peer_id = b'-qB4250-dYUl8lqi!FJ8'


class Seed:
    def __init__(self):
        self.server_ip = ''
        self.server_port = 0
        self.listen_num = 5
        self.torrent_hash = []

    def handshakeListener(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.server_ip, self.server_port))

        server.listen(self.listen_num)

        while True:
            client, addr = server.accept()
            print("[*] Connected. [ Source : {}]".format(addr))

            data = client.recv(buffer_size)
            print("[*] Received Data.")

            num_b = data[:2]
            data = data[2:]
            num = int.from_bytes(num_b, 'big')

            protocol = data[:num].decode('utf-8')
            data = data[num:]

            if protocol == 'BitTorrent protocol':
                data = data[16:]
                info_hash = data[:20]
                data = data[20:]

                c_peer_id = data

    def listener(self):
        pass


class Peer:
    def __init__(self):
        self.ip = ''
        self.port = 0

    def handshake(self):
        pass


def main():
    if len(sys.argv) != 2:
        print("Usage: {} <server port>".format(sys.argv[0]))
        exit(1)


if __name__ == '__main__':
    main()

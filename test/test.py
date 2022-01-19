import socket

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind(("127.0.0.1", 10000))
socket.listen(10)

client_sock, client_addr = socket.accept()

while True:
    data = input()

    client_sock.sendall(data.encode())
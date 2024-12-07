import socket


PORT = 5000
SERVER = "localhost"
ADDR = (SERVER, PORT)


def tcp_send(bin: bytes):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(bin)
    res = client.recv(1024).decode("utf-8")
    print(res)
    client.close()

import socket
from typing import Literal


PORT = 5000
SERVER = "hairo.local"
ADDR = (SERVER, PORT)


def tcp_send(bin: bytes) -> Literal["ok", "disconnected", "timeout"]:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.settimeout(0.2)
        client.connect(ADDR)
        client.settimeout(None)
    except Exception as e:
        print(e)
        client.close()
        return "disconnected"

    try:
        client.settimeout(0.2)
        client.send(bin)
        res = client.recv(1024).decode("utf-8")
        client.settimeout(None)
        client.close()

        if res != "ok":
            return "timeout"
        else:
            return "ok"
    except Exception as e:
        print(e)
        client.close()
        return "timeout"

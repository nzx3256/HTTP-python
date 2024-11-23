<<<<<<< HEAD
import os
import socket

IP = "localhost"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server"

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break
        data = input("> ")
        data = data.split(" ")
        cmd = data[0]
        
        if cmd == "TASK":
            client.send(cmd.encode(FORMAT))
        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break
    print("Disconnected from the server.")
    client.close()

if __name__ == "__main__":
    main()
=======
import os
import socket
import sys
import protocol

host_type = os.path.splitext(os.path.basename(__file__))[0].lower()
PORT = 8080

def usage(n: int = 0) -> None:
    if n == 0:
        print("USAGE: python client.py <server IP>")
    elif n == 1:
        print("server IP must be a valid IPv4")
        print("IPv4 must be formatted like so:\n\
    xxx.xxx.xxx.xxx\n\
(where x is are numbers from 0-9)")
    else:
        print("Undefined usage error")

def validateIP(ip: str) -> None:
    if nums := ip.split('.'):
        #IP check
        validIP: bool = True
        if len(nums) > 4:
            validIP = False
            usage(1)
        for n in nums:
            if not n.isnumeric():
                validIP = False
                break
            elif int(n) > 255 or int(n) < 0:
                validIP = False
                break
        if not validIP:
            usage(1)
            sys.exit(-1)

def main() -> None:
    if len(sys.argv) < 2:
        usage(0)
        sys.exit(-1)
    IP = sys.argv[1]
    validateIP(IP)
    # socket setup
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost",PORT))
        ret, _ = protocol.introduction(sock)
        if ret == 1:
            login_ret = protocol.login_user(sock, "")
            if not login_ret:
                protocol.exit_close(sock, 0)
        elif ret == 0:
            protocol.new_profile(sock, "")
        elif ret == -1:
            protocol.exit_close(sock, -1)

        # login routine
        while True:
            cmd_parse = input("> ").split(' ')
            cmd = cmd_parse[0]
            if cmd.lower() == 'logout':
                sock.send(b"LOGOUT@client request")
                break

if __name__ == "__main__":
    main()
>>>>>>> abe4ccd18c07f7d996756614fdb375adaa118488

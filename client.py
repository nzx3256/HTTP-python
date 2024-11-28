import os
import socket
import sys
import protocol

host_type = os.path.splitext(os.path.basename(__file__))[0].lower()
PORT = 8080

def recv_print(sock) -> None:
    msg = sock.recv(protocol.MSG_SIZE).decode()
    if msg.split('@')[0] == "OK":
        print(msg.split('@')[1])
    elif msg.split('@')[0] == "UERR":
        print(f"User Error: {msg.split('@')[1]}")
    elif msg.split('@')[0] == "SERR":
        print(f"Server Error: {msg.split('@')[1]}")
    else:
        print("Unexpected messsage")

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

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        usage(0)
        return -1
    IP = argv[1]
    validateIP(IP)
    # socket setup
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost",PORT))
        ret, _ = protocol.introduction(sock)
        if ret == 1:
            login_ret = protocol.login_user(sock, "")
            if not login_ret:
                print("Authentication Failed")
                print("Exiting Client")
                protocol.exit_close(sock, 0)
        elif ret == 0:
            protocol.new_profile(sock, "")
        elif ret == -1:
            protocol.exit_close(sock, -1)

        # login routine
        while True:
            cin = input("> ")
            cmd_parse = cin.split(' ')
            cmd = cmd_parse[0]
            l = len(cmd_parse)
            if cmd.lower() == 'logout':
                sock.send(b"LOGOUT@client request")
                break
            elif cmd.lower() == 'ls':
                if l == 1:
                    path = ''
                elif l == 2:
                    path = cmd_parse[-1]
                    if path[-1] == "\n":
                        path = path[:-1]
                else: # remove this else block when arguments are added to the commands (1)
                    print("Too many arguments for ls")
                    print("Usage: ls <dirname>")
                    continue
                if protocol.validPath(path, True):
                    sock.send(("LS@"+path).encode())
                else:
                    continue
                recv_print(sock)
            elif cmd.lower() == 'del':
                if l == 1:
                    print("Usage: mkdir <dirname>")
                    continue
                elif l == 2:
                    path = cmd_parse[-1]
                    if path[-1] == "\n":
                        path = path[:-1]
                else: # same as mark[1]
                    print("Too many arguments for mkdir")
                    print("Usage: mkdir <path>")
                    continue
                if protocol.validPath(path, True):
                    sock.send(("DEL@"+path).encode())
                else:
                    continue
                recv_print(sock)
            elif cmd.lower() == 'mkdir':
                if l == 1:
                    print("Usage: mkdir <dirname>")
                    continue
                elif l == 2:
                    dirname = cmd_parse[-1]
                    if dirname[-1] == "\n":
                        dirname = dirname[:-1]
                else: # same as mark[1]
                    print("Too many arguments for mkdir")
                    print("Usage: mkdir <dirname>")
                    continue
                if protocol.validPath(dirname, True):
                    sock.send(("MKDIR@"+dirname).encode())
                else:
                    continue
                recv_print(sock)
            elif cmd.lower() == 'rmdir':
                if l == 1:
                    print("Usage: rmdir <dirname>")
                    continue
                elif l == 2:
                    dirname = cmd_parse[-1]
                    if dirname[-1] == "\n":
                        dirname = dirname[:-1]
                else: # same as mark[1]
                    print("Too many arguments for mkdir")
                    print("Usage: rmdir <dirname>")
                    continue
                if protocol.validPath(dirname, True):
                    sock.send(("RMDIR@"+dirname).encode())
                else:
                    continue
                recv_print(sock)
            elif cmd.lower() == 'download':
                if l == 1:
                    print("Usage: download <path/to/file>")
                    continue
                elif l == 2:
                    path = cmd_parse[-1]
                    if path[-1] == "\n":
                        path = path[:-1]
                else:
                    print("Too many arguements for download")
                    print("Usage: download <path/to/file>")
                    continue
                if protocol.validPath(path, True):
                    sock.send(b"DOWN@"+path.encode())
                else:
                    continue
                protocol.file_transfer(sock, download=True, filename=path)
            elif cmd.lower() == 'upload':
                if l == 1:
                    print("Usage: upload <path/to/file>")
                    continue
                elif l == 2:
                    path = cmd_parse[-1]
                    if path[-1] == "\n":
                        path = path[:-1]
                else:
                    print("Too many arguements for download")
                    print("Usage: upload <path/to/file>")
                    continue
                if os.path.exists(path):
                    sock.send(b"UP@"+path.encode())
                else:
                    print("File does not exist: "+path)
                    continue
                protocol.file_transfer(sock, download=False, filename=path)
            elif cmd.lower() == 'ldir':
                sargs = cin[len(cmd)+1:]
                os.system("dir "+sargs)
            elif cmd.lower() == 'cd':
                sargs = cin[len(cmd)+1:]
                os.system("cd "+sargs)
            else:
                continue

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

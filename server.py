import os
import protocol
import subprocess as sproc
import socket
import threading

IP = "localhost"
PORT = 8080
host_type: str = os.path.splitext(os.path.basename(__file__))[0].lower()

# thread callback to set up client connection
def handle_client(conn, addr):
    ret, hash = protocol.introduction(conn, host_type == 'client')
    if ret == 1:
        # login_user protocol
        login_ret = protocol.login_user(conn, hash, host_type == 'client')
        if not login_ret:
            protocol.exit_close(conn, 0, False)
    elif ret == 0:
        # new_profile protocol
        protocol.new_profile(conn, hash, host_type == 'client')
    elif ret == -1:
        # disconnect client and close the thread
        protocol.exit_close(conn, -1, host_type == 'client')

    os.chdir("CWD")
    # If the thread gets to this line that means that the server has passed the login subroutine.
    # start handling commands from the client
    while True:
        msg = conn.recv(protocol.MSG_SIZE).decode()
        if msg.split('@')[0] == 'LOGOUT':
            break
        elif msg.split('@')[0] == 'LS':
            relpath = msg.split('@')[-1]
            if protocol.validPath(relpath):
                #continue processing command
                cmdin = "dir "+relpath
                try:
                    conn.send(b"OK@"+sproc.check_output(cmdin, shell=True))
                except:
                    conn.send(b"SERR@unexpected command error")
            else:
                conn.send(b"UERR@invalid relative path")
        elif msg.split('@')[0] == 'MKDIR':
            dirname = msg.split('@')[-1]
            if protocol.validPath(dirname):
                cmdin = "mkdir "+dirname
                if sproc.call(cmdin, shell=True, stdout=sproc.DEVNULL, stderr=sproc.DEVNULL) == 0:
                    conn.send(("OK@"+dirname+" created").encode())
                else:
                    conn.send(b"SERR@unexpected command error")
            else:
                conn.send(b"UERR@invalid relative path")
        elif msg.split('@')[0] == 'RMDIR':
            dirname = msg.split('@')[-1]
            if protocol.validPath(dirname):
                cmdin = "rmdir "+dirname
                if sproc.call(cmdin, shell=True, stdout=sproc.DEVNULL, stderr=sproc.DEVNULL) == 0:
                    conn.send(("OK@"+dirname+" deleted").encode())
                else:
                    conn.send(b"SERR@unexpected command error")
            else:
                conn.send(b"UERR@invalid relative path")
        elif msg.split('@')[0] == 'DEL':
            filename = msg.split('@')[-1]
            if protocol.validPath(filename):
                cmdin = "del "+filename
                if sproc.call(cmdin, shell=True, stdout=sproc.DEVNULL, stderr=sproc.DEVNULL) == 0:
                    conn.send(("OK@"+filename+" deleted").encode())
                else:
                    conn.send(b"SERR@unexpected command error")
            else:
                conn.send(b"UERR@invalid relative path")
        elif msg.split('@')[0] == 'DOWN':
            path = msg.split('@')[-1]
            if protocol.validPath(path) and os.path.exists(path):
                protocol.file_transfer(conn, download=False, filename=path)
        elif msg.split('@')[0] == 'UP':
            file = os.path.basename(msg.split('@')[-1])
            protocol.file_transfer(conn, download=True, filename=file)
    conn.close()

def main():
    print("Starting the server")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen(2)
    print(f"server listening on {IP}:{PORT}")
    while True:
        conn, addr = server.accept()
        print(f"Connection established with {addr[0]}:{addr[1]}")
        callback = threading.Thread(target=handle_client, args=(conn,addr))
        callback.start()

if __name__ == "__main__":
    main()

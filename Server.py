import os
import protocol
import socket
import time
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

    # If the thread gets to this line that means that the server has passed the login subroutine.
    # start handling commands from the client
    while True:
        msg = conn.recv(protocol.MSG_SIZE).decode()
        if msg.split('@')[0] == 'LOGOUT':
            break

    conn.close()

def main():
    print("Starting the server")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen(2)
    print(f"server listening on {IP}:{PORT}")
    while True:
        conn, addr = server.accept()
        callback = threading.Thread(target=handle_client, args=(conn,addr))
        callback.start()

if __name__ == "__main__":
    main()

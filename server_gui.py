import sys
import tkinter as tk
from tkinter import scrolledtext
import protocol
import subprocess as sproc
import socket
import threading
import os

IP = socket.gethostbyname(socket.gethostname())
PORT = 8080
host_type: str = os.path.splitext(os.path.basename(__file__))[0].lower()
initial_dir = os.getcwd()


class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Server")
        self.server = None
        self.server_running = False

        # UI Elements
        self.start_button = tk.Button(root, text="Start Server", command=self.start_server)
        self.start_button.pack()

        self.stop_button = tk.Button(root, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack()

        self.client_list_label = tk.Label(root, text="Connected Clients:")
        self.client_list_label.pack()

        self.client_listbox = tk.Listbox(root)
        self.client_listbox.pack(fill=tk.BOTH, expand=True)

        self.log_label = tk.Label(root, text="Server Log:")
        self.log_label.pack()

        self.log_text = scrolledtext.ScrolledText(root, state='disabled', height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.yview(tk.END)
        self.log_text.config(state='disabled')

    def start_server(self):
        self.server_running = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((IP, PORT))
        self.server.listen(2)

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log(f"Server started at {IP}:{PORT}")

        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while self.server_running:
            try:
                conn, addr = self.server.accept()
                self.client_listbox.insert(tk.END, f"{addr[0]}:{addr[1]}")
                self.log(f"Client connected: {addr[0]}:{addr[1]}")
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except OSError:
                break

    def stop_server(self):
        self.server_running = False
        self.server.close()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("Server stopped.")
        sys.exit()


def handle_client(conn, addr):
    # LOGIN PROTOCOLS
    os.chdir(initial_dir)
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
        # LS Command
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
        # MKDIR Command
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



if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()

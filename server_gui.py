import tkinter as tk
from tkinter import scrolledtext
import threading
import socket
from Server import handle_client, IP, PORT

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

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()

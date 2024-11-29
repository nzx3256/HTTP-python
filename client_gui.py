import tkinter as tk
from tkinter import messagebox, filedialog
import socket
import protocol
from tkinter import simpledialog
import threading

# Constants
MSG_SIZE = 1024
PORT = 8080

class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Client GUI")
        self.root.geometry("600x400")

        # Socket
        self.sock = None

        # Frames
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(pady=10)

        self.middle_frame = tk.Frame(self.root)
        self.middle_frame.pack(pady=10)

        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(pady=10)

        self.output_frame = tk.Frame(self.root)
        self.output_frame.pack(pady=10)

        # Login/Connection Widgets
        self.server_ip_label = tk.Label(self.top_frame, text="Server IP:")
        self.server_ip_label.grid(row=0, column=0, padx=5)
        self.server_ip_entry = tk.Entry(self.top_frame)
        self.server_ip_entry.grid(row=0, column=1, padx=5)

        self.connect_btn = tk.Button(self.top_frame, text="Connect", command=self.connect_to_server)
        self.connect_btn.grid(row=0, column=2, padx=5)

        self.login_btn = tk.Button(self.top_frame, text="Login", command=self.login_user, state=tk.DISABLED)
        self.login_btn.grid(row=0, column=3, padx=5)

        self.register_btn = tk.Button(self.top_frame, text="Register", command=self.register_user, state=tk.DISABLED)
        self.register_btn.grid(row=0, column=4, padx=5)

        # Command Buttons
        self.ls_btn = tk.Button(self.middle_frame, text="List Directory", command=self.ls_command, state=tk.DISABLED)
        self.ls_btn.grid(row=0, column=0, padx=5)

        self.mkdir_btn = tk.Button(self.middle_frame, text="Make Directory", command=self.mkdir_command, state=tk.DISABLED)
        self.mkdir_btn.grid(row=0, column=1, padx=5)

        self.rmdir_btn = tk.Button(self.middle_frame, text="Remove Directory", command=self.rmdir_command, state=tk.DISABLED)
        self.rmdir_btn.grid(row=0, column=2, padx=5)

        self.del_btn = tk.Button(self.middle_frame, text="Delete File", command=self.del_command, state=tk.DISABLED)
        self.del_btn.grid(row=0, column=3, padx=5)

        self.download_btn = tk.Button(self.middle_frame, text="Download File", command=self.download_command, state=tk.DISABLED)
        self.download_btn.grid(row=1, column=0, padx=5)

        self.upload_btn = tk.Button(self.middle_frame, text="Upload File", command=self.upload_command, state=tk.DISABLED)
        self.upload_btn.grid(row=1, column=1, padx=5)

        self.logout_btn = tk.Button(self.middle_frame, text="Logout", command=self.logout, state=tk.DISABLED)
        self.logout_btn.grid(row=1, column=2, padx=5)

        # Output Area
        self.output_label = tk.Label(self.output_frame, text="Output:")
        self.output_label.pack(anchor="w")

        self.output_text = tk.Text(self.output_frame, width=70, height=10)
        self.output_text.pack()

    def connect_to_server(self):
        server_ip = self.server_ip_entry.get()
        if not server_ip:
            messagebox.showerror("Error", "Server IP cannot be empty")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((server_ip, PORT))
            self.output_text.insert("end", f"Connected to server at {server_ip}:{PORT}\n")
            self.login_btn.config(state=tk.NORMAL)
            self.register_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def login_user(self):
        if not self.sock:
            messagebox.showerror("Error", "Not connected to any server")
            return

        ret, _ = protocol.introduction(self.sock)
        if ret == 1:
            login_ret = protocol.login_user(self.sock, "")
            if login_ret:
                self.output_text.insert("end", "Login Successful\n")
                self.enable_commands()
            else:
                self.output_text.insert("end", "Login Failed\n")
        elif ret == 0:
            self.output_text.insert("end", "User not found on server. Register a new profile.\n")
        elif ret == -1:
            self.output_text.insert("end", "Server rejected connection.\n")

    def register_user(self):
        if not self.sock:
            messagebox.showerror("Error", "Not connected to any server")
            return

        protocol.new_profile(self.sock, "")
        self.output_text.insert("end", "New user registered successfully.\n")

    def ls_command(self):
        self.send_command("LS@")

    def mkdir_command(self):
        # Ask for the name of the directory to create
        dirname = simpledialog.askstring("Make Directory", "Enter the name of the directory to create:")
        if not dirname:
            self.output_text.insert("end", "Operation canceled: No directory name provided.\n")
            return

        # Ask where to create the directory
        parent_dir = simpledialog.askstring("Make Directory", "Enter the path where the directory should be created:")
        if not parent_dir:
            self.output_text.insert("end", "Operation canceled: No parent directory provided.\n")
            return

        command = f"MKDIR@{parent_dir}\\{dirname}"
        self.send_command(command)

    def rmdir_command(self):
        # Ask for the name of the directory to remove
        dirname = simpledialog.askstring("Remove Directory", "Enter the name of the directory to remove:")
        if not dirname:
            self.output_text.insert("end", "Operation canceled: No directory name provided.\n")
            return

        command = f"RMDIR@{dirname}"
        self.send_command(command)

    def del_command(self):
        # Ask for the name of the file to delete
        filename = simpledialog.askstring("Delete File", "Enter the name of the file to delete:")
        if not filename:
            self.output_text.insert("end", "Operation canceled: No file name provided.\n")
            return

        command = f"DEL@{filename}"
        self.send_command(command)

    def download_command(self):
        # Ask for the name of the file to download
        filename = simpledialog.askstring("Download File", "Enter the name of the file to download:")
        if not filename:
            self.output_text.insert("end", "Operation canceled: No file name provided.\n")
            return


        command = f"DOWN@{filename}"
        self.send_command(command)

    def upload_command(self):
        # Ask for the file to upload
        filepath = simpledialog.askstring("Upload File", "Enter the full path of the file to upload:")
        if not filepath:
            self.output_text.insert("end", "Operation canceled: No file path provided.\n")
            return

        # Ask where to upload the file
        #destination = simpledialog.askstring("Upload File", "Enter the destination path on the server:")
        #if not destination:
        #    self.output_text.insert("end", "Operation canceled: No destination path provided.\n")
        #    return

        protocol.file_transfer(self.sock, download=False, filename=filepath)
        self.output_text.insert("end", f"File {filepath} uploaded successfully.\n")

    def logout(self):
        self.send_command("LOGOUT@client request")
        self.sock.close()
        self.sock = None
        self.disable_commands()
        self.output_text.insert("end", "Logged out successfully.\n")

    def send_command(self, cmd):
        if self.sock:
            self.sock.send(cmd.encode())
            msg = self.sock.recv(MSG_SIZE).decode()
            self.output_text.insert("end", f"Server Response: {msg}\n")
        else:
            messagebox.showerror("Error", "Not connected to any server")

    def enable_commands(self):
        for widget in self.middle_frame.winfo_children():
            widget.config(state=tk.NORMAL)

    def disable_commands(self):
        for widget in self.middle_frame.winfo_children():
            widget.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()

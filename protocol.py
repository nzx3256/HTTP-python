import socket
import os
import json
from threading import Lock
from login import getpwhash, pchash, newpwhash

MSG_SIZE = 1024
pchash_file = "pchash.json"
mutex = Lock()

def file_transfer(conn, download: bool, filename = None) -> None:
    if download:
        if filename == None or type(filename) != str:
            return
        data = b""
        msg = conn.recv(MSG_SIZE)
        if msg[:4] == b"FILE":
            while msg[-5:] != b"<END>":
                data += msg
                msg = conn.recv(MSG_SIZE)
            data += msg[:-5]
            head_sp = data.decode().split('#')
            filename = "default.txt"
            payload = b"Nothing to write"
            for s in head_sp[1:]:
                if s.split('@')[0] == "NAME":
                    filename = os.path.basename(s.split('@')[1])
                elif s.split('@')[0] == "SIZE":
                    pass
                elif s.split('@')[0] == "PAYLOAD":
                    payload = s.split('@')[1]
            with open(filename, 'wb') as fd:
                fd.write(payload)
            conn.send(b"DONE")
    else:
        #upload
        if filename == None or type(filename) != str:
            return
        try:
            with open(filename, "r") as fd:
                conn.send(b"FILE#")
                conn.send(b"NAME@"+filename.encode()+b"#")
                conn.send(b"SIZE@"+str(os.path.getsize(filename)).encode()+b"#")
                conn.send(b"PAYLOAD"+fd.read().encode()+b"#")
                conn.send(b"<END>")
            conn.recv(4)
        #except FileNotFoundError:
            #conn.send(b"SERR@FileNotFoundError")
        except:
            #conn.send(b"SERR@unexpected error")
            pass

def validPath(path: str, err_out: bool = False) -> bool:
    # enforce \ as the directory delimeter
    if '/' in path:
        print("Paths cannot contain / as a directory delimeter. Use \\ instead")
        return False
    sp = path.split("\\")
    c = 0
    for a in sp:
        if a == "..":
            c-=1
        elif a == "." or a == '':
            continue
        else:
            c+=1
        if c < 0:
            if err_out:
                print("Cannot navigate to parent directory \"..\"")
            return False
    return True

def exit_close(conn, status_code, client: bool = True) -> None:
    if client:
        msg = conn.recv(MSG_SIZE).decode()
        conn.send(b"EXIT@client")
        conn.close()
        print(f"Exiting with status code: {status_code}")
        exit(status_code)
    else:
        conn.send(b"EXIT@server")
        conn.recv(MSG_SIZE).decode()
        conn.close()
        print(f"Exiting with status code: {status_code}")
        exit(status_code)

def introduction(conn, client: bool = True) -> tuple[int, str]:
    if client:
        # client must send a hash of its IP address to the host
        msg = conn.recv(MSG_SIZE).decode()
        if msg == "INTRO@send pchash":
            conn.send(("INTRO@"+str(pchash())).encode())
            msg = conn.recv(MSG_SIZE).decode()
            if msg.split('@')[1] == "found":
                return (1, "")
            elif msg.split('@')[1] == "notfound":
                return (0, "")
            else:
                print(f"\"{msg}\" was not an acceptable input")
        else:
            conn.send(b"FAIL@unexpected msg")
            print(f"expected \"INTRO@send pchash\" msg from server. instead got {msg}")
        return (-1, "")
    else:
        conn.send(b"INTRO@send pchash")
        msg = conn.recv(MSG_SIZE).decode()
        sp = msg.split('@')
        if sp[0] == "INTRO":
            # file IO is not thread safe so we are using locks
            mutex.acquire()
            # here we are getting a dictionary of all the saved pchashes in the pchash_file declared above
            try:
                with open(pchash_file, "r") as hashfd:
                    d = json.load(hashfd)
            # if the pchash_file does not exist or is not in json format we open the file for writing and save it
            # as an empty dictionary
            except FileNotFoundError or json.JSONDecodeError:
                with open(pchash_file, "w") as hashfd:
                    print("Server-side: creating pchash.json")
                    d = {}
                    hashfd.write(json.dumps(d,indent=4))
            # if the hash is in the dictionary we got in the above step return true; else return false
            mutex.release() # release the lock here
            if sp[1] in d:
                conn.send(b"INTRO@found")
                return (1, sp[1])
            else:
                conn.send(b"INTRO@notfound")
                return (0, sp[1])
        else:
            print(f"unexpected msg type: {sp[0]}. Expected INTRO msg")
            conn.send(b"FAIL@msg not recognized")
            return (-1, "")

def new_profile(conn, pchash: str = "", client: bool = True) -> None:
    if client:
        msg = conn.recv(MSG_SIZE).decode()
        pwhash = newpwhash()
        if msg == "NEW@Enter a password":
            conn.send(("NEW@"+str(pwhash)).encode())
        else:
            print(msg)
    else:
        if pchash == "":
            print("pchash must be a non empty string contrain a string")
            conn.send("FAIL@unset server function")
            return
        conn.send(b"NEW@Enter a password")
        msg = conn.recv(MSG_SIZE).decode()
        cmd = msg.split('@')[0]
        args = msg.split('@')[1].split(' ')
        if cmd == "NEW":
            mutex.acquire()
            with open("pchash.json", "r") as hashfd:
                d = json.load(hashfd)
            with open("pchash.json", "w") as hashfd:
                d[pchash] = args[0]
                hashfd.write(json.dumps(d,indent=4))
            mutex.release()
        elif cmd == "FAIL":
            print(f"Client returned \"{msg}\" :\tExpected \"NEW\" msg")

# steps:
# 1. server sends the client a message to initiate the login_user protocol
# 2. client program will get pwhash from the user
# 3. client sends pwhash to the server
# 4. server opens pchash.json to confirm login credentials. using the hash retrieved from intro
# 5. if login is correct server will continue the connection. otherwise close the connection
def login_user(conn, pchash: str, client: bool = True) -> bool:
    if client:
        msg = conn.recv(MSG_SIZE).decode()
        if msg == "LOGIN@enter your password":
            pwhash = getpwhash()
            conn.send(("LOGIN@"+str(pwhash)).encode())
        elif msg == "FAIL@server error":
            print(msg)
        else:
            conn.send(b"FAIL@unexpected msg in login_user")
        msg = conn.recv(MSG_SIZE).decode()
        if msg == "LOGIN@successful":
            return True
        elif msg == "LOGIN@unsuccessful":
            return False
        else:
            print(msg)
            return False
    else:
        if pchash == "":
            conn.send(b"FAIL@server error")
            return False
        conn.send(b"LOGIN@enter your password")
        msg = conn.recv(MSG_SIZE).decode()
        if msg.split('@')[0] == "LOGIN":
            mutex.acquire()
            with open("pchash.json", "r") as hashfd:
                d = json.load(hashfd)
            mutex.release()
            if d[pchash] == msg.split('@')[1]:
                conn.send(b"LOGIN@successful")
                return True
            else:
                conn.send(b"LOGIN@unsuccessful")
                return False
        else:
            print(f"Client returned \"{msg}\" :\tExpected \"LOGIN\" msg")
            return False

def main():
    print("no runner setup")
if __name__ == "__main__":
    main()
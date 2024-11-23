from getpass import getpass
from hashlib import sha256
from socket import gethostname, gethostbyname

def pchash() -> str:
    hasher = sha256()
    hasher.update(gethostbyname(gethostname()).encode())
    hash = hasher.hexdigest()
    return hash

def getpwhash() -> str:
    pw = getpass("Enter your password: ") 
    hasher = sha256()
    hasher.update(pw.encode())
    hash = hasher.hexdigest()
    return hash

def newpwhash() -> str:
    pw1 = ""
    while True:
        pw1 = getpass("Enter a password: ")
        pw2 = getpass("Enter password again: ")
        if pw1 == pw2:
            break
        else:
            print("Passwords don't match. Enter them agin")
            print("")
    hasher = sha256()
    hasher.update(pw1.encode())
    hash = hasher.hexdigest()
    return hash

if __name__ == "__main__":
    b = getpwhash()
    print(b)

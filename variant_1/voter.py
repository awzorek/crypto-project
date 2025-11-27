import socket
from voter_list import VoterList
from tools import hash, encrypt, decrypt, sign, verify
from tools import blind, blind_sign, unblind, verify_blind_signature
from tools import construct_message, deconstruct_message

HOST = "127.0.0.1"
REGISTRATION_SERVER_PORT = 2137
BALLOT_BOX_SERVER_PORT = 2138
BUFFER_SIZE = 4096

def authenticate():
    # just a filler
    id = int(input('Enter your id (1-4):'))
    if id < 1 or id > 4:
        print('ID out of range...')
        exit(1)
    v = VoterList()
    v.read()
    private = v.get_private_key(id)
    public = v.get_public_keys()

    return id, private, public

def get_empty_ballot():
    pass

def connect_to_server(server_port) -> socket:
    print(f"Trying to connect to registration server at {HOST}:{server_port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, server_port))
    except ConnectionRefusedError:
        print(f"Could not connect to registration server at {HOST}:{server_port}")
        return

    print(f"Connected to registration server at {HOST}:{server_port}")
    return s

def send_welcome(s : socket, id : int, serv_pub_key, my_key):
    if id == -1:
        print('Incorrect ID')
        exit(3)

    data = talk(s, construct_message(id, 'WEL', 'welcome', my_key, serv_pub_key))
    serv_id, code, text, useless = deconstruct_message(data, serv_pub_key, my_key)

    print(f"Serwer {serv_id}: {code}, {text}")
        
def talk(s : socket, message):
    s.sendall(message)
    data = s.recv(BUFFER_SIZE)
    if not data:
        print('Server closed the connection.')
        exit(4)
    return data.decode()

def main():
    id, private, public = authenticate()

    serv_pub_key = public['0']['public_key']
    my_priv_key = private['private_key']
    
    s = connect_to_server(REGISTRATION_SERVER_PORT)
    send_welcome(s, id, serv_pub_key, my_priv_key)
    while True: pass

if __name__ == "__main__": main()
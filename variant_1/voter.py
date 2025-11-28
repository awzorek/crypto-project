import json
import socket

from voter_list import VoterList
from tools import hash, encrypt, decrypt, sign, verify
from tools import generate_aes_key, aes_encrypt, aes_decrypt
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

def get_empty_ballot(s : socket, id : int, serv_pub_key, my_key):
    # GEB - Get Empty Ballot
    _, _, text = talk(s, id, 'GEB', '', my_key, serv_pub_key)
    return json.loads(text)

def fill_the_ballot(BS0 : dict):
    print('=== Ballot sheet === ')
    print('Title:', BS0['title'])

    for key in BS0.keys():
        if key == 'title': continue
        print(f"Candidate {key}: {BS0[str(key)]}")
    
    num = input('Enter a number of your candidate: ')

    if num in BS0:
        S = input(f"Confirm your choice of {BS0[str(num)]} by typing YES: ")
        if S.lower() == 'yes':
            print(f"Sending vote for {BS0[str(num)]}")
            return num
        else:
            print('Confirmation failed. Try voting again.')
            return fill_the_ballot(BS0)
    else:
        print('Wrong key. Try voting again.')
        return fill_the_ballot(BS0)
    
def send_filled_ballot(s : socket, id : int, BS : str, serv_key, my_key):
    m = generate_aes_key()
    m_BS = aes_encrypt(BS.encode(), m)
    h = hash(m_BS)
    blinded_m_BS, r = blind(h, serv_key)
    blinded_m_BS = str(blinded_m_BS)

    print('Vote sent')
    _, _, ans = talk(s, id, 'FB', blinded_m_BS, my_key, serv_key)

    return ans, m, r

def connect_to_server(server_port) -> socket:
    print(f"Trying to connect to registration server at {HOST}:{server_port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, server_port))
    except ConnectionRefusedError:
        print(f"Could not connect to registration server at {HOST}:{server_port}")
        return

    if server_port == REGISTRATION_SERVER_PORT:
        print(f"Connected to registration server at {HOST}:{server_port}")
    elif server_port == BALLOT_BOX_SERVER_PORT:
        print(f"Connected to ballot box server at {HOST}:{server_port}")
    return s

def disconnect(s : socket, server_port):
    if server_port == REGISTRATION_SERVER_PORT:
        print("Disconnected the registration server")
    elif server_port == BALLOT_BOX_SERVER_PORT:
        print("Disconnected the ballot box server")
    else:
        print('Disconnected the server')
    s.close()

def send_welcome(s : socket, id : int, serv_pub_key, my_key):
    if id == -1:
        print('Incorrect ID')
        exit(3)

    serv_id, code, text = talk(s, id, 'WEL', 'welcome', my_key, serv_pub_key)

    print(f"Serwer {serv_id}: {code}, {text}")
        
def talk(s : socket, id, code, text, my_key, serv_pub_key):
    message = construct_message(id, code, text, my_key, serv_pub_key)
    s.sendall(message)
    data = s.recv(BUFFER_SIZE)
    if not data:
        print('Server closed the connection.')
        exit(4)
    serv_id, code, text, _ = deconstruct_message(data, serv_pub_key, my_key)
    return serv_id, code, text

def main():
    id, private, public = authenticate()

    serv_pub_key = public['0']['public_key']
    my_priv_key = private['private_key']
    
    s = connect_to_server(REGISTRATION_SERVER_PORT)
    BS0 = get_empty_ballot(s, id, serv_pub_key, my_priv_key)
    BS = fill_the_ballot(BS0)
    ans, m, r = send_filled_ballot(s, id, BS, serv_pub_key, my_priv_key)

    signed_blinded_m_BS = int(ans)
    signed_m_BS = unblind(signed_blinded_m_BS, r, serv_pub_key)
    disconnect(s, REGISTRATION_SERVER_PORT)

    while True: pass

if __name__ == "__main__": main()
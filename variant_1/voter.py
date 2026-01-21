import json
import socket

from voter_list import VoterList
from tools import generate_aes_key, aes_encrypt, blind, unblind, hash
from tools import construct_message, deconstruct_message

HOST = "127.0.0.1"
REGISTRATION_SERVER_PORT = 2137
BALLOT_BOX_SERVER_PORT = 2138
BUFFER_SIZE = 4096

def authenticate():
    # just a filler
    v = VoterList()
    size = v.length()

    id = int(input(f"Enter your id (3-{size-1}):"))
    if id < 3 or id > size-1:
        print('ID out of range...')
        exit(1)
    
    private = v.get_private_key(id)
    public = v.get_public_keys()

    return id, private, public

def request_empty_ballot(s : socket, id : int, serv_pub_key, my_key):
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
    h = hash(m_BS).digest()
    blinded_m_BS, r = blind(h, serv_key)
    blinded_m_BS = str(blinded_m_BS)

    print('Vote sent')
    _, _, ans = talk(s, id, 'FB', blinded_m_BS, my_key, serv_key)

    return ans, m, r, m_BS

def send_encrypted_ballot(s : socket, id : int, signed_m_BS, m_BS, serv_key, my_key):
    string = json.dumps({
        'signed_m_BS' : signed_m_BS,
        'm_BS' : m_BS
    })
    _, code, text = talk(s, id, 'EB', string, my_key, serv_key)
    i = int(text)
    if code == 'ACK':
        print('Ballot box server reiceved the encrypted ballot.')
    return i

def check_if_ballot_published(s : socket, id : int, i : int, m_BS : str, serv_key, my_key):
    string = json.dumps({
        'i' : i,
        'm_BS' : m_BS
    })
    _, _, text = talk(s, id, 'CIP', string, my_key, serv_key)
    if text == 'TRUE':
        print('Encrypted ballot sheet published.')
        return True
    elif text == 'FALSE':
        print('Encrypted ballot sheet not published.')
    else: print('Unknown symbol returned.')
    return False

def add_symmetrical_key(s : socket, id : int, i : int, m : bytes, serv_key, my_key):
    try:
        string = json.dumps({
            'i' : i,
            'm' : m.hex(),
        })
        _, code, _ = talk(s, id, 'ASK', string, my_key, serv_key)
        if code == 'ACK':
            print('Symmetrical key added to the list.')
            print('Your vote was counted.')
    except Exception as e:
        print('Error:', e)

def connect_to_server(server_port) -> socket:
    print(f"Trying to connect to server at {HOST}:{server_port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, server_port))
    except ConnectionRefusedError:
        print(f"Could not connect to server at {HOST}:{server_port}")
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

    reg_serv_pub_key = public['0']['public_key']
    bb_serv_pub_key = public['1']['public_key']
    my_priv_key = private['private_key']
    
    s = connect_to_server(REGISTRATION_SERVER_PORT)
    BS0 = request_empty_ballot(s, id, reg_serv_pub_key, my_priv_key)
    BS = fill_the_ballot(BS0)
    ans, m, r, m_BS = send_filled_ballot(s, id, BS, reg_serv_pub_key, my_priv_key)

    signed_blinded_m_BS = int(ans)
    signed_m_BS = unblind(signed_blinded_m_BS, r, reg_serv_pub_key)
    disconnect(s, REGISTRATION_SERVER_PORT)

    s = connect_to_server(BALLOT_BOX_SERVER_PORT)

    i = send_encrypted_ballot(s, id, signed_m_BS, m_BS, bb_serv_pub_key, my_priv_key)
    if check_if_ballot_published(s, id, i, m_BS, bb_serv_pub_key, my_priv_key):
        add_symmetrical_key(s, id, i, m, bb_serv_pub_key, my_priv_key)

if __name__ == "__main__": main()
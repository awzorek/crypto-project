import json, socket, sys

from voter_list import VoterList
from tools import _b64_encode, blind, unblind, hash, get_random_token, construct_message, deconstruct_message

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
        sys.exit(1)
    
    private = v.get_private_key(id)
    public = v.get_public_keys()

    return id, private, public

def sign_t_token(id : int, conn : socket, blinded_t : str, serv_pub_key, my_key):
    _, _, sig_blinded_t = talk(conn, id, 'REG', blinded_t, my_key, serv_pub_key)
    return sig_blinded_t

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

def send_filled_ballot(s : socket, id : int, BS : str, hash_t, signed_t_token, bb_serv_pub_key, my_priv_key):
    package = {
        'BS' : BS,
        'hash_t' : _b64_encode(hash_t),
        'signed_t' : signed_t_token
    }
    talk_str = json.dumps(package)
    _, code, _ = talk(s, id, 'FB', talk_str, my_priv_key, bb_serv_pub_key)
    
    if code == 'ACK':
        print('Ballot received by ballot box server.')
    else:
        print('Unexpected response from ballot box server.')

def check_if_published(s : socket, id : int, BS : str, hash_t, bb_serv_pub_key, my_priv_key):
    package = {
        'BS' : BS,
        'hash_t' : _b64_encode(hash_t),
    }
    talk_str = json.dumps(package)
    _, _, text = talk(s, id, 'CIP', talk_str, my_priv_key, bb_serv_pub_key)

    if text == 'TRUE':
        print('Your ballot has been published.')
    else:
        print('Your ballot has NOT been published.')

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

def talk(s : socket, id, code, text : str, my_key, serv_pub_key):
    message = construct_message(id, code, text, my_key, serv_pub_key)
    s.sendall(message)
    data = s.recv(BUFFER_SIZE)
    if not data:
        print('Server closed the connection.')
        sys.exit(4)
    serv_id, code, text, _ = deconstruct_message(data, serv_pub_key, my_key)
    return serv_id, code, text

def main():
    id, private, public = authenticate()

    reg_serv_pub_key = public['0']['public_key']
    bb_serv_pub_key = public['1']['public_key']
    my_priv_key = private['private_key']

    s = connect_to_server(REGISTRATION_SERVER_PORT)

    t = _b64_encode(get_random_token())
    hash_t = hash(t).digest()
    blinded_t, r = blind(hash_t, reg_serv_pub_key)
    sign_blinded_t_token = sign_t_token(id, s, str(blinded_t), reg_serv_pub_key, my_priv_key)
    signed_t_token = unblind(int(sign_blinded_t_token), r, reg_serv_pub_key)

    print(f"Received signed t_token: {signed_t_token}")

    disconnect(s, REGISTRATION_SERVER_PORT)

    s = connect_to_server(BALLOT_BOX_SERVER_PORT)

    BS0 = request_empty_ballot(s, id, bb_serv_pub_key, my_priv_key)
    BS = fill_the_ballot(BS0)

    send_filled_ballot(s, id, BS, hash_t, signed_t_token, bb_serv_pub_key, my_priv_key)
    check_if_published(s, id, BS, hash_t, bb_serv_pub_key, my_priv_key)
    disconnect(s, BALLOT_BOX_SERVER_PORT)

if __name__ == "__main__": main()
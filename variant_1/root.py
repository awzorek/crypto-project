import json
import socket

from tools import construct_message
from voter_list import VoterList

HOST = "127.0.0.1"
BALLOT_BOX_SERVER_PORT = 2138
BUFFER_SIZE = 4096
ROOT_ID = 2
BB_SERVER_ID = '1'

def regenerate_keys(num : int):
    v = VoterList()
    v.generate(num)
    v.save()

def generate_ballot(title : str, candidates : list):
    b = {}
    b['title'] = title
    for i in range(len(candidates)):
        b[str(i)] = candidates[i]
    s = json.dumps(b)

    with open('ballot', 'w') as f:
        f.write(s)

def talk(s : socket, id, code, text, my_key, serv_pub_key):
    message = construct_message(id, code, text, my_key, serv_pub_key)
    s.sendall(message)
    data = s.recv(BUFFER_SIZE)
    if not data:
        print('Server closed the connection.')
        exit(4)

def connect_to_server(server_port) -> socket:
    print(f"Trying to connect to ballot box server at {HOST}:{server_port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, server_port))
    except ConnectionRefusedError:
        print(f"Could not connect to ballot box server at {HOST}:{server_port}")
        return

    if server_port == BALLOT_BOX_SERVER_PORT:
        print(f"Connected to ballot box server at {HOST}:{server_port}")
    return s

def end_voting():
    v = VoterList()
    my_key = v.get_private_key(ROOT_ID)['private_key']
    ballot_box_key = v.get_public_keys()[BB_SERVER_ID]['public_key']

    s = connect_to_server(BALLOT_BOX_SERVER_PORT)
    talk(s, 2, "EOV", "EOV", my_key, ballot_box_key)

def main():
    print('===ROOT CONSOLE===')
    print('1. Load ballot')
    print('2. Generate new keys')
    print('3. End voting')

    while True:
        action = int(input('>'))
        if action == 1: generate_ballot('Wybory na prezydenta Polski', ['Lech Adamus', 'Jacek R***a'])
        elif action == 2: regenerate_keys(10)
        elif action == 3: end_voting()
        else: print('Wrong input. Try again.')

if __name__ == '__main__': main()
import json, socket, sys

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
        sys.exit(4)

def end_voting():
    v = VoterList()
    my_key = v.get_private_key(ROOT_ID)['private_key']
    ballot_box_key = v.get_public_keys()[BB_SERVER_ID]['public_key']

    print(f"Trying to connect to ballot box server at {HOST}:{BALLOT_BOX_SERVER_PORT}...")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, BALLOT_BOX_SERVER_PORT))
    except ConnectionRefusedError:
        print(f"Could not connect to ballot box server at {HOST}:{BALLOT_BOX_SERVER_PORT}")
        return

    print(f"Connected to ballot box server at {HOST}:{BALLOT_BOX_SERVER_PORT}")
    
    talk(s, 2, "EOV", "EOV", my_key, ballot_box_key)
    s.close()
    print("\n[!] Voting ended. Results summarized.")

def main():
    print('===ROOT CONSOLE===')
    print('1. Load ballot')
    print('2. Generate new keys')
    print('3. End voting')

    try:
        while True:
            action = int(input('>'))
            if action == 1: generate_ballot('Wybory na prezydenta Polski', ['Jan Kowalski', 'Marcin Nowak'])
            elif action == 2: regenerate_keys(10)
            elif action == 3:
                end_voting()
                sys.exit(0)
            else: print('Wrong input. Try again.')
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit(0)

if __name__ == '__main__': main()
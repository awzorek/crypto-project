import itertools
import json
import socket
import threading

from voter_list import VoterList
from ballot_list import BallotList
from tools import verify_blind_signature, hash
from tools import construct_message, deconstruct_message

HOST = "127.0.0.1"
PORT = 2138
BACKLOG = 10
BUFFER_SIZE = 4096

REG_SERVER_ID = 0
BB_SERVER_ID = 1

client_id_counter = itertools.count(1)

b = BallotList()

lock = threading.Lock()

def get_ballot():
    with open('ballot') as f:
        return json.loads(f.read())

def check_and_publish_ballot(string : str, conn : socket, client_key, my_key, reg_serv_pub_key):
    package = json.loads(string)
    signed_m_BS = package['signed_m_BS']
    m_BS = package['m_BS']
    if not verify_blind_signature(signed_m_BS, hash(m_BS), reg_serv_pub_key):
        print("Couldn't verify the blind signature")
        return
    with lock:
        i = b.append_m_BS(m_BS)
    conn.sendall(construct_message(BB_SERVER_ID, 'ACK', str(i), my_key, client_key))

def check_if_published(string : str, conn : socket, client_key, my_key):
    package = json.loads(string)
    i = int(package['i'])
    m_BS = package['m_BS']

    with lock:
        text = 'TRUE' if b.check_if_published(i, m_BS) else 'FALSE'
    conn.sendall(construct_message(BB_SERVER_ID, 'CIP_ANS', text, my_key, client_key))

def add_symetrical_key(string : str, conn : socket, client_key, my_key):
    package = json.loads(string)
    i = int(package['i'])
    m = bytes.fromhex(package['m'])

    b.add_key(i, m)

    conn.sendall(construct_message(BB_SERVER_ID, 'ACK', '', my_key, client_key))

def summarise(client_key):
    v = VoterList()
    if client_key != v.get_public_keys()['2']['public_key']:
        print('EOV not executed. Command not given by root.')
        return
    
    results = {}
    faulty = 0

    ballot = get_ballot()

    for i in ballot.keys():
        if i == 'title': continue
        results[i] = {
            'name' : ballot[i],
            'score' : 0,
        }
    
    for B in b.get_list().values():
        BS = B['BS']
        if BS in results.keys():
            results[BS]['score'] += 1
        else:
            faulty += 1
    
    lst = list(results.values())
    
    lst = sorted(lst, key=lambda x : x['score'], reverse=True)
    print("Results:")
    
    for r in lst:
        print(f"{r['name']}: {r['score']}")

    print("Invalid votes:", faulty)
    exit(0)

def handle_client(conn : socket.socket, addr, client_id : int, my_key, reg_serv_pub_key):
    client_key = None
    print(f"Client #{client_id} connected from {addr}")
    
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break

            id, code, text, client_key = deconstruct_message(data.decode(errors='replace'), client_key, my_key)

            if code == 'EB': check_and_publish_ballot(text, conn, client_key, my_key, reg_serv_pub_key)
            elif code == 'CIP': check_if_published(text, conn, client_key, my_key)
            elif code == 'ASK': add_symetrical_key(text, conn, client_key, my_key)
            elif code == 'EOV' and text == 'EOV': summarise(client_key)
            else: print('Unknown code')

    except ConnectionResetError:
        print(f"[-] Connection reset by client #{client_id} ({addr})")
    except Exception as e:
        print(f"[-] Error with client #{client_id} ({addr}): {e}")
    finally:
        print(f"[x] Client #{client_id} disconnected")
    
def main():
    v = VoterList()

    my_key = v.get_private_key(BB_SERVER_ID)['private_key']
    reg_serv_pub_key = v.get_public_keys()[str(REG_SERVER_ID)]['public_key']

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
        server.listen(BACKLOG)
        print(f"Server listening on {HOST}:{PORT} (CTRL-C to stop)")

        while True:
            conn, addr = server.accept()
            cid = next(client_id_counter)
            t = threading.Thread(target=handle_client, args=(conn, addr, cid, my_key, reg_serv_pub_key), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down (keyboard interrupt).")
    except Exception as e:
        print(f"[!] Server error: {e}")
    finally:
        try:
            server.close()
        except:
            pass
        print("[!] Server closed")

if __name__ == "__main__": main()
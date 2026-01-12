import itertools, json, os, socket, sys, threading

from ballot_list import BallotList
from voter_list import VoterList
from tools import _b64_decode, construct_message, deconstruct_message, verify_blind_signature

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
    
def send_empty_ballot(id : int, conn : socket, client_key, my_key):
    print(f"Voter {id}: requesting an empty ballot")

    empty_ballot = get_ballot()
    empty_ballot_json = json.dumps(empty_ballot)

    print(f"Answering voter {id}")
    conn.sendall(construct_message(BB_SERVER_ID, 'GEB_ANS', empty_ballot_json, my_key, client_key))

def check_and_publish_ballot(id, text, conn, client_key, my_key, reg_serv_pub_key):
    print(f"Voter {id}: sending filled ballot for publication")

    package = json.loads(text)
    signed_t = package['signed_t']
    hash_t = _b64_decode(package['hash_t'])
    BS = package['BS']

    if verify_blind_signature(signed_t, hash_t, reg_serv_pub_key):
        print("Blind signature verified")
    else:
        print("Token signature invalid")
        return

    b.append(BS, signed_t, hash_t)
    conn.sendall(construct_message(BB_SERVER_ID, 'ACK', 'ACK', my_key, client_key))


def check_if_published(id : int, string : str, conn : socket, client_key, my_key, reg_serv_pub_key):
    print(f"Voter {id}: checking the list")

    package = json.loads(string)
    BS = package['BS']
    hash_t = _b64_decode(package['hash_t'])

    with lock:
        text = 'TRUE' if b.check_if_published(BS, hash_t, reg_serv_pub_key) else 'FALSE'
        print(f"Check result: {text}")
    conn.sendall(construct_message(BB_SERVER_ID, 'CIP_ANS', text, my_key, client_key))
    
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

def handle_client(conn : socket.socket, addr, client_id : int, my_key, reg_serv_pub_key):
    client_key = None
    print(f"Client #{client_id} connected from {addr}")
    
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break

            id, code, text, client_key = deconstruct_message(data.decode(errors='replace'), client_key, my_key)

            if code == 'GEB': send_empty_ballot(id, conn, client_key, my_key)
            elif code == 'FB': check_and_publish_ballot(id, text, conn, client_key, my_key, reg_serv_pub_key)
            elif code == 'CIP': check_if_published(id, text, conn, client_key, my_key, reg_serv_pub_key)
            elif code == 'EOV' and text == 'EOV':
                summarise(client_key)
                print("\n[!] Voting finished. Summarise function completed. Server shutting down...")
                os._exit(0)
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
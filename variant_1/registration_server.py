import itertools
import json
import socket
import threading

from tools import blind_sign, construct_message, deconstruct_message
from voter_list import VoterList

HOST = "127.0.0.1"
PORT = 2137
BACKLOG = 10
BUFFER_SIZE = 4096

REG_SERVER_ID = 0

client_id_counter = itertools.count(1)

def get_ballot():
    with open('ballot') as f:
        return json.loads(f.read())

def send_empty_ballot(id : int, conn : socket, client_key, my_key):
    print(f"Voter {id}: requesting an empty ballot")

    empty_ballot = get_ballot()
    empty_ballot_json = json.dumps(empty_ballot)

    print(f"Answering voter {id}")
    conn.sendall(construct_message(REG_SERVER_ID, 'GEB_ANS', empty_ballot_json, my_key, client_key))

def validate_ballot(id : int, text : str, conn : socket, client_key, my_key):
    print(f"Voter {id}: requesting ballot validation")

    blinded_m_BS = int(text)
    signed = str(blind_sign(blinded_m_BS, my_key))

    print(f"Validating ballot for voter {id}")
    conn.sendall(construct_message(REG_SERVER_ID, 'FB_ANS', signed, my_key, client_key))

def handle_client(conn : socket.socket, addr, client_id : int, my_key):
    client_key = None
    print(f"Client #{client_id} connected from {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break

            id, code, text, client_key = deconstruct_message(data.decode(errors='replace'), client_key, my_key)

            if code == 'GEB': send_empty_ballot(id, conn, client_key, my_key)
            elif code == 'FB': validate_ballot(id, text, conn, client_key, my_key)

    except ConnectionResetError:
        print(f"[-] Connection reset by client #{client_id} ({addr})")
    except Exception as e:
        print(f"[-] Error with client #{client_id} ({addr}): {e}")
    finally:
        print(f"[x] Client #{client_id} disconnected")

def main():
    v = VoterList()

    my_key = v.get_private_key(REG_SERVER_ID)['private_key']

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
        server.listen(BACKLOG)
        print(f"Server listening on {HOST}:{PORT} (CTRL-C to stop)")

        while True:
            conn, addr = server.accept()
            cid = next(client_id_counter)
            t = threading.Thread(target=handle_client, args=(conn, addr, cid, my_key), daemon=True)
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
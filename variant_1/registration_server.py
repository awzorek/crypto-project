import socket
import threading
import itertools

from voter_list import VoterList
from tools import encrypt, decrypt, sign, verify
from tools import blind, blind_sign, unblind, verify_blind_signature
from tools import construct_message, deconstruct_message

HOST = "127.0.0.1"
PORT = 2137
BACKLOG = 5
BUFFER_SIZE = 4096

client_id_counter = itertools.count(1)

def send_empty_ballot():
    pass

def handle_client(conn : socket.socket, addr, client_id : int, my_key):
    client_key = None
    print(f"Client #{client_id} connected from {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break

            id, code, text, client_key = deconstruct_message(data.decode(errors='replace'), client_key, my_key)

            print(f"Voter {id}: {code} {text}")
            print(f"Answering voter {id}...")

            conn.sendall(construct_message(0, 'ANS', 'We welcome you to the RS', my_key, client_key))
    except ConnectionResetError:
        print(f"[-] Connection reset by client #{client_id} ({addr})")
    except Exception as e:
        print(f"[-] Error with client #{client_id} ({addr}): {e}")
    finally:
        print(f"[x] Client #{client_id} disconnected")

def main():
    v = VoterList()
    v.read()

    my_key = v.get_private_key(0)['private_key']

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
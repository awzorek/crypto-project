import itertools, json, socket, threading

from tools import blind_sign, construct_message, deconstruct_message
from voter_list import VoterList

HOST = "127.0.0.1"
PORT = 2137
BACKLOG = 10
BUFFER_SIZE = 4096

REG_SERVER_ID = 0

client_id_counter = itertools.count(1)
signed_tokens = {}
lock = threading.Lock()

def sign_t_token(id : int, conn : socket, t_token : str, client_key, my_key):
    if id in signed_tokens.keys():
        print(f"Voter {id} trying to register again, sending already signed token.")
        conn.sendall(construct_message(REG_SERVER_ID, 'REG_ANS', signed_tokens[id], my_key, client_key))
        return

    print(f"Signing t_token for registration for voter {id}")
    blinded_t_token = int(t_token)
    signed = str(blind_sign(blinded_t_token, my_key))
    with lock : signed_tokens[id] = signed

    print(f"Answering voter {id}")
    conn.sendall(construct_message(REG_SERVER_ID, 'REG_ANS', signed, my_key, client_key))

def handle_client(conn : socket.socket, addr, client_id : int, my_key):
    client_key = None
    print(f"Client #{client_id} connected from {addr}")
    
    try: 
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break

            id, code, text, client_key = deconstruct_message(data.decode(errors='replace'), client_key, my_key)

            # if code == 'GEB': send_empty_ballot(id, conn, client_key, my_key)
            # elif code == 'FB': validate_ballot(id, text, conn, client_key, my_key)

            if code == 'REG': sign_t_token(id, conn, text, client_key, my_key)
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
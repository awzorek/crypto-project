import socket
import threading
import itertools
import sys

HOST = "127.0.0.1"
PORT = 2137
BACKLOG = 5
BUFFER_SIZE = 1024

client_id_counter = itertools.count(1)  # gives unique IDs 1,2,3,...

def handle_client(conn: socket.socket, addr, client_id: int):
    """
    Handle messages from a single client.
    Server prints each message prefixed with client info.
    Replies "ACK" after each message.
    """
    print(f"[+] Client #{client_id} connected from {addr}")
    try:
        with conn:
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    # client closed connection
                    break
                message = data.decode(errors="replace")
                # print on server console
                print(f"[Client #{client_id} | {addr}] {message}")
                # if client requested to exit, acknowledge and break
                if message.strip().lower() == "exit":
                    conn.sendall("ACK".encode())
                    break
                # send ACK to client
                conn.sendall("ACK".encode())
    except ConnectionResetError:
        print(f"[-] Connection reset by client #{client_id} ({addr})")
    except Exception as e:
        print(f"[-] Error with client #{client_id} ({addr}): {e}")
    finally:
        print(f"[x] Client #{client_id} disconnected")

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((HOST, PORT))
        srv.listen(BACKLOG)
        print(f"Server listening on {HOST}:{PORT} (CTRL-C to stop)")
        while True:
            conn, addr = srv.accept()
            cid = next(client_id_counter)
            t = threading.Thread(target=handle_client, args=(conn, addr, cid), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down (keyboard interrupt).")
    except Exception as e:
        print(f"[!] Server error: {e}")
    finally:
        try:
            srv.close()
        except:
            pass
        print("[!] Server closed")

if __name__ == "__main__":
    main()
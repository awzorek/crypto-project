import socket

HOST = "127.0.0.1"
PORT = 2137
BUFFER_SIZE = 1024

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except ConnectionRefusedError:
            print(f"Could not connect to server at {HOST}:{PORT}")
            return

        print(f"Connected to server at {HOST}:{PORT}. Type messages. Type 'exit' to quit.")
        try:
            while True:
                msg = input("> ")
                if not msg:
                    # ignore empty lines
                    continue
                s.sendall(msg.encode())
                # wait for ACK
                data = s.recv(BUFFER_SIZE)
                if not data:
                    print("Server closed the connection.")
                    break
                print("Server:", data.decode())
                if msg.strip().lower() == "exit":
                    # we asked to exit; close client side
                    break
        except KeyboardInterrupt:
            print("\nInterrupted, closing.")
        except BrokenPipeError:
            print("Connection lost.")
        finally:
            s.close()

if __name__ == "__main__":
    main()
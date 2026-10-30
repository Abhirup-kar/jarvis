import socket
import subprocess
import threading
import json
import platform
import os

HOST = '0.0.0.0'
PORT = 8483

def handle_client(conn, addr):
    print(f"[JARVIS] Connected to {addr}")
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            command = data.decode('utf-8').strip()
            print(f"[JARVIS] Executing: {command}")
            
            if command.startswith("RUN:"):
                cmd = command[4:]
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                output = res.stdout + res.stderr
                conn.sendall(output.encode('utf-8'))
            elif command == "STATUS":
                status = json.dumps({"os": platform.system(), "node": platform.node(), "status": "ONLINE"})
                conn.sendall(status.encode('utf-8'))
            else:
                conn.sendall(b"UNKNOWN COMMAND")
    except Exception as e:
        print(f"[JARVIS] Error: {e}")
    finally:
      conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[JARVIS] Daemon listening on port {PORT}...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()

import socket
from threading import Thread
from peer_manager import PeerManager
import json

peer_manager = PeerManager()

def new_connection(addr, conn):
    print(f"[PeerServer] Connection from {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break  # peer đã ngắt
            try:
                msg = json.loads(data.decode())
            except json.JSONDecodeError:
                print("[PeerServer] Invalid message")
                continue
            
            action = msg.get("action")
            peer_id = msg.get("peer_id")
            
            if action == "register":
                peer_manager.register_peer(peer_id, addr[0], addr[1])
            elif action == "unregister":
                peer_manager.unregister_peer(peer_id)
            else:
                print(f"[PeerServer] Unknown action: {action}")

    except Exception as e:
        print(f"[PeerServer] Error {addr}: {e}")
    finally:
        # optional: cleanup khi client disconnect mà không gửi unregister
        for pid, (ip, port) in peer_manager.list_peers().items():
            if ip == addr[0] and port == addr[1]:
                peer_manager.unregister_peer(pid)
        conn.close()
        print(f"[PeerServer] Connection closed: {addr}")

def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def server_program(host, port):
    server_socket = socket.socket()
    server_socket.bind((host, port))

    server_socket.listen(108)
    while True:
        conn, addr = server_socket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()

if __name__ == '__main__':
    hostip = get_host_default_interface_ip()
    port = 2234
    print("listening on: {}:{}".format(hostip, port))
    server_program(hostip, port=port)
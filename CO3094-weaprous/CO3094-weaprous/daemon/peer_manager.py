from threading import Lock
from threading import Thread
from socket import socket

class PeerManager:
    def __init__(self):
        self.peers = {}  # peer_id -> (ip, port)
        self.lock = Lock()
    
    def register_peer(self, peer_id, ip, port):
         with self.lock:
            self.peers[peer_id] = (ip, port)
            print(f"[PeerManager] Registered {peer_id}: {ip}:{port}")
    def unregister_peer(self, peer_id):
        with self.lock:
            if peer_id in self.peers:
                del self.peers[peer_id]
                print(f"[PeerManager] Unregistered {peer_id}")

    def list_peers(self):
        with self.lock:
            return dict(self.peers)

    def get_peer(self, peer_id):
        with self.lock:
            return self.peers.get(peer_id)
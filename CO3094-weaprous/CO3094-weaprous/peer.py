#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse
import threading
import time

from daemon.weaprous import WeApRous

from daemon.request import Request
from daemon.response import Response

PORT = 8000  # Default port
P2P_PORT = 5000

app = WeApRous()

tracker_ip = '127.0.0.1'
tracker_port = '8080'

# Peer info
my_ip = '127.0.0.1'
my_p2p_port = P2P_PORT
my_username = 'Anonymous'

connected_peers = {}
# Peer info: {peer_id: {"ip": ..., "port": ..., "username": ...}}
peers_info = {}


def register_to_tracker():
    """Register this peer to tracker server"""
    try:
        data = {
            "ip": my_ip,
            "port": my_p2p_port,
            "username": my_username
        }
        print(f"[Peer] Registering to tracker: {data}")
        response = send_http_request('POST', '/submit-info', data)
        print(f"[Peer] Registration response: {response[:100]}")
        return True
    except Exception as e:
        print(f"[Peer] Registration failed: {e}")
        return False

def get_peers_from_tracker():
    """Get list of all peers from tracker"""
    try:
        response = send_http_request('GET', '/get-list', None)
        # Parse JSON from response body
        body_start = response.find('\r\n\r\n') + 4
        body = response[body_start:]
        data = json.loads(body)
        
        peers = data.get('peers', [])
        print(f"[Peer] Got {len(peers)} peers from tracker")
        
        # Update peers_info
        for peer in peers:
            # Skip self
            if peer['ip'] == my_ip and peer['port'] == my_p2p_port:
                continue
            peer_id = f"{peer['ip']}:{peer['port']}"
            peers_info[peer_id] = peer
        
        return peers
    except Exception as e:
        print(f"[Peer] Failed to get peers: {e}")
        return []

def connect_to_peer(peer_ip, peer_port):
    """Establish P2P connection to another peer"""
    try:
        peer_id = f"{peer_ip}:{peer_port}"
        
        # Check if already connected
        if peer_id in connected_peers:
            print(f"[Peer] Already connected to {peer_id}")
            return True
        
        # Create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((peer_ip, int(peer_port)))
        
        # Store connection
        connected_peers[peer_id] = sock
        
        # Start thread to receive messages from this peer
        thread = threading.Thread(
            target=handle_peer_messages,
            args=(sock, peer_id),
            daemon=True
        )
        thread.start()
        
        print(f"[Peer] Connected to peer {peer_id}")
        return True
        
    except Exception as e:
        print(f"[Peer] Failed to connect to {peer_ip}:{peer_port} - {e}")
        return False
    
def handle_peer_messages(sock, peer_id):
    """Receive and handle messages from a connected peer"""
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            
            message = data.decode('utf-8')
            print(f"\n[Peer] Message from {peer_id}: {message}")
            
            # Parse message (assume JSON format)
            try:
                msg_data = json.loads(message)
                msg_type = msg_data.get('type', 'chat')
                from_user = msg_data.get('from', 'Unknown')
                content = msg_data.get('message', '')
                
                print(f"[{from_user}]: {content}")
            except:
                print(f"[Peer] Raw message: {message}")
    
    except Exception as e:
        print(f"[Peer] Connection closed with {peer_id}: {e}")
    finally:
        # Remove from connected peers
        if peer_id in connected_peers:
            del connected_peers[peer_id]
        sock.close()

def send_to_peer(peer_id, message):
    """Send message to a specific connected peer"""
    try:
        if peer_id not in connected_peers:
            print(f"[Peer] Not connected to {peer_id}")
            return False
        
        sock = connected_peers[peer_id]
        
        # Create message format
        msg_data = {
            "type": "direct",
            "from": my_username,
            "to": peer_id,
            "message": message
        }
        
        msg_str = json.dumps(msg_data)
        sock.sendall(msg_str.encode('utf-8'))
        
        print(f"[Peer] Sent to {peer_id}: {message}")
        return True
        
    except Exception as e:
        print(f"[Peer] Failed to send to {peer_id}: {e}")
        return False
    
def broadcast_message(message):
    """Broadcast message to all connected peers"""
    msg_data = {
        "type": "broadcast",
        "from": my_username,
        "message": message
    }
    
    msg_str = json.dumps(msg_data)
    success_count = 0
    
    for peer_id, sock in list(connected_peers.items()):
        try:
            sock.sendall(msg_str.encode('utf-8'))
            success_count += 1
        except Exception as e:
            print(f"[Peer] Failed to broadcast to {peer_id}: {e}")
    
    print(f"[Peer] Broadcast to {success_count}/{len(connected_peers)} peers")
    return success_count

def start_p2p_server():
    """Start P2P server to accept incoming peer connections"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((my_ip, my_p2p_port))
        server.listen(10)
        print(f"[P2P Server] Listening on {my_ip}:{my_p2p_port}")
        
        while True:
            conn, addr = server.accept()
            peer_id = f"{addr[0]}:{addr[1]}"
            print(f"[P2P Server] Incoming connection from {peer_id}")
            
            # Store connection
            connected_peers[peer_id] = conn
            
            # Handle in separate thread
            thread = threading.Thread(
                target=handle_peer_messages,
                args=(conn, peer_id),
                daemon=True
            )
            thread.start()
            
    except Exception as e:
        print(f"[P2P Server] Error: {e}")
    finally:
        server.close()

@app.route('/connect-peer', methods=['POST'])
def connect(headers="guest", body="anonymous"):
    ############# Connect peer ##################
    try:
        target_ip = body.get('ip')
        target_port = body.get('port')
        
        if not target_ip or not target_port:
            return {"success": False, "message": "Missing ip or port"}
        
        success = connect_to_peer(target_ip, target_port)
        
        if success:
            return {"success": True, "message": f"Connected to {target_ip}:{target_port}"}
        else:
            return {"success": False, "message": "Connection failed"}
    
    except Exception as e:
        return {"success": False, "message": str(e)}
    
    
@app.route('/broadcast-peer', methods=['POST'])
def broadcast(headers, body):
    """Broadcast message to all CONNECTED peers"""
    try:
        message = body.get('message', '')
        
        if not message:
            return {"success": False, "message": "Empty message"}
        
        # If no peers connected, try to connect to all
        if len(connected_peers) == 0:
            print("[Peer] No connected peers, connecting to all known peers...")
            for peer_id, peer_info in peers_info.items():
                connect_to_peer(peer_info['ip'], peer_info['port'])
            time.sleep(1)  # Wait for connections
        
        count = broadcast_message(message)
        
        return {
            "success": True,
            "message": f"Broadcast to {count} peers",
            "peer_count": count
        }
    
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.route('/send-peer', methods=['POST'])
def send_message(headers, body):
    """Send message to a specific peer (auto-connect if not connected)"""
    try:
        target = body.get('target')  # peer_id: "127.0.0.1:5001"
        message = body.get('message', '')
        
        if not target or not message:
            return {"success": False, "message": "Missing target or message"}
        
        # Check if connected, if not → connect first
        if target not in connected_peers:
            print(f"[Peer] Not connected to {target}, connecting...")
            
            # Parse target
            peer_ip, peer_port = target.split(':')
            
            # Try to connect
            if not connect_to_peer(peer_ip, peer_port):
                return {"success": False, "message": "Failed to connect"}
            
            time.sleep(0.5)  # Wait for connection to establish
        
        # Now send
        success = send_to_peer(target, message)
        
        if success:
            return {"success": True, "message": f"Sent to {target}"}
        else:
            return {"success": False, "message": "Send failed"}
    
    except Exception as e:
        return {"success": False, "message": str(e)}

def send_http_request(method, path, data=None):
    """Send HTTP request to tracker"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((tracker_ip, int(tracker_port)))  # FIX: convert to int
    
    req = Request()
    req.method = method
    req.path = path
    req.headers = {
        "Host": f"{tracker_ip}:{tracker_port}",
        "Content-Type": "application/json",
        "Connection": "close"
    }
    
    if data:
        req.prepare_body(data=None, files=None, json=data)  # FIX: json → json_data
    else:
        req.body = ""
        req.prepare_content_length("")
    
    # Build raw HTTP request
    raw = f"{req.method} {req.path} HTTP/1.1\r\n"
    for k, v in req.headers.items():
        raw += f"{k}: {v}\r\n"
    raw += "\r\n"
    if req.body:
        raw += req.body
    
    s.sendall(raw.encode('utf-8'))
    
    # Receive response
    response_data = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        response_data += chunk
    
    s.close()
    return response_data.decode('utf-8')


if __name__ == "__main__":
    # ... parse args ...
    parser = argparse.ArgumentParser(prog='Peer', description='Chat Peer Node')
    parser.add_argument('--server-ip', default='127.0.0.1')
    parser.add_argument('--server-port', type=int, default=PORT)
    parser.add_argument('--p2p-port', type=int, default=P2P_PORT)
    parser.add_argument('--username', default='Anonymous')
    parser.add_argument('--tracker-ip', default='127.0.0.1')
    parser.add_argument('--tracker-port', type=int, default=8000)
 
    args = parser.parse_args()
    
    # Update global variables
    my_ip = args.server_ip
    my_p2p_port = args.p2p_port
    my_username = args.username
    tracker_ip = args.tracker_ip
    tracker_port = args.tracker_port
    
    print(f"[Peer] Starting peer: {my_username}")
    print(f"[Peer] API Server: {my_ip}:{args.server_port}")
    print(f"[Peer] P2P Server: {my_ip}:{my_p2p_port}")
    print(f"[Peer] Tracker: {tracker_ip}:{tracker_port}")
    # Start P2P server
    p2p_thread = threading.Thread(target=start_p2p_server, daemon=True)
    p2p_thread.start()
    time.sleep(1)
    
    # Register to tracker
    register_to_tracker()
    
    # Get peer list (chỉ lưu info, KHÔNG connect)
    get_peers_from_tracker()
    print(f"[Peer] Found {len(peers_info)} peers (not connected yet)")
    
    # Start API server
    app.prepare_address(my_ip, args.server_port)
    app.run()
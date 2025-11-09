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

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

app = WeApRous()

peers = []
channels = []
users = {
    "admin": "password"
}
@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    ############# Login ##################
    username = body.get('username','')
    password = body.get('password','')
    print("[Tracker] Login attempt: {}".format(username))
    if username in users and users[username] == password:
        return {"auth": True, "message": "Login success"}
    else:
        return {"auth": False, "message": "Invalid credentials"}
    
@app.route('/submit-info', methods=['POST'])
def submit_info(headers, body):
    ################# Add peer ip, port, username to peer list ##################
    try:
        if not any(p["ip"] == body["ip"] and p["port"] == body["port"] for p in peers):
            peers.append(body)
        print ("[Tracker] Register new peer: {}".format(body))
        return {"message": "Success"}
    except Exception as e:
        print(f"[Tracker] Error: {e}")
        return {"message": "Failed", "error": str(e)}

@app.route('/get-list', methods=['GET'])
def get_list(headers, body):
    ################# Get peer list ##################
    print("[Tracker] Get peer list")
    return {"peers":peers}

@app.route('/add-list', methods=['POST'])
def add_list(headers, body):
    ################# Add peer manually ##################
    if not any(p["ip"] == body["ip"] and p["port"] == body["port"] for p in peers):
        peers.append(body)
    print ("[Tracker] Register new peer: {}".format(body))
    return {"message": "Success"}

# ==================== CHANNEL MANAGEMENT ====================

@app.route('/add-channel', methods=['POST'])
def add_channel(headers, body):
    """Create new channel"""
    try:
        if "name" not in body:
            return {"success": False, "message": "Missing channel name"}
        
        channel_name = body["name"]
        
        # Check if channel exists
        if any(c["name"] == channel_name for c in channels):
            return {"success": False, "message": "Channel already exists"}
        
        # Create channel
        new_channel = {
            "name": channel_name,
            "members": [],
            "created_by": body.get("created_by", "anonymous"),
            "description": body.get("description", "")
        }
        
        channels.append(new_channel)
        print(f"[Tracker] New channel created: {channel_name}")
        
        return {"success": True, "message": "Channel created", "channel": new_channel}
        
    except Exception as e:
        print(f"[Tracker] Error creating channel: {e}")
        return {"success": False, "message": str(e)}

@app.route('/get-channels', methods=['GET'])
def get_channels(headers, body):
    """Get all channels"""
    print(f"[Tracker] Get channels - {len(channels)} channels")
    return {"success": True, "channels": channels}

@app.route('/join-channel', methods=['POST'])
def join_channel(headers, body):
    """Join a channel"""
    try:
        channel_name = body.get("channel")
        peer_id = body.get("peer_id")  # Format: "ip:port"
        username = body.get("username", "Anonymous")
        
        if not channel_name or not peer_id:
            return {"success": False, "message": "Missing channel or peer_id"}
        
        # Find channel
        channel = None
        for c in channels:
            if c["name"] == channel_name:
                channel = c
                break
        
        if not channel:
            return {"success": False, "message": "Channel not found"}
        
        # Check if already member
        if any(m["peer_id"] == peer_id for m in channel["members"]):
            return {"success": False, "message": "Already a member"}
        
        # Add member
        member = {
            "peer_id": peer_id,
            "username": username
        }
        channel["members"].append(member)
        
        print(f"[Tracker] {username} joined channel: {channel_name}")
        
        return {
            "success": True,
            "message": f"Joined {channel_name}",
            "members": channel["members"]
        }
        
    except Exception as e:
        print(f"[Tracker] Error joining channel: {e}")
        return {"success": False, "message": str(e)}

@app.route('/leave-channel', methods=['POST'])
def leave_channel(headers, body):
    """Leave a channel"""
    try:
        channel_name = body.get("channel")
        peer_id = body.get("peer_id")
        
        if not channel_name or not peer_id:
            return {"success": False, "message": "Missing channel or peer_id"}
        
        # Find channel
        channel = None
        for c in channels:
            if c["name"] == channel_name:
                channel = c
                break
        
        if not channel:
            return {"success": False, "message": "Channel not found"}
        
        # Remove member
        channel["members"] = [m for m in channel["members"] if m["peer_id"] != peer_id]
        
        print(f"[Tracker] Peer {peer_id} left channel: {channel_name}")
        
        return {"success": True, "message": f"Left {channel_name}"}
        
    except Exception as e:
        print(f"[Tracker] Error leaving channel: {e}")
        return {"success": False, "message": str(e)}

@app.route('/get-channel-members', methods=['POST'])
def get_channel_members(headers, body):
    """Get members of a specific channel"""
    try:
        channel_name = body.get("channel")
        
        if not channel_name:
            return {"success": False, "message": "Missing channel name"}
        
        # Find channel
        channel = None
        for c in channels:
            if c["name"] == channel_name:
                channel = c
                break
        
        if not channel:
            return {"success": False, "message": "Channel not found"}
        
        print(f"[Tracker] Get members of {channel_name} - {len(channel['members'])} members")
        
        return {
            "success": True,
            "channel": channel_name,
            "members": channel["members"]
        }
        
    except Exception as e:
        print(f"[Tracker] Error getting members: {e}")
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()

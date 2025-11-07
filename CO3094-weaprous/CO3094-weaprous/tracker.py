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
    if username == "admin" and password == "password":
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
    return {"peer":peers}

@app.route('/add-list', methods=['POST'])
def add_list(headers, body):
    ################# Add peer manually ##################
    if not any(p["ip"] == body["ip"] and p["port"] == body["port"] for p in peers):
        peers.append(body)
    print ("[Tracker] Register new peer: {}".format(body))
    return {"message": "Success"}

@app.route('/add-channel', methods=['POST'])
def add_channel(headers, body):
    ################### Add new channel #####################
    if "name" not in body:
        return {"message": "Failed", "error": "Missing channel name"}
    
    if not any(c["name"] == body["name"] for c in channels):
        channels.append(body)
        print(f"[Tracker] New channel: {body['name']}")
        return {"message": "Success"}
    return {"message": "Channel already exists"}

@app.route('/get-channels', methods=['GET'])
def get_channels(headers, body):
    ######################### get channel list #################
    return {"channels": channels}

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
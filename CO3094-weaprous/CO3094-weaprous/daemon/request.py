#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

############ add import###########
from urllib.parse import urlencode
import json as jsonlib
import base64

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None
        ##############: Add self.version   ################
        self.version = None
        self.auth = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        
        if not routes == {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            #
            # self.hook manipulation goes here
            # ...
            #

        self.headers = self.prepare_headers(request)
        cookies = self.headers.get('cookie', '')
            #
            #  TODO: implement the cookie function here
            #        by parsing the header            #
            #############Body######################
        self.body = self._extract_body(request)
            ###############Da hoan thanh ################
        self.cookies = {}
        if cookies:
            for cookie in cookies.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    key, val = cookie.split('=',1)
                    self.cookies[key.lower()] = val
        return self

    def prepare_body(self, data, files, json=None):
        ##########-----Add here-----####################
        body = ""
        if json is not None:
            body = jsonlib.dumps(json)
        elif data is not None:
            if isinstance(data,dict):
                body = urlencode(data)
        else:
            body = str(data)
            #Tam bo qua file
        ###################################
        self.prepare_content_length(body)
        self.body = body
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_content_length(self, body):
        self.headers["Content-Length"] = "0"
        ###############--Add here----############
        if body is None:
            length = 0
        elif isinstance(body, str):
            length = len(body.encode("utf-8"))
        elif isinstance(body, dict):
            length = len(jsonlib.dumps(body).encode("utf-8"))
        else:
            length = len(str(body).encode("utf-8"))

        self.headers["Content-Length"] = str(length)
        ##################################
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies

    def _extract_body(self, request):
        """
        Extract and parse body from raw HTTP request.
        
        :param request: Raw HTTP request string
        :return: Parsed body (dict for JSON/form, string for plain text, or None)
        """
        # Find the end of headers (double CRLF)
        try:
            header_end = request.index('\r\n\r\n')
            raw_body = request[header_end + 4:].strip()
        except ValueError:
            # No body found
            return None
        
        # If no body content
        if not raw_body:
            return None
        
        # Get Content-Type to determine how to parse
        content_type = self.headers.get('content-type', '').lower()
        
        # Parse based on Content-Type
        if 'application/json' in content_type:
            try:
                return jsonlib.loads(raw_body)
            except jsonlib.JSONDecodeError as e:
                print(f"[Request] JSON parse error: {e}")
                return raw_body
        
        elif 'application/x-www-form-urlencoded' in content_type:
        # Parse form data: username=admin&password=password
            body_dict = {}
            for pair in raw_body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    body_dict[key] = value
            return body_dict
        
        else:
            # Plain text or unknown type
            return raw_body

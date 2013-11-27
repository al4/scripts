#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Take a websocket challenge from a client:

GET /mychat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==
Sec-WebSocket-Protocol: chat
Sec-WebSocket-Version: 13
Origin: http://example.com

... and formulate the correct server response:

HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: HSmrc0sMlYUkAGmm5OPpG2HaGWk=
Sec-WebSocket-Protocol: chat
'''

import sys
import hashlib
import base64
import os
import os.path
import socket
# from time import sleep


def server():
    sockfile = "/tmp/SOCKET"

    if os.path.exists(sockfile):
        os.remove(sockfile)

    print("Opening socket...")

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sockfile)
    server.listen(5)

    os.chmod(sockfile, 0666)

    print("Listening...")
    while True:
        conn, addr = server.accept()

        print("Accepted connection")

        while 1:
            data = conn.recv(1024)
            if not data:
                break

            try:
                # Shitty hack to determine if we're dealing with headers or websocket frames
                x = data.decode('ascii')
            except:
                # Decode ws frame
                data = decode(data)

            print("<" + "-" * 20)
            response_key = ""

            for line in data.splitlines():
                print(line)
                l = line.split(": ")
                if l[0] == "Sec-WebSocket-Key":
                    response_key = gen_server_key(l[1].rstrip())
            print("-" * 20)

            if "DONE" == data:
                break

            # Build response
            if len(response_key) > 0:
                print("Calculated key: " + response_key)

                response = '''HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: %s
Sec-WebSocket-Protocol: chat

''' % response_key
                print(">" + "-" * 20)
                print(response)
            else:
                response = reply()

            try:
                conn.send(response)
            except socket.error:
                print("Connection ended")
                return False

    print("-" * 20)
    print("Shutting down...")


def gen_server_key(client_key):
    guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    return base64.b64encode(hashlib.sha1(client_key + guid).digest())


def reply():
    # Get a response from the user
    # sys.stdin = os.fdopen(3, "w")
    sys.stdin = open('/dev/tty')
    try:
        string = raw_input('--> ')
        if string == "quit":
            raise SystemExit
        # sys.stdout.write(i + '\n')
    except EOFError:
        sys.stderr.write("\rGot EOF\n")
        raise SystemExit

    uString = bytes.decode("utf8")

    bytesFormatted = []
    bytesFormatted.append(129)
    # indexStartRawData = -1

    bytesFormatted.append(len(uString))
    bytesFormatted.append(uString)

    response = "".join(str(x) for x in bytesFormatted)

    return response


def decode(data):
    # Decodes a websocket frame
    frame = bytearray(data)

    length = frame[1] & 127

    indexFirstMask = 2
    if length == 126:
        indexFirstMask = 4
    elif length == 127:
        indexFirstMask = 10

    indexFirstDataByte = indexFirstMask + 4
    mask = frame[indexFirstMask:indexFirstDataByte]

    i = indexFirstDataByte
    j = 0
    decoded = []
    while i < len(frame):
        decoded.append(frame[i] ^ mask[j % 4])
        i += 1
        j += 1

    # print decoded

    return "".join(chr(byte) for byte in decoded)


if __name__ == "__main__":
    while 1:
        server()


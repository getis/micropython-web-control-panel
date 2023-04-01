# use web interface to control an LED

import utime
import network
import socket
import urequests
from NetworkCredentials import NetworkCredentials
from RequestParser import RequestParser
from WiFiConnection import WiFiConnection

# connect to WiFi
if not WiFiConnection.start_station_mode(True):
    raise RuntimeError('network connection failed')

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print('listening on', addr)

# main loop
while True:
    client, client_addr = s.accept()
    raw_request = client.recv(1024)

    print("Request received")
    request = RequestParser(raw_request)
    print(request.method, request.url, request.get_action())
    for key in request.data():
        print(key, request.data()[key])

    client.send("HTTP/1.1 200 OK\r\n")
    client.send("Content-Type: application/json\r\n")
    client.send("\r\n")
    client.send("{ \"sensor\": 12345, \"reading2\": 98765, \"input\": \"hello\" }\r\n")
    client.close()
    print("Request closed")
    print()

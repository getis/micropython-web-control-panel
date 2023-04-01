# use web interface to display HTTP Request message

import utime
import network
import socket
import urequests
from NetworkCredentials import NetworkCredentials
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
    print("*** byte string ***")
    print()
    print(raw_request)
    print()
    # translate byte string to normal string variable
    decoded_request = raw_request.decode("utf-8")
    print("*** Decoded string ***")
    print()
    print(decoded_request)
    print()

    client.send("HTTP/1.1 200 OK\r\n\r\nRequest Received\r\n")
    client.close()

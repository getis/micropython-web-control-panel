# use web interface to control an LED

import utime
import network
import socket
import urequests
from NetworkCredentials import NetworkCredentials
from RequestParser import RequestParser
from ResponseBuilder import ResponseBuilder
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
    print()

    response_builder = ResponseBuilder()
    # filter out api request
    if request.url_match("/api"):
        action = request.get_action()
        if action == 'readData':
            response_obj = {
                'status': 0,
                'pot_value': 100,
                'temp_value': 25
            }
            response_builder.set_body_from_dict(response_obj)
        else:
            # unknown action
            response_builder.set_status(404)

    # try to serve static file
    else:
        response_builder.serve_static_file(request.url, "/api_index.html")

    response_builder.build_response()
    print(response_builder.response)

    client.send(response_builder.response)
    client.close()
    print("Request closed")
    print()

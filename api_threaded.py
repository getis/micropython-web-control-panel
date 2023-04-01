import time

import gc
import utime
import network
import urequests
import socket
from machine import Pin, ADC
from NetworkCredentials import NetworkCredentials
from RequestParser import RequestParser
import json
import _thread
from ResponseBuilder import ResponseBuilder
from WiFiConnection import WiFiConnection
from IoHandler import IoHandler
import random

# connect to WiFi
if not WiFiConnection.start_station_mode(True):
    raise RuntimeError('network connection failed')

def web_server():

    # Open socket
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print('listening on', addr)

    while True:
        cl = False
        try:
            cl, addr = s.accept()
            # print('client connected from', addr)
            raw_request = cl.recv(1024)

            request = RequestParser(raw_request)
            print(request.method, request.url, request.get_action())

            response_builder = ResponseBuilder()

            # filter out api request
            if request.url_match("/api"):
                action = request.get_action()
                if action == 'readData':
                    # ajax request for value of pot
                    pot_value = IoHandler.get_pot_reading()
                    temp_value = IoHandler.get_temp_reading()
                    cled_states = {
                        'blue': IoHandler.get_blue_led(),
                        'yellow': IoHandler.get_yellow_led(),
                        'green': IoHandler.get_green_led()
                    }
                    response_obj = {
                        'status': 0,
                        'pot_value': pot_value,
                        'temp_value': temp_value,
                        'cled_states': cled_states,
                        'rgb_leds': IoHandler.rgb_led_colours
                    }
                    response_builder.set_body_from_dict(response_obj)
                elif action == 'setLedColour':
                    # turn on requested coloured led
                    # returns json object with led states
                    led_colour = request.data()['colour']

                    status = 'OK'
                    cled_states = {
                        'blue': 0,
                        'yellow': 0,
                        'green': 0
                    }
                    if led_colour == 'blue':
                        cled_states['blue'] = 1
                    elif led_colour == 'yellow':
                        cled_states['yellow'] = 1
                    elif led_colour == 'green':
                        cled_states['green'] = 1
                    elif led_colour == 'off':
                        # leave leds off
                        pass
                    else:
                        status = 'Error'
                    IoHandler.set_coloured_leds([cled_states['blue'], cled_states['yellow'], cled_states['green']])
                    response_obj = {
                        'status': status,
                        'cled_states': cled_states
                    }
                    response_builder.set_body_from_dict(response_obj)
                elif action == 'setRgbColour':
                    # turn on requested coloured led
                    # returns json object with led states
                    rgb_red = int(request.data()['red'])
                    rgb_green = int(request.data()['green'])
                    rgb_blue = int(request.data()['blue'])

                    status = 'OK'
                    rgb_colours = {
                        'red': rgb_red,
                        'green': rgb_green,
                        'blue': rgb_blue
                    }
                    IoHandler.set_rgb_leds(rgb_red, rgb_green, rgb_blue)
                    response_obj = {
                        'status': status,
                        'rgb_colours': rgb_colours
                    }
                    response_builder.set_body_from_dict(response_obj)
                else:
                    # unknown action
                    response_builder.set_status(404)

            # try to serve static file
            else:
                response_builder.serve_static_file(request.url, "/api_index.html")

            response_builder.build_response()
            print("resp len = ", len(response_builder.response))
            sent = cl.write(response_builder.response)
            print("sent = ", sent)
            cl.close()

            # gc.collect()

        except OSError as e:
            cl.close()
            print('connection closed')


def main_loop():
    counter = 0
    while True:
        if counter % 70000 == 0:
            IoHandler.toggle_red_led()
            new_colour = (random.randint(0, 1) * 128, random.randint(0, 1) * 128, random.randint(0, 1) * 128)
            for pixel in range(7, 4, -1):
                IoHandler.set_rgb_pixel(pixel, IoHandler.get_rgb_pixel(pixel - 1))
            IoHandler.set_rgb_pixel(4, new_colour)
            IoHandler.show_rgb_leds()
        counter += 1

# web server on second processor
second_thread = _thread.start_new_thread(main_loop, ())

# main loop on first processor
web_server()

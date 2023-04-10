# non blocking web server using second core

import utime
import socket
from RequestParser import RequestParser
import _thread
from ResponseBuilder import ResponseBuilder
from WiFiConnection import WiFiConnection
from IoHandler import IoHandler
import random

# connect to WiFi
if not WiFiConnection.start_station_mode(True):
    raise RuntimeError('network connection failed')

# main function to run web server using blocking code
def web_server():

    # Open socket
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print('listening on', addr)

    # main web server loop
    while True:
        cl = False
        try:
            # wait for HTTP request
            cl, addr = s.accept()
            # print('client connected from', addr)
            raw_request = cl.recv(1024)

            # parse HTTP request
            request = RequestParser(raw_request)
            #print(request.method, request.url, request.get_action())

            # Prepare to build HTTP response
            response_builder = ResponseBuilder()

            # filter out api request
            if request.url_match("/api"):
                # read api action requested
                action = request.get_action()
                if action == 'readData':
                    # api request for sensor and data values
                    pot_value = IoHandler.get_pot_reading()
                    temp_value = IoHandler.get_temp_reading()
                    cled_states = {
                        'blue': IoHandler.get_blue_led(),
                        'yellow': IoHandler.get_yellow_led(),
                        'green': IoHandler.get_green_led()
                    }
                    # build the response data package
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

                    # get requested colour
                    led_colour = request.data()['colour']

                    # set default states of leds
                    status = 'OK'
                    cled_states = {
                        'blue': 0,
                        'yellow': 0,
                        'green': 0
                    }
                    # turn on requested led
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
                    # set led outputs
                    IoHandler.set_coloured_leds([cled_states['blue'], cled_states['yellow'], cled_states['green']])
                    # build the response data package
                    response_obj = {
                        'status': status,
                        'cled_states': cled_states
                    }
                    response_builder.set_body_from_dict(response_obj)
                elif action == 'setRgbColour':
                    # sets the RGB colour of the first 4 neopixels
                    rgb_red = int(request.data()['red'])
                    rgb_green = int(request.data()['green'])
                    rgb_blue = int(request.data()['blue'])

                    # build data for RGB leds
                    status = 'OK'
                    rgb_colours = {
                        'red': rgb_red,
                        'green': rgb_green,
                        'blue': rgb_blue
                    }
                    # set colour of neopixels in output handler
                    IoHandler.set_rgb_leds(rgb_red, rgb_green, rgb_blue)
                    # build the response data package
                    response_obj = {
                        'status': status,
                        'rgb_colours': rgb_colours
                    }
                    response_builder.set_body_from_dict(response_obj)
                else:
                    # unknown action - send back not found error status
                    response_builder.set_status(404)

            # try to serve static file
            else:
                # return file if valid
                response_builder.serve_static_file(request.url, "/api_index.html")

            # build the HTTP response
            response_builder.build_response()
            # return response to client
            sent = cl.write(response_builder.response)
            cl.close()

        except OSError as e:
            cl.close()
            print('connection closed')

# main control loop
def main_loop():
    counter = 0
    while True:
        # use simple loop with counter to get idea of speed of operation
        # 70000 loops per change of state in led
        if counter % 70000 == 0:
            # toggle state of red led
            IoHandler.toggle_red_led()
            # generate new RGB colour
            new_colour = (random.randint(0, 1) * 128, random.randint(0, 1) * 128, random.randint(0, 1) * 128)
            # shift bottom 3 neopixels along one slot
            for pixel in range(7, 4, -1):
                IoHandler.set_rgb_pixel(pixel, IoHandler.get_rgb_pixel(pixel - 1))
            # set bottom neopixel to new colour
            IoHandler.set_rgb_pixel(4, new_colour)
            # send colour data to neopixels
            IoHandler.show_rgb_leds()
            # reset counter
            counter = 0
        counter += 1

# run main control loop on second processor
second_thread = _thread.start_new_thread(main_loop, ())

# main loop on first processor
# NOTE : webs server doesn't seem to run on second core (???)
web_server()

# full demo with web control panel
# combines multi core and multi tasking

import utime
from RequestParser import RequestParser
import json
import uasyncio
import _thread
from ResponseBuilder import ResponseBuilder
from WiFiConnection import WiFiConnection
from IoHandler import IoHandler
import random

# connect to WiFi
if not WiFiConnection.start_station_mode(True):
    raise RuntimeError('network connection failed')


async def handle_request(reader, writer):
    try:
        raw_request = await reader.read(2048)

        request = RequestParser(raw_request)

        response_builder = ResponseBuilder()

        # filter out api request
        if request.url_match("/api"):
            action = request.get_action()
            if action == 'readData':
                # ajax request for data
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
                # set RGB colour of first 4 neopixels
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
        writer.write(response_builder.response)
        await writer.drain()
        await writer.wait_closed()

    except OSError as e:
        print('connection error ' + str(e.errno) + " " + str(e))


async def main():
    print('Setting up webserver...')
    server = uasyncio.start_server(handle_request, "0.0.0.0", 80)
    uasyncio.create_task(server)

    # main async loop on first core
    # just pulse the red led
    counter = 0
    while True:
        if counter % 500 == 0:
            IoHandler.toggle_red_led()
        counter += 1
        await uasyncio.sleep(0)

# run the top 4 neopixel scrolling loop
def neopixels():
    while True:
        new_colour = (random.randint(0, 1) * 128, random.randint(0, 1) * 128, random.randint(0, 1) * 128)
        for pixel in range(7, 4, -1):
            IoHandler.set_rgb_pixel(pixel, IoHandler.get_rgb_pixel(pixel - 1))
        IoHandler.set_rgb_pixel(4, new_colour)
        IoHandler.show_rgb_leds()
        utime.sleep(1)


# start neopixel scrolling loop on second processor
second_thread = _thread.start_new_thread(neopixels, ())

try:
    # start asyncio tasks on first core
    uasyncio.run(main())
finally:
    uasyncio.new_event_loop()

# using asyncio for non blocking web server

import utime
from RequestParser import RequestParser
import uasyncio
from ResponseBuilder import ResponseBuilder
from WiFiConnection import WiFiConnection
from IoHandler import IoHandler
import random

# connect to WiFi
if not WiFiConnection.start_station_mode(True):
    raise RuntimeError('network connection failed')

# coroutine to handle HTTP request
async def handle_request(reader, writer):
    try:
        # allow other tasks to run while waiting for data
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
                # returns json object with rgb colour
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

        # build response message
        response_builder.build_response()
        # send reponse back to client
        writer.write(response_builder.response)
        # allow other tasks to run while data being sent
        await writer.drain()
        await writer.wait_closed()

    except OSError as e:
        print('connection error ' + str(e.errno) + " " + str(e))


# coroutine that will run as the neopixel update task
async def neopixels():

    counter = 0
    while True:
        if counter % 1000 == 0:
            new_colour = (random.randint(0, 1) * 128, random.randint(0, 1) * 128, random.randint(0, 1) * 128)
            for pixel in range(7, 4, -1):
                IoHandler.set_rgb_pixel(pixel, IoHandler.get_rgb_pixel(pixel - 1))
            IoHandler.set_rgb_pixel(4, new_colour)
            IoHandler.show_rgb_leds()
        counter += 1
        # 0 second pause to allow other tasks to run
        await uasyncio.sleep(0)


# main coroutine to boot async tasks
async def main():
    # start web server task
    print('Setting up webserver...')
    server = uasyncio.start_server(handle_request, "0.0.0.0", 80)
    uasyncio.create_task(server)

    # start top 4 neopixel updating task
    uasyncio.create_task(neopixels())

    # main task control loop pulses red led
    counter = 0
    while True:
        if counter % 1000 == 0:
            IoHandler.toggle_red_led()
        counter += 1
        # 0 second pause to allow other tasks to run
        await uasyncio.sleep(0)


# start asyncio task and loop
try:
    # start the main async tasks
    uasyncio.run(main())
finally:
    # reset and start a new event loop for the task scheduler
    uasyncio.new_event_loop()

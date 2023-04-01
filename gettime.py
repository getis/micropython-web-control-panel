# use web service to get date and time information

import utime
import network
import urequests
from NetworkCredentials import NetworkCredentials

ssid = NetworkCredentials.ssid
password = NetworkCredentials.password

# set WiFi to station interface
wlan = network.WLAN(network.STA_IF)
# activate the network interface
wlan.active(True)
# connect to wifi network
wlan.connect(ssid, password)

max_wait = 10
# wait for connection
while max_wait > 0:
    """
        0   STAT_IDLE -- no connection and no activity,
        1   STAT_CONNECTING -- connecting in progress,
        -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
        -2  STAT_NO_AP_FOUND -- failed because no access point replied,
        -1  STAT_CONNECT_FAIL -- failed due to other problems,
        3   STAT_GOT_IP -- connection successful.
    """
    if wlan.status() < 0 or wlan.status() >= 3:
        # connection successful
        break
    max_wait -= 1
    print('waiting for connection... ' + str(max_wait))
    utime.sleep(1)

# check connection
if wlan.status() != 3:
    # No connection
    raise RuntimeError('network connection failed')
else:
    # connection successful
    print('wlan connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])

# main loop
while True:
    start = utime.ticks_ms()
    response = urequests.get('https://timeapi.io/api/Time/current/zone?timeZone=Europe/London')
    print('request took ' + str(utime.ticks_ms() - start) + "ms")
    print(response.content)
    print(response.json()['dateTime'])
    utime.sleep(5)

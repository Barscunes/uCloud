#!/usr/bin/python

import mosquitto
import serial

import sys
from select import select


def on_connect(mosq, obj, rc):
    mqttc.publish("ucloud/post", str(json), 0)


def kbhit():
    dr, dw, de = select([sys.stdin], [], [], 0)
    return dr != []

# json={
# 		'name': 'lightsensor',
# 		"suscribeto": [
# 		{
# 			"lightSensorState": [
# 			"Mucha luz",
# 			"Suficiente luz",
# 			"Poca luz"
# 			]
# 		}
# 		],
# 		"publishto": [
# 		{

# 		}
# 		]
# 		}
json = {
    "mac": 4,
    'json': {"name": 'lightsensor', 'state': ''},
    'metajson': {'/name': {'action': "pass", 'value': 'replace',
                           'validmsg': '', 'validtype': ''},
                 'setup': {'lightsensorstate':
                           {'action': 'subscribe', 'msg':
                            'lightsensorstate', 'type': 'MQTT'}},
                 'setdown': {'lightsensorstate':
                             {'action': 'unsubscribe', 'msg':
                              'lightsensorstate', 'type': 'MQTT'}},
                 'show': [{'name': 'state', 'type': 'MQTT',
                           'validmsg': ['Mucha luz', 'Suficiente luz',
                                        'Poca luz'],
                           'validtype': 'str', 'topic': 'lightsensorstate',
                           'pattern': 'publisher',
                           'notes': 'Shows the current ' +
                                    'state of the Sensor light'}],
                 'mqtt/lightsensorstate': {'dir': 'state', 'action': "pass",
                                           'value': 'replace',
                                           'validmsg': ['high', 'medium',
                                                        'low'],
                                           'validtype': 'unicode'}}}
mqttc = mosquitto.Mosquitto()
mqttc.on_connect = on_connect

mqttc.connect("0.0.0.0")
port = "/dev/ttyACM0"
serialFromArduino = serial.Serial(port, 9600, timeout=0.05)
serialFromArduino.flushInput()

while mqttc.loop() == 0:
    try:
        com = serialFromArduino.readline()
        if com != "":
            mqttc.publish("lightsensorstate", com.rstrip(), 0)
        if kbhit():
            Salir = raw_input(">")
            if Salir == "salir":
                mqttc.publish("ucloud/delete", str(json), 0)
                mqttc.loop_stop()
                mqttc.disconnect()
                sys.exit()
    except KeyboardInterrupt:
        mqttc.loop_stop()
        mqttc.disconnect()

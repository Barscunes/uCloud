#!/usr/bin/python

import mosquitto
import serial

import sys
from select import select
from LampSuscriptions import LampSuscriptions


def on_connect(mosq, obj, rc):

    mqttc.subscribe("powerlamp", 0)
    mqttc.subscribe("assignlamptopic", 0)
    mqttc.subscribe("assignlampmsgon", 0)
    mqttc.subscribe("assignlampmsgoff", 0)
    mqttc.subscribe("lampunlinktopic", 0)
    mqttc.subscribe("lampunlinkmsgon", 0)
    mqttc.subscribe("lampunlinkmsgoff", 0)
    mqttc.publish("ucloud/post", str(json), 0)


def on_message(mosq, obj, msg):
    print "topic " + str(msg.topic)
    print "mensaje " + str(msg.payload)
    if str(msg.topic) == "powerlamp":

        if str(msg.payload) == "1":
            serialFromArduino.write('1')
            mqttc.publish("lampstate", 1, 0)
        elif str(msg.payload) == "0":
            serialFromArduino.write('0')
            mqttc.publish("lampstate", 0, 0)

    elif str(msg.topic) == "assignlamptopic":
        mqttc.subscribe(msg.payload, 0)

    elif str(msg.topic) == "assignlampmsgon":
        lampsuscriptions.newOn(msg.payload)

    elif str(msg.topic) == "assignlampmsgoff":
        lampsuscriptions.newOff(msg.payload)

    elif str(msg.topic) == "lampunlinktopic":
        mqttc.unsubscribe(msg.payload)

    elif str(msg.topic) == "lampunlinkmsgon":
        lampsuscriptions.remOn(msg.payload)

    elif str(msg.topic) == "lampunlinkmsgoff":
        lampsuscriptions.remOff(msg.payload)
    else:

        if lampsuscriptions.containOn(msg.payload):
            serialFromArduino.write('1')
            mqttc.publish("lampstate", 1, 0)
        elif lampsuscriptions.containOff(msg.payload):
            serialFromArduino.write('0')
            mqttc.publish("lampstate", 0, 0)


def kbhit():
    dr, dw, de = select([sys.stdin], [], [], 0)
    return dr != []

# json={
# 		'name': 'lamp',
# 		"suscribeto": [
# 		{

# 		}
# 		],
# 		"publishto": [
# 		{
# 			"powerlamp": "0",
# 			"assignlamptopic": "",
# 			"assignlampmsgon": "",
# 			"assignlampmsgoff": ""
# 	}
# 	]
# 	}

json = {
    "mac": 3,
    'json': {"name": 'lamp', 'state': 0, 'power': '',
             'control': {'msg_on': [], 'msg_off': [], 'topic': [],
                             'unlink_msg_on': '', 'unlink_msg_off': '',
                             'unlink_topic': ''}},
    'metajson': {'/name': {'action': "pass", 'value': 'replace',
                           'validmsg': '', 'validtype': ''},
                 '/power': {'action': 'send', 'value': 'erase',
                            'validmsg': ['on', 'off', 1, 0, True, False],
                            'validtype': ['bool', 'unicode', 'int'],
                            'topic': 'powerlamp', 'type': 'MQTT'},
                 '/control/msg_on': {'action': 'send', 'value': 'add',
                                     'validmsg': '', 'validtype': '',
                                     'topic': 'assignlampmsgon',
                                     'type': 'MQTT'},
                 '/control/msg_off': {'action': 'send', 'value': 'add',
                                      'validmsg': '', 'validtype': '',
                                      'topic': 'assignlampmsgoff',
                                      'type': 'MQTT'},
                 '/control/topic': {'action': 'send', 'value': 'add',
                                    'validmsg': '', 'validtype': '',
                                    'topic': 'assignlamptopic',
                                    'type': 'MQTT'},
                 '/control/unlink_msg_on': {'action': 'send',
                                            'item': {'key': 'msg_on',
                                                     'value': 'remove',
                                                     'validmsg': '',
                                                     'validtype': ''},
                                            'value': 'erase',
                                            'validmsg': '',
                                            'validtype': '',
                                            'topic': 'lampunlinkmsgon',
                                            'type': 'MQTT'},
                 '/control/unlink_msg_off': {'action': 'send',
                                             'item': {'key': 'msg_off',
                                                      'value': 'remove',
                                                      'validmsg': '',
                                                      'validtype': ''},
                                             'value': 'erase',
                                             'validmsg': '',
                                             'validtype': '',
                                             'topic': 'lampunlinkmsgoff',
                                             'type': 'MQTT'},
                 '/control/unlink_topic': {'action': 'send',
                                           'item': {'key': 'topic',
                                                    'value': 'remove',
                                                    'validmsg': '',
                                                    'validtype': ''},
                                           'value': 'erase',
                                           'validmsg': '',
                                           'validtype': '',
                                           'topic': 'lampunlinktopic',
                                           'type': 'MQTT'},
                 'setup': {'lampstate': {'action': 'subscribe',
                                         'msg': 'lampstate', 'type': 'MQTT'}},
                 'setdown': {'lampstate': {'action': 'unsubscribe',
                                           'msg': 'lampstate',
                                           'type': 'MQTT'}},
                 'show': [{'name': 'power', 'type': 'MQTT', 'validmsg': [0, 1],
                           'validtype': 'int', 'pattern': 'listener',
                           'dir': 'power',
                           'notes': 'Turn on and off the lamp'},
                          {'name': 'state', 'type': 'MQTT', 'validmsg': [0, 1],
                           'validtype': 'int', 'topic': 'lampstate',
                           'pattern': 'publisher',
                           'notes': 'Shows the current state of the lamp'},
                          {'name': 'msg_on', 'type': 'MQTT', 'validmsg': '',
                           'validtype': '', 'pattern': 'subscriber',
                           'dir': {'control': 'msg_on'},
                           'notes': 'Link the message sent ' +
                                    'to switch on the lamp'},
                          {'name': 'msg_off', 'type': 'MQTT', 'validmsg': '',
                           'validtype': '', 'pattern': 'subscriber',
                           'dir': {'control': 'msg_off'},
                           'notes': 'Link the message sent ' +
                                    'to switch off the lamp'},
                          {'name': 'topic', 'type': 'MQTT', 'validmsg': '',
                           'validtype': '', 'pattern': 'subscriber',
                           'dir': {'control': 'topic'},
                           'notes': 'Subscribe to the message sent'},
                          {'name': 'unlink_msg_on', 'type': 'MQTT',
                           'validmsg': '', 'validtype': '',
                           'pattern': 'manage',
                           'dir': {'control': 'unlink_msg_on'},
                           'notes': 'Unlink the message sent ' +
                                    'with the switch on action of the lamp'},
                          {'name': 'unlink_msg_off', 'type': 'MQTT',
                           'validmsg': '', 'validtype': '',
                           'pattern': 'manage',
                           'dir': {'control': 'unlink_msg_off'},
                           'notes': 'Unlink the message sent ' +
                                    'with the switch off action of the lamp'},
                          {'name': 'unlink_topic', 'type': 'MQTT',
                           'validmsg': '', 'validtype': '',
                           'pattern': 'manage',
                           'dir': {'control': 'unlink_topic'},
                           'notes': 'Unsubscribe to the message sent'}],
                 'mqtt/lampstate': {'dir': 'state', 'action': "pass",
                                    'value': 'replace', 'validmsg': [0, 1],
                                    'validtype': 'int'}}}
mqttc = mosquitto.Mosquitto()
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect("0.0.0.0")
port = "/dev/ttyACM1"
serialFromArduino = serial.Serial(port, 9600)
serialFromArduino.flushInput()
lampsuscriptions = LampSuscriptions()

while mqttc.loop() == 0:
    try:
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

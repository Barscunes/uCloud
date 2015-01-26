from __future__ import print_function
import paho.mqtt.client as mqtt
import requests
import zmq
import sys
from select import select
import json
import ast
sys.path.append('../Classes')
from things import Things

# #############################################################
# ##################### MQTT EVENTS ###########################
# #############################################################

# ################# Initial setup for the MQTT Client ########################


def on_connect(_client, _userdata, _rc):
    _mqtt_client.subscribe(UNAME + '/post', 0)
    _mqtt_client.subscribe(UNAME + '/delete', 0)

# ################# Behavior when message is received ########################


def on_message(_client, _userdata, _msg):
    print("MSG" + _msg.payload)
    if _msg.topic == UNAME + '/post' or _msg.topic == UNAME + '/delete':
        _send_rest(_msg.topic, _msg.payload)
    else:
        _msg = _things.check_inst('mqtt/' + _msg.topic, _msg.payload,
                                  'metajsonid')
        _actions[_msg[0]['action']](_msg[1])

# #############################################################
# ##################### FUNCTINONS ############################
# #############################################################

# ################# Send the payload to the REST server ######################


def _send_rest(_topic, _payload):
    _msg_conv = ast.literal_eval(_payload)
    _send_rest = _rest_opt[_topic](_msg_conv)
    print ("Status:" + str(_send_rest.status_code))
    print ("Json:" + str(_send_rest.json()))

# ################# Obtain keyboard input  ########################


def kbhit():
    _dr, _dw, _de = select([sys.stdin], [], [], 0)
    return _dr != []

# ############# Start the ZeroMQ Publisher and Subscriber #####################


def _start_zeromq_client():
    global _zero_pub, _zero_sub, _context
    _context = zmq.Context()
    _zero_pub = _context.socket(zmq.PUB)
    _zero_pub.bind("tcp://*:5560")

    _zero_sub = _context.socket(zmq.SUB)
    _zero_sub.connect("tcp://localhost:5561")
    _zero_sub.setsockopt(zmq.SUBSCRIBE, "MQTTPub")
    _zero_sub.setsockopt(zmq.SUBSCRIBE, "MQTTSub")
    _zero_sub.setsockopt(zmq.SUBSCRIBE, "MQTTUnsub")
    _zero_sub.setsockopt(zmq.RCVTIMEO, 1000)

# #############################################################
# ######################## MAIN ###############################
# #############################################################

UNAME = 'ucloud'
_things = Things()
_rest_opt = {
    UNAME + '/post': lambda x: requests.post('http://localhost:8000/'
                                             + UNAME + '/thing',
                                             data=json.dumps(x),
                                             headers={'content-type':
                                                      'application/json'}),

    UNAME + '/delete': lambda x: requests.delete('http://localhost:8000/'
                                                 + UNAME + '/thing',
                                                 data=json.dumps(x),
                                                 headers={'content-type':
                                                          'application/json'})
}
_zero_opt = {
    'MQTTPub': lambda x: _mqtt_client.publish(x['topic'], str(x['msg']), 0),
    'MQTTSub': lambda x: _mqtt_client.subscribe(x, 0),
    'MQTTUnsub': lambda x: _mqtt_client.unsubscribe(x)
}

_actions = {
    'print': lambda x: print(x),
    'send': lambda x: _zero_pub.send_multipart([x['topic'], x['msg']]),
    'pass': lambda x: x
}

_mqtt_client = mqtt.Client()
_mqtt_client.on_connect = on_connect
_mqtt_client.on_message = on_message

_mqtt_client.connect("0.0.0.0")

_zero_sub = ''
_zero_pub = ''
_context = ''

_start_zeromq_client()

# ################# MQTT Loop and ZeroMQ Listener ########################

while _mqtt_client.loop() == 0:

    try:
        [_address, _contents] = _zero_sub.recv_multipart()
        print("[%s] %s" % (_address, _contents))
        try:
            _contents = ast.literal_eval(_contents)
        except:
            pass
        _zero_opt[_address](_contents)
    except:
        if kbhit():
            msg = raw_input(">")
            if msg == "salir":
                _zero_sub.close()
                _zero_pub.close()
                _context.term()
                sys.exit()
            else:
                _zero_pub.send_multipart(["REST", "PUB:" + msg])

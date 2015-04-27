from __future__ import print_function
import paho.mqtt.client as mqtt
import requests
import zmq
import sys
from select import select
import json
import ast
sys.path.append('../Classes')
import things
import constants

# #############################################################################
# ################################### MAIN ####################################
# #############################################################################

# ################### Constants and variables assignments #####################
PORT = constants.retrieve('MQTTPort.txt')
GENERAL = constants.retrieve('General.txt')
UNAME = GENERAL['UNAME']
IDENTIFIER = GENERAL['IDENTIFIER']
JSONID = GENERAL['JSONID']
METAJSONID = GENERAL['METAJSONID']
PORT_NAME = PORT['PORT_NAME']
DB_COLUMN = {
    IDENTIFIER: 'identifier',
    JSONID: 'jsonid',
    METAJSONID: 'metajsonid'
}
SUBSCRIPTIONS = PORT['SUBSCRIPTIONS']
PORT_PUB = PORT['PORT_PUB']
PORTS_SUB = PORT['PORT_SUB']
TOPICS_SUB = PORT['TOPIC_SUB']
REST_TOPICS = PORT['REST_TOPICS']
INSTRUCTIONS = 0
MSG = 1
KNOWN_ERRORS = {'malformed string': 'invalid_msg',
                'unexpected EOF': 'invalid_msg',
                'Connection refused': 'refused', 'Address already': 'address',

                'Invalid argument': 'invalid_input',
                'string indices must be integers': 'incomplete_inst',
                'Unknown action': 'unkwn_action',
                "object has no attribute '__getitem__'": 'no_inst'}
mqtt_client = mqtt.Client()
context = zmq.Context()
zero_pub = context.socket(zmq.PUB)
zero_sub = context.socket(zmq.SUB)

# ########################### Dictionary switches #############################
_error_msg = {
    'invalid_msg': lambda x: print('Invalid payload'),
    'refused': lambda x: print('Rest service unavailable'),
    'address': lambda x: print('Address already in use'),
    'undefined': lambda x: print('Undefined error'),
    'invalid_input': lambda x: print("Can't start zmq client, check the "
                                     + 'constants file for input errors'),
    'incomplete_inst': lambda x: print('Incomplete instruction'),
    'unkwn_action': lambda x: print(x),
    'no_inst': lambda x: print("The message wasn't an Instruction")
}
_missing_data = {
    UNAME + '/post': lambda msg: things.missing_data(msg, ''),
    UNAME + '/delete': lambda msg: IDENTIFIER not in msg

}
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
                                                          'application' +
                                                          '/json'})
}
_zero_opt = {
    'MQTTPub': lambda x: mqtt_client.publish(
        x['topic'], str(x['msg']), 0),
    'MQTTSub': lambda x: mqtt_client.subscribe(x, 0),
    'MQTTUnsub': lambda x: mqtt_client.unsubscribe(x)
}

_actions = {
    'print': lambda x: print(x),
    'send': lambda x: zero_pub.send_multipart([x['topic'], x['msg']]),
    'pass': lambda x: x
}

# #############################################################################
# ############################# MQTT EVENTS ###################################
# #############################################################################

# ################# Initial setup for the MQTT Client #########################


def _on_connect(_client, _userdata, _rc):
    for _topic_to_sub in SUBSCRIPTIONS:
            mqtt_client.subscribe(UNAME + '/' + _topic_to_sub, 0)

# ################# Behavior when message is received ########################


def _on_message(_client, _userdata, _msg):
    if any(UNAME + '/' + _rest_topic == _msg.topic
           for _rest_topic in REST_TOPICS):

        _send_rest(_msg.topic, _msg.payload)
    else:
        _get_inst = things.check_inst(PORT_NAME + '/' + _msg.topic,
                                      _msg.payload, DB_COLUMN[METAJSONID])
        if _get_inst:
            try:
                _actions[_get_inst[INSTRUCTIONS]['action']](_get_inst[MSG])
            except Exception, _error:
                if "object has no attribute '__getitem__'" not in str(_error):
                    if _get_inst[INSTRUCTIONS]['action'] in str(_error):
                        _error = 'Unknown action ' + str(_error)
                _error_managment(str(_error))
        else:
            print('Thing not found')

# #############################################################################
# ############################## FUNCTINONS ###################################
# #############################################################################

# ################### Send the payload to the REST server #####################


def _send_rest(_topic, _payload):
    try:
        _msg_conv = ast.literal_eval(_payload)
        if not _missing_data[_topic](_msg_conv):
            _reply = _rest_opt[_topic](_msg_conv)
            print ('Status:' + str(_reply.status_code))
            print ('Json:' + str(_reply.json()))

        else:
            print ('Missing Data')
    except Exception, _error:
        _error_managment(str(_error))

# ######################## MQTT Loop and ZeroMQ Listener #####################


def _mqtt_loop():
    while mqtt_client.loop() == 0:
        try:
            [_address, _contents] = zero_sub.recv_multipart()
            print('[%s] %s' % (_address, _contents))
            try:
                _contents = ast.literal_eval(_contents)
            except:
                pass
            _zero_opt[_address](_contents)
        except:
            if _kbhit():
                _command = raw_input('>')
                if _command == 'quit':
                    _exit_program()
    print('MQTT client error, check the constants file for input errors')


# ######################### Obtain keyboard input  ############################


def _kbhit():
    _dr, _dw, _de = select([sys.stdin], [], [], 0)
    return _dr != []

# ########### Disconnect the ZMQ client and terminates the program ############


def _exit_program():
    zero_sub.close()
    zero_pub.close()
    context.term()
    mqtt_client.disconnect()
    sys.exit()

# ############### Start the ZeroMQ Publisher and Subscriber ###################


def _start_zeromq_client():
    try:
        zero_pub.bind('tcp://*:' + PORT_PUB)
        for _port_to_sub in PORTS_SUB:
            zero_sub.connect('tcp://localhost:' + _port_to_sub)
        for _topic_to_sub in TOPICS_SUB:
            zero_sub.setsockopt(zmq.SUBSCRIBE, _topic_to_sub)
        zero_sub.setsockopt(zmq.RCVTIMEO, 1000)
    except Exception, _error:
        _error_managment(str(_error))
        _exit_program()

# ######################## Start the MQTT connection ##########################


def _start_mqtt_client():
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect('0.0.0.0')

# ############################## Error managment ##############################


def _error_managment(_error):
    _error_found = False
    for _error_sample in KNOWN_ERRORS.keys():
        if _error_sample in _error:
            _error_msg[KNOWN_ERRORS[_error_sample]](_error)
            _error_found = True
    if not _error_found:
        _error_msg['undefined'](_error)


# ######################## Start MQTT and ZMQ clients #########################

_start_mqtt_client()
_start_zeromq_client()

if __name__ == '__main__':
    _mqtt_loop()

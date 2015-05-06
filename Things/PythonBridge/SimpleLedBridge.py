import paho.mqtt.client as mqtt
import serial

BROKER_NAME = 'localhost'
SERIAL_PORT = "/dev/ttyACM0"


def _on_connect(_client, _userdata, _msg):

    _client.subscribe('powerled', 0)
    _client.subscribe('link/topic', 0)
    _client.subscribe('link/msg/on', 0)
    _client.subscribe('link/msg/off', 0)
    _client.publish("ucloud/post", str(led_json_model), 0)


def _on_message(_client, _userdata, _msg):
    if _msg.topic == 'powerled':

        if _msg.payload == '1' or '0':
            msg_to_arduino.write(_msg.payload)
            _client.publish("ledstate", _msg.payload, 0)
    elif _msg.topic == 'link/topic':
        _client.subscribe(_msg.payload, 0)
    elif _msg.topic == 'link/msg/on':
        msgs_power_on.append(_msg.payload)
    elif _msg.topic == 'link/msg/off':
        msgs_power_off.append(_msg.payload)
    else:
        if _msg.payload in msgs_power_on:
            msg_to_arduino.write('1')
            _client.publish("ledstate", 1, 0)
        elif _msg.payload in msgs_power_off:
            msg_to_arduino.write('0')
            _client.publish("ledstate", 0, 0)


def _start_mqtt_client():
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(BROKER_NAME)


mqtt_client = mqtt.Client()
msgs_power_on = []
msgs_power_off = []
_start_mqtt_client()
msg_to_arduino = serial.Serial(SERIAL_PORT, 9600)
msg_to_arduino.flushInput()

led_json_model = {
    'mac': 1,
    'json': {'name': 'SimpleLed', 'state': 0, 'power': '',
             'link': {'topic': [],
                      'On': [], 'Off': []}},
    'metajson': {'/name': {'action': 'pass', 'value': 'replace',
                           'validmsg': '', 'validtype': ''},
                 '/power': {'action': 'send', 'value': 'erase',
                            'validmsg': [1, 0], 'validtype': ['int'],
                            'topic': 'powerled', 'type': 'MQTT'},
                 '/link/topic': {'action': 'send', 'value': 'add',
                                 'validmsg': '', 'validtype': '',
                                 'topic': 'link/topic', 'type': 'MQTT'},
                 '/link/On': {'action': 'send', 'value': 'add', 'validmsg': '',
                              'validtype': '', 'topic': 'link/msg/on',
                              'type': 'MQTT'},
                 '/link/Off': {'action': 'send', 'value': 'add',
                               'validmsg': '', 'validtype': '',
                               'topic': 'link/msg/off'},
                 'setup': {'ledstate': {'action': 'subscribe',
                                        'msg': 'ledstate', 'type': 'MQTT'}},
                 'setdown': {'ledstate': {'action': 'unsubscribe',
                                          'msg': 'ledstate', 'type': 'MQTT'}},
                 'show': [{'name': 'name', 'type': 'configuration',
                           'validmsg': 'any', 'validtype': 'str',
                           'dir': 'show',
                           'notes': 'Change the name of the led'},
                          {'name': 'power', 'type': 'MQTT', 'validmsg': [0, 1],
                           'validtype': 'int', 'pattern': 'listener',
                           'dir': 'power',
                           'notes': 'Turn on and off the led'},
                          {'name': 'topic', 'type': 'MQTT', 'validmsg': 'any',
                           'validtype': 'any', 'pattern': 'subscriber',
                           'dir': '/link/topic', 'notes': 'The led ' +
                           'subscribes to the message sent'},
                          {'name': 'On', 'type': 'MQTT', 'validmsg': 'any',
                           'validtype': 'any', 'pattern': 'subscriber',
                           'dir': '/link/On', 'notes': 'Link the message ' +
                           'sent to switch on the led'},
                          {'name': 'Off', 'type': 'MQTT', 'validmsg': 'any',
                           'validtype': 'any', 'pattern': 'subscriber',
                           'dir': '/link/Off', 'notes': 'Link the message ' +
                           'sent to switch off the led'}],
                 'mqtt/ledstate': {'dir': 'state', 'action': 'pass',
                                   'value': 'replace', 'validmsg': [0, 1],
                                   'validtype': 'int'}}
}

while mqtt_client.loop() == 0:
    pass

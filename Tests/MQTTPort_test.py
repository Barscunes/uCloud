import sys
import mock
import requests_mock
sys.path.append('../Ports')
import MQTTPort
sys.path.append('../Classes')
import constants

# #############################################################################
# ################### Constants and variables definitions #####################
# ############################################################################

GENERAL = constants.retrieve('General.txt')
PORT = constants.retrieve('MQTTPort.txt')
UNAME = GENERAL['UNAME']

# #############################################################################
# ################################ CLASSES ####################################
# #############################################################################

# Class used as a mqtt template for the tests


class _MqttTemplate:
    client = 'client'
    userdata = 'data'
    rc = 'rc'

    class post:
        topic = 'ucloud/post'
        payload = ("{'mac': 88, 'json': {'name': ''}," +
                   "'metajson': {'/name': ''}}")

    class incomplete_post:
        topic = 'ucloud/post'
        payload = "{'mac': 88}"

    class delete:
        topic = 'ucloud/delete'
        payload = "{'mac': 88}"

    class wrong_value:
        topic = 'ucloud/post'
        payload = "wrong value"

    class check_inst:
        topic = 'check'
        payload = 'inst'

# Captures the data sent to the function to be mocked


class _Capture:

    def __init__(self):
        self.captured_values = ()

    def __call__(self, *new_values):
        self.captured_values = self.captured_values + new_values

    def values(self):
        return self.captured_values

# Callable class that end the mqtt loop after a given number of iterations


class _mqtt_loop:

    def __init__(self, limit):
        self.limit = limit
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls > self.limit:
            return 1
        else:
            return 0

# #############################################################################
# ############################## TEST FUNCTIONS ###############################
# #############################################################################

# Creates a new Capture object to be used in the next test

subscribe = _Capture()

# Test that the mqtt _on_connect function subscribes to the defined topics


@mock.patch('MQTTPort.mqtt_client.subscribe',
            side_effect=subscribe)
def test_on_connect(mock_sub):

    MQTTPort._on_connect(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.rc)

    assert all(_subscription_targets in str(subscribe.values())
               for _subscription_targets in PORT['SUBSCRIPTIONS'])

# MQTT subscription error


def test_mqtt_topic_error(capsys):

    MQTTPort.mqtt_client.subscribe('##', 0)
    MQTTPort._mqtt_loop()
    _out, _err = capsys.readouterr()

    assert 'MQTT client error, check the constants' in _out

# #### Creates new Capture objects to be used in the next test #######

sub_connect = _Capture()
sub_setsockopt = _Capture()
pub_bind = _Capture()


# Test that the ZMQ client connects and subscribes to the defined
# values

@mock.patch('MQTTPort.zero_sub.connect', side_effect=sub_connect)
@mock.patch('MQTTPort.zero_sub.setsockopt',
            side_effect=sub_setsockopt)
@mock.patch('MQTTPort.zero_pub.bind', side_effect=pub_bind)
def test_start_zeromq_client(zero_sub_con, zero_sub_set, zero_pub):

    MQTTPort._start_zeromq_client()

    assert (PORT['PORT_PUB'] in str(pub_bind.values()) and
            all(_ports_sub in str(sub_connect.values()) for _ports_sub
                in PORT['PORT_SUB']) and
            all(_topics_sub in str(sub_setsockopt.values())
                for _topics_sub in PORT['TOPIC_SUB']))

# ############### Test the ZMQ client with wrong input ###############


@mock.patch('MQTTPort._exit_program', return_value='')
def test_start_zeromq_client_pub_error(_exit_program, capsys):

    MQTTPort.PORT_PUB = ''
    MQTTPort._start_zeromq_client()
    _out, _err = capsys.readouterr()

    assert "Can't start zmq client" in _out

# Test the requests.post method trigger by the reception of a MQTT
# message with 'post' topic


@requests_mock.mock()
def test_post(post_uri):

    post_uri.post('http://localhost:8000/' + UNAME + '/thing',
                  text='data')
    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.post())
    _reply = post_uri.request_history

    assert '"mac": 88' in _reply[0].text


# Test the event for a incomplete MQTT message with 'post' topic

def test_incomplete_post(capsys):

    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.incomplete_post())
    _out, _err = capsys.readouterr()

    assert 'Missing Data' in _out


# Test the event for a wrong MQTT message with 'post' topic

def test_wrong_post(capsys):

    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.wrong_value())
    _out, _err = capsys.readouterr()

    assert 'Invalid payload' in _out


# Test the requests.delete method trigger by the reception of a MQTT
# message with 'delete' topic

@requests_mock.mock()
def test_delete(delete_uri):

    delete_uri.delete('http://localhost:8000/' + UNAME + '/thing',
                      text='data')
    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.delete())
    _reply = delete_uri.request_history

    assert '"mac": 88' in _reply[0].text


# Test the event for a nonexistent thing on the data base

def test_check(capsys):

    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.check_inst())
    _out, _err = capsys.readouterr()

    assert 'Thing not found' in _out

# Test the event of a publisher thing on the data base


@mock.patch('MQTTPort.things.check_inst',
            return_value=({'action': 'print'},
                          'Test action'))
def test_action(things_check_inst, capsys):

    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.check_inst())
    _out, _err = capsys.readouterr()

    assert 'Test action' in _out

# Test the event of an incomplete message of the publisher thing


@mock.patch('MQTTPort.things.check_inst',
            return_value=({'action': 'send'},
                          'Test incomplete action'))
def test_action_incomplete(things_check_inst, capsys):

    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.check_inst())
    _out, _err = capsys.readouterr()

    assert 'Incomplete instruction' in _out


# Test the event of an undefined action sent by the publisher thing


@mock.patch('MQTTPort.things.check_inst',
            return_value=(True,
                          'Test no instruction'))
def test_action_no_instruction(things_check_inst, capsys):

    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.check_inst())
    _out, _err = capsys.readouterr()

    assert "The message wasn't an Instruction" in _out

# Test the event of an undefined action sent by the publisher thing


@mock.patch('MQTTPort.things.check_inst',
            return_value=({'action': 'unknown'},
                          'Test unknown action'))
def test_action_undefined(things_check_inst, capsys):

    MQTTPort._on_message(_MqttTemplate.client, _MqttTemplate.userdata,
                         _MqttTemplate.check_inst())
    _out, _err = capsys.readouterr()

    assert "Unknown action 'unknown'" in _out

publish = _Capture()


# Acces the MQTT loop once and collect the message from a mocked
# function

@mock.patch('MQTTPort.mqtt_client.loop', side_effect=_mqtt_loop(1))
@mock.patch('MQTTPort._kbhit', return_value=False)
@mock.patch('MQTTPort.zero_sub.recv_multipart',
            return_value=('MQTTPub',
                          "{'topic':'test', 'msg':'loop'}"))
@mock.patch('MQTTPort.mqtt_client.publish', side_effect=publish)
def test_mqtt_loop(conditional, _kbhit, zero_recv, mqtt_recv):
    MQTTPort._mqtt_loop()
    assert 'loop' in publish.values() and 'test' in publish.values()

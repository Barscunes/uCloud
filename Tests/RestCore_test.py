import pytest
import sys
import json
import random
import zmq
sys.path.append('../Core')
import RestCore

UNAME = 'ucloud'
JSONID = 'json'
METAJSONID = 'metajson'
IDENTIFIER = 'mac'
HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}
COLUMNS = [{'msg': {JSONID: {'name': ''}, METAJSONID: {'/name': ''}},
            'reply': 'mac'},
           {'msg': {IDENTIFIER: 0, METAJSONID: {'/name': ''}},
            'reply': 'json'},
           {'msg': {IDENTIFIER: 0, JSONID: {'name': ''}},
            'reply': 'metajson'},
           {'msg': {IDENTIFIER: 0, JSONID: {}, METAJSONID: {}},
            'reply': 'name'}]

_zero_sub = None
_contex = None


@pytest.fixture
def client(request):
    RestCore.app.config['TESTING'] = True
    client = RestCore.app.test_client()
    return client

# ############# MODIFICAR PARA HACERLO MAS FLEXIBLE #############
# ################################################################


def _start_zeromq_client():
    global _zero_sub, _context
    _context = zmq.Context()

    _zero_sub = _context.socket(zmq.SUB)
    _zero_sub.connect("tcp://localhost:5561")


def _port_subscriptions(port):
    global _zero_sub
    _zero_sub.setsockopt(zmq.SUBSCRIBE, port + "Pub")
    _zero_sub.setsockopt(zmq.SUBSCRIBE, port + "Sub")
    _zero_sub.setsockopt(zmq.SUBSCRIBE, port + "Unsub")
    _zero_sub.setsockopt(zmq.RCVTIMEO, 1000)


# ############### Test get_things with out any thing ####################


def test_get_things_json(client):
    response = client.get('/' + UNAME + '/' + JSONID + '/things')
    assert response.status_code == 200


# ############### Test add_thing function ####################


def test_add_thing_wo_request(client):
    response = client.post('/' + UNAME + '/thing')
    assert 'Bad request' in response.data


def test_add_thing_bad_request(client):
    _column = random.randint(0, len(COLUMNS) - 1)
    data = json.dumps(COLUMNS[_column]['msg'])
    response = client.post('/' + UNAME + '/thing',
                           data=data, headers=HEADERS)
    assert COLUMNS[_column]['reply'] in response.data


def test_add_minimal_thing(client):
    data = json.dumps({'mac': 88, 'json': {'name': ''},
                       'metajson': {'/name': ''}})
    response = client.post('/' + UNAME + '/thing',
                           data=data, headers=HEADERS)
    assert 'New' in response.data


def test_add_duplicated_thing(client):
    data = json.dumps({'mac': 88, 'json': {'name': ''},
                       'metajson': {'/name': ''}})
    response = client.post('/' + UNAME + '/thing',
                           data=data, headers=HEADERS)
    assert 'thing already exist' in response.data


def test_add_bad_type(client):
    data = json.dumps({'mac': 45, 'json': '', 'metajson': ''})

    response = client.post('/' + UNAME + '/thing',
                           data=data, headers=HEADERS)

    assert (IDENTIFIER + ' must be a integer, ' + JSONID + ' and ' +
            METAJSONID + ' must be dictionaries' in response.data)

# ########### Test get metajson and identifier with one thing ############


def test_get_things_metajson(client):
    response = client.get('/' + UNAME + '/' + METAJSONID + '/things')
    assert response.status_code == 200


def test_get_things_identifier(client):
    response = client.get('/' + UNAME + '/' + IDENTIFIER + '/things')
    assert response.status_code == 200


def test_get_things_bad_request(client):
    response = client.get('/' + UNAME + '/' + str(random.random()) + '/things')
    assert 'Bad request' in response.data

# ################### Test find_thing function  ###################


def test_find_things_with_out_filter(client):
    response = client.get('/' + UNAME + '/find/things')
    assert 'found' in response.data


def test_find_things_with_subscriber_filter(client):
    data_thing = json.dumps({'mac': 89, 'json': {'name': ''},
                             'metajson': {
                                 '/name': '',
                                 'show': [
                                     {'name': 'pub', 'type': 'MQTT',
                                      'pattern': 'publisher'},
                                     {'name': 'sub', 'type': 'MQTT',
                                      'pattern': 'subscriber'}]}})
    data_find = json.dumps({'pattern': 'subscriber'})
    add_new_thing = client.post('/' + UNAME + '/thing',
                                data=data_thing, headers=HEADERS)

    response = client.get('/' + UNAME + '/find/things',
                          data=data_find, headers=HEADERS)
    assert 'subscriber' in response.data and 'New' in add_new_thing.data


def test_find_things_not_found(client):
    data_show = json.dumps({'not': 'found'})
    data_type = json.dumps('BT')
    response_show = client.get('/' + UNAME + '/find/things',
                               data=data_show, headers=HEADERS)
    response_type = client.get('/' + UNAME + '/find/' + data_type + '/things')
    assert ('Not found' in response_show.data and
            'Not found' in response_type.data)


def test_find_things_bad_request(client):
    data = 'BAD REQUEST'
    response = client.get('/' + UNAME + '/find/things',
                          data=data, headers=HEADERS)
    assert 'Bad request' in response.data

# ############### Test modify_thing function ################


def test_modify_thing(client):
    data_thing = json.dumps({'mac': 90, 'json': {'name': '', 'power': ''},
                             'metajson': {
                                 '/name': {'action': 'pass',
                                           'value': 'replace',
                                           'validmsg': '', 'validtype': ''},
                                 '/power': {'action': 'pass',
                                            'value': 'replace',
                                            'validmsg': '', 'validtype': ''},
                                 'show': [
                                     {'name': 'sub', 'type': 'MQTT',
                                      'pattern': 'subscriber'}]}})
    data_modify = json.dumps({'mac': 90, 'json': {'name': ''}})
    add_new_thing = client.post('/' + UNAME + '/thing',
                                data=data_thing, headers=HEADERS)

    response = client.put('/' + UNAME + '/thing',
                          data=data_modify, headers=HEADERS)

    assert 'Modified' in response.data and 'New' in add_new_thing.data


def test_modify_two_values(client):
    data = json.dumps({'mac': 90, 'json': {'name': 'bob',
                                           'power': 'powerOn'}})

    response = client.put('/' + UNAME + '/thing',
                          data=data, headers=HEADERS)
    response_get = client.get('/' + UNAME + '/' + JSONID + '/things')

    assert 'Modified' in response.data and 'powerOn' in response_get.data


def test_modify_repeat_value(client):

    data = json.dumps({'mac': 90, 'json': {'name': 'bob'}})

    response = client.put('/' + UNAME + '/thing',
                          data=data, headers=HEADERS)

    assert 'already have that value' in response.data


def test_modify_repeat_w_two_values(client):
    data = json.dumps({'mac': 90, 'json': {'name': 'bob',
                                           'power': 'powerOff'}})

    response = client.put('/' + UNAME + '/thing',
                          data=data, headers=HEADERS)
    response_get = client.get('/' + UNAME + '/' + JSONID + '/things')

    assert 'Modified' in response.data and 'powerOff' in response_get.data


def test_modify_repeat_two_values(client):
    data = json.dumps({'mac': 90, 'json': {'name': 'bob',
                                           'power': 'powerOff'}})

    response = client.put('/' + UNAME + '/thing',
                          data=data, headers=HEADERS)

    assert 'already have that value' in response.data


def test_modify_not_existing_value(client):

    data = json.dumps({'mac': 90, 'json': {'invalidir': ''}})

    response = client.put('/' + UNAME + '/thing',
                          data=data, headers=HEADERS)

    assert 'can\'t be modified or doesn\'t have' in response.data

# ############### Test find with filter #########################


def test_find_thing_only_publisher(client):
    data = json.dumps({'pattern': 'publisher', 'type': 'MQTT'})
    response = client.get('/' + UNAME + '/find/things',
                          data=data, headers=HEADERS)
    assert 'publisher' in response.data and 'subscriber' not in response.data

# ######################## Test actions ##############################


def test_actions(capsys, client):
    RestCore._start_zeromq_pub()
    _start_zeromq_client()
    _port_subscriptions("MQTT")
    _zero_sub.setsockopt(zmq.SUBSCRIBE, 'MQTTPub')
    data_thing = json.dumps({'mac': 91, 'json': {'name': '',
                                                 'print': '',
                                                 'send': '',
                                                 'pass': ''},
                             'metajson': {
                                 '/print': {'action': 'print',
                                            'value': 'replace',
                                            'validmsg': '', 'validtype': ''},
                                 '/send': {'action': 'send',
                                           'value': 'replace',
                                           'validmsg': '', 'validtype': '',
                                           'topic': 'powerlamp',
                                           'type': 'MQTT'},
                                 '/pass': {'action': 'pass',
                                           'value': 'replace',
                                           'validmsg': '', 'validtype': ''}}})

    data_modify = json.dumps({'mac': 91, 'json': {'print': 'print action',
                                                  'send': 'send action',
                                                  'pass': 'pass action'}})

    add_new_thing = client.post('/' + UNAME + '/thing',
                                data=data_thing, headers=HEADERS)

    response = client.put('/' + UNAME + '/thing',
                          data=data_modify, headers=HEADERS)
    try:
        [_address, _contents] = _zero_sub.recv_multipart()
    except Exception, e:
        print("ERROR:!!!!!"+str(e))
        _contents = 'Time expired'
    get_mod_things = client.get('/' + UNAME + '/' + JSONID + '/things')
    out, err = capsys.readouterr()

    assert ('Modified' in response.data and 'New' in add_new_thing.data and
            'print action' in out and 'pass action' in get_mod_things.data and
            u'send action' in _contents)


def test_error_action(client):

    data_thing = json.dumps({'mac': 92, 'json': {'name': '',
                                                 'send': ''},
                             'metajson': {
                                 '/send': {'action': 'send',
                                           'value': 'replace',
                                           'validmsg': '', 'validtype': ''}}})

    data_modify = json.dumps({'mac': 92, 'json': {'send': 'send action'}})

    add_new_thing = client.post('/' + UNAME + '/thing',
                                data=data_thing, headers=HEADERS)

    response = client.put('/' + UNAME + '/thing',
                          data=data_modify, headers=HEADERS)

    assert ('\'Thing\' can\'t perform that action' in response.data and
            'New' in add_new_thing.data)

# ############### Test delete_thing function ####################


def test_delete_thing(client):
    data = (json.dumps({'mac': 88}), json.dumps({'mac': 89}),
            json.dumps({'mac': 90}), json.dumps({'mac': 91}),
            json.dumps({'mac': 92}))
    _deleted_things = 0

    for _thing in range(len(data)):
        response = client.delete('/' + UNAME + '/thing',
                                 data=data[_thing],
                                 headers=HEADERS)
        if 'Deleted' in response.data:
            _deleted_things += 1

    assert (_deleted_things is len(data))


def test_delete_not_existing_thing(client):
    data = (json.dumps({'mac': 88}))
    response = client.delete('/' + UNAME + '/thing', data=data,
                             headers=HEADERS)

    assert ('Not found' in response.data)

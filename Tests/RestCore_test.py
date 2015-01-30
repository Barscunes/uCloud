import pytest
import sys
import json
import random
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
           {'msg': {IDENTIFIER: 0, JSONID: {'name': ''}}, 'reply': 'metajson'}]


@pytest.fixture
def client(request):
    RestCore.app.config['TESTING'] = True
    client = RestCore.app.test_client()
    return client

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


def test_add_minimal_thing_(client):
    data = json.dumps({'mac': 88, 'json': {'name': ''},
                       'metajson': {'/name': ''}})
    response = client.post('/' + UNAME + '/thing',
                           data=data, headers=HEADERS)
    assert 'New' in response.data

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
    response = client.get('/' + UNAME + '/find/MQTT/things')
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

    response = client.get('/' + UNAME + '/find/MQTT/things',
                          data=data_find, headers=HEADERS)
    assert 'subscriber' in response.data and 'New' in add_new_thing.data


def test_find_things_not_found(client):
    data_show = json.dumps({'not': 'found'})
    data_type = json.dumps('BT')
    response_show = client.get('/' + UNAME + '/find/MQTT/things',
                               data=data_show, headers=HEADERS)
    response_type = client.get('/' + UNAME + '/find/' + data_type + '/things')
    assert ('Not found' in response_show.data and
            'Not found' in response_type.data)


def test_find_things_bad_request(client):
    data = 'BAD REQUEST'
    response = client.get('/' + UNAME + '/find/MQTT/things',
                          data=data, headers=HEADERS)
    assert 'Bad request' in response.data

# ############### Test modify_thing function ################


def test_modify_thing(client):
    data_thing = json.dumps({'mac': 90, 'json': {'name': ''},
                             'metajson': {
                                 '/name': {'action': 'pass',
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

# ############### Test find with filter #########################


def test_find_thing_only_publisher(client):
    data = json.dumps({'pattern': 'publisher'})
    response = client.get('/' + UNAME + '/find/MQTT/things',
                          data=data, headers=HEADERS)
    assert 'publisher' in response.data and 'subscriber' not in response.data

# ############### Test delete_thing function ####################


def test_delete_thing(client):
    data = (json.dumps({'mac': 88}), json.dumps({'mac': 89}),
            json.dumps({'mac': 90}))
    response88 = client.delete('/' + UNAME + '/thing', data=data[0],
                               headers=HEADERS)
    response89 = client.delete('/' + UNAME + '/thing', data=data[1],
                               headers=HEADERS)
    response90 = client.delete('/' + UNAME + '/thing', data=data[2],
                               headers=HEADERS)
    assert ('Deleted' in response88.data and 'Deleted' in response89.data and
            'Deleted' in response90.data)

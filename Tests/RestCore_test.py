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
COLUMNS = [{JSONID: '', METAJSONID: ''}, {IDENTIFIER: 0, METAJSONID: ''},
           {IDENTIFIER: 0, JSONID: ''},
           {IDENTIFIER: 0, JSONID: '', METAJSONID: ''}]


@pytest.fixture
def client(request):
    RestCore.app.config['TESTING'] = True
    client = RestCore.app.test_client()
    return client

# ############### Test get_things function ####################


def test_get_things_json(client):
    response = client.get('/' + UNAME + '/' + JSONID + '/things')
    assert response.status_code == 200


def test_get_things_metajson(client):
    response = client.get('/' + UNAME + '/' + METAJSONID + '/things')
    assert response.status_code == 200


def test_get_things_identifier(client):
    response = client.get('/' + UNAME + '/' + IDENTIFIER + '/things')
    assert response.status_code == 200


def test_get_things_bad_request(client):
    response = client.get('/' + UNAME + '/' + str(random.random()) + '/things')
    assert 'Bad request' in response.data

# ############### Test find_things function ####################


def test_find_things_with_out_filter(client):
    response = client.get('/' + UNAME + '/find/MQTT/things')
    assert 'found' in response.data


def test_find_things_with_publisher_filter(client):
    data = json.dumps({'pattern': 'publisher'})
    response = client.get('/' + UNAME + '/find/MQTT/things',
                          data=data, headers=HEADERS)
    assert 'publisher' in response.data and 'subscriber' not in response.data


def test_find_things_with_subscriber_filter(client):
    data = json.dumps({'pattern': 'subscriber'})
    response = client.get('/' + UNAME + '/find/MQTT/things',
                          data=data, headers=HEADERS)
    assert 'subscriber' in response.data and 'publisher' not in response.data


def test_find_things_not_found(client):
    data = json.dumps({'not': 'found'})
    response = client.get('/' + UNAME + '/find/MQTT/things',
                          data=data, headers=HEADERS)
    assert 'Not Found' in response.data


def test_find_things_bad_request(client):
    data = 'BAD REQUEST'
    response = client.get('/' + UNAME + '/find/MQTT/things',
                          data=data, headers=HEADERS)
    assert 'Bad request' in response.data

# ############### Test add_thing function ####################


# def test_add_thing_wo_request(client):
#     response = client.post('/' + UNAME + '/thing')
#     assert 'Bad request' in response.data


# def test_add_thing_bad_request(client):
#     data = json.dumps(COLUMNS[random.randint(0, len(COLUMNS) - 1)])
#     response = client.post('/' + UNAME + '/thing',
#                            data=data, headers=HEADERS)
#     assert 'Bad request' in response.data


def test_add_thing_minim(client):
    data = json.dumps({'mac': 88, 'json': {'name': ''},
                       'metajson': {'/name': ''}})
    response = client.post('/' + UNAME + '/thing',
                           data=data, headers=HEADERS)
    assert 'New' in response.data


def test_get_things_json_af(client):
    response = client.get('/' + UNAME + '/' + JSONID + '/things')
    assert response.status_code == 200


def test_get_things_metajson_af(client):
    response = client.get('/' + UNAME + '/' + METAJSONID + '/things')
    assert response.status_code == 200

# ############### Test delete_thing function ####################


def test_delete_thing(client):
    data = json.dumps({'mac': 88})
    response = client.delete('/' + UNAME + '/thing', data=data,
                             headers=HEADERS)
    assert 'Deleted' in response.data

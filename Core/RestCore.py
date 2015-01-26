#!flask/bin/python
from __future__ import print_function
from flask import Flask, jsonify, abort, make_response, request
import zmq
import threading
import sys
import os
from select import select
import ast
sys.path.append('../Classes')
from things import Things

# ############################################################
# ######################## FUNCTIONS #########################
# ############################################################

# ##################### Start 0MQ publisher ##################################


def _start_zeromq_pub():
    global _zero_pub
    _context = zmq.Context()
    _zero_pub = _context.socket(zmq.PUB)
    _zero_pub.bind("tcp://*:5561")
    print("Conectado")

# ############# Initial set up for the new things #############################


def _initial_set(_instructions, _set):
    print(_instructions)
    for x in _instructions:
        _set[str(_instructions[x]['action'])](
            str(_instructions[x]['msg']), str(_instructions[x]['type']))

# ##### Gets the Keyboard Input, used in communication with the thread ########


def _kbhit():
    _dr, _dw, _de = select([sys.stdin], [], [], 0)
    return _dr != []

# ############### Initialize subscriber thread ###############################


def _start_zeromq_sub():

    _zeromq_thread = threading.Thread(target=_zeromq_sub_thread)
    _zeromq_thread.start()

# ################# Initialize 0MQ subscriber #################################


def _zeromq_sub_thread():
    _context = zmq.Context()
    _zero_sub = _context.socket(zmq.SUB)
    _zero_sub.connect('tcp://localhost:5560')
    _zero_sub.setsockopt(zmq.SUBSCRIBE, 'REST')
    _zero_sub.setsockopt(zmq.RCVTIMEO, 1000)
    print ('Thread Start')
    _exit = False
    while _exit is False:
        try:
            [_address, _contents] = _zero_sub.recv_multipart()
            print('[%s] %s' % (_address, _contents))
        except:
            if _kbhit():
                _msg = raw_input('>')
                if _msg == 'salir':
                    _zero_sub.close()
                    _context.term()
                    _exit = True
    print('Thread Stop')
    os._exit(1)

# ################### Check if any field is missing ########################


def _missing_data(_req_json, _msg_exception):

    if IDENTIFIER not in _req_json and _msg_exception != IDENTIFIER:
        _msg = '400' + IDENTIFIER
    elif JSONID not in _req_json and _msg_exception != JSONID:
        _msg = '400' + JSONID
    elif METAJSONID not in _req_json and _msg_exception != METAJSONID:
        _msg = '400' + METAJSONID
    else:
        _msg = None

    return _msg

# #################### Execute the Action things #######################


def _do_actions(_instructions):
    try:
        _instructions = ast.literal_eval(_instructions)
    except:
        pass
    x = 0
    while len(_instructions) > x:
        try:
            _actions[_instructions[x]['action']](_instructions[x + 1],
                                                 _instructions[x])
        except Exception, e:
            print(e)
        x += 2

# ############################################################
# ####################### MAIN ###############################
# ############################################################

app = Flask(__name__)
_things = Things()
UNAME = 'ucloud'
IDENTIFIER = 'mac'
JSONID = 'json'
METAJSONID = 'metajson'
SETUPID = 'setup'
SETDOWNID = 'setdown'
_zero_pub = None

_actions = {
    'print': lambda x, y: print(x),
    'send': lambda x, y: _zero_pub.send_multipart([str(y['type']) + 'Pub',
                                                   str({'topic': y['topic'],
                                                        'msg': x})]),
    'pass': lambda x, y: x
}
_error_msg = {
    'duplicate': 'That thing already exist',
    '400ReqJson': 'No Json',
    '400' + IDENTIFIER: IDENTIFIER + ' missing',
    '400' + JSONID: JSONID + ' missing',
    '400' + METAJSONID: METAJSONID + ' missing',
    'name': 'Name missing',
    'badtype': IDENTIFIER + ' must be a integer, ' + JSONID + ' and ' +
                            METAJSONID + ' must be dictionaries'
}
_setup_inst = {
    'subscribe': lambda x, y: _zero_pub.send_multipart([y + 'Sub', x]),
    'publish': lambda x, y: _zero_pub.send_multipart([y + 'Pub', x])
}
_setdown_inst = {
    'unsubscribe': lambda x, y: _zero_pub.send_multipart([y + 'Unsub', x]),
    'publish': lambda x, y: _zero_pub.send_multipart([y + 'Pub', x])
}
_error_key = None
_start_zeromq_pub()
# _start_zeromq_sub()

# ############################################################
# ################## ERROR HANDLERS ##########################
# ############################################################


@app.errorhandler(400)
def bad_request(error):
    global _error_key
    if _error_key is None:
        return make_response(jsonify({'error': 'Bad request'}), 400)
    else:
        _tmp_error_key = _error_key
        _error_key = None
        return make_response(jsonify({'error': 'Bad request',
                                      'Cause': _error_msg[_tmp_error_key]}),
                             400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(409)
def conflict(error):
    global _error_key
    _tmp_error_key = _error_key
    _error_key = None
    return make_response(jsonify({'error': 'Conflict',
                                  'Cause': _error_msg[_tmp_error_key]}), 409)

# ############################################################
# ################## REST METHODS ############################
# ############################################################

# ##### Get the JSON of all your connected things ############


@app.route('/' + UNAME + '/<string:_key>/things', methods=['GET'])
def get_things(_key):
    if _key == IDENTIFIER or _key == JSONID or _key == METAJSONID:
        return jsonify({'Things': _things.retrieve_all_col(str(_key))})
    else:
        abort(400)

# #################### Find specific things #####################


@app.route('/' + UNAME + '/find/<string:_type>/things', methods=['GET'])
def find_things(_type):
    if request.json:
        print(request.json)
        _reply = _things.find(_type, request.json)
    else:
        _reply = _things.find(_type)
    return jsonify({'Things': _reply})

# ################## Add new thing ###########################


@app.route('/' + UNAME + '/thing', methods=['POST'])
def add_thing():
    global _error_key

    if not request.json:
        _error_key = '400ReqJson'
    else:
        _error_key = _missing_data(request.json, '')

    if _error_key is not None:
        abort(400)

    _reply = _things.add(request.json)
    if not _reply[0]:
        _error_key = _reply[1]
        abort(_reply[2])

    if SETUPID in request.json[METAJSONID]:
        _initial_set(request.json[METAJSONID][SETUPID], _setup_inst)

    return jsonify({'Thing': 'New'}), 201


# ################## Modify Thing #############################


@app.route('/' + UNAME + '/thing', methods=['PUT'])
def update_task():
    global _error_key

    if not request.json:
        _error_key = '400ReqJson'
    else:
        _error_key = _missing_data(request.json, METAJSONID)

    if _error_key is not None:
        abort(400)
    _reply = _things.modify(request.json)
    if not _reply[0]:
        _error_key = _reply[1]
        abort(_reply[2])
    _do_actions(_reply)
    return jsonify({'Thing': 'Modified'}), 202

# ################## Delete Thing #############################


@app.route('/' + UNAME + '/thing', methods=['DELETE'])
def delete_thing():
    global _error_key

    if not request.json:
        _error_key = '400ReqJson'
    elif IDENTIFIER not in request.json:
        _error_key = '400' + IDENTIFIER

    if _error_key is not None:
        abort(400)
    _reply = _things.delete(request.json)
    if not _reply[0]:
        _error_key = _reply[1]
        abort(_reply[2])
    _reply = ast.literal_eval(_reply)
    if SETDOWNID in _reply:
        _initial_set(_reply[SETDOWNID], _setdown_inst)
    return jsonify({'Thing': 'Deleted'}), 201


# ############################################################
# ################ START THE SERVER ##########################
# ############################################################

if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=False)

#!flask/bin/python
from __future__ import print_function
from flask import Flask, jsonify, abort, make_response, request
import zmq
import threading
import sys
import os
from select import select
sys.path.append('../Classes')
import things
import constants

# #############################################################################
# ################################## MAIN #####################################
# #############################################################################

# ###################### Constants and variables assignment ###################
app = Flask(__name__)
GENERAL = constants.retrieve('General.txt')
CORE = constants.retrieve('RestCore.txt')
UNAME = GENERAL['UNAME']
IDENTIFIER = GENERAL['IDENTIFIER']
JSONID = GENERAL['JSONID']
METAJSONID = GENERAL['METAJSONID']
SETUPID = GENERAL['SETUPID']
SETDOWNID = GENERAL['SETDOWNID']
PORT_PUB = CORE['PORT_PUB']
context = zmq.Context()
zero_pub = context.socket(zmq.PUB)
error_key = None

# ######################### Dictionary switches ###############################
_actions = {
    'print': lambda x, y: print(x),
    'send': lambda x, y: zero_pub.send_multipart([str(y['type']) + 'Pub',
                                                  str({'topic': y['topic'],
                                                       'msg': x})]),
    'pass': lambda x, y: x
}
_error_msg = {
    'missing': 'Missing information',
    'modifyRepeat': 'Thing already have that value',
    'notDir': 'Thing value can\'t be modified or doesn\'t have that atrribute',
    'duplicate': 'That thing already exist',
    'instruction': 'The \'Thing\' can\'t perform that action ',
    '400ReqJson': 'No Json',
    '400' + IDENTIFIER: IDENTIFIER + ' missing',
    '400' + JSONID: JSONID + ' missing',
    '400' + METAJSONID: METAJSONID + ' missing',
    'name': 'name missing',
    'badtype': IDENTIFIER + ' must be a integer, ' + JSONID + ' and ' +
                            METAJSONID + ' must be dictionaries'
}
_setup_inst = {
    'subscribe': lambda x, y: zero_pub.send_multipart([y + 'Sub', x]),
    'publish': lambda x, y: zero_pub.send_multipart([y + 'Pub', x])
}
_setdown_inst = {
    'unsubscribe': lambda x, y: zero_pub.send_multipart([y + 'Unsub', x]),
    'publish': lambda x, y: zero_pub.send_multipart([y + 'Pub', x])
}

# #############################################################################
# ################################ FUNCTIONS ##################################
# #############################################################################

# Start 0MQ publisher


def _start_zeromq_pub():
    zero_pub.bind('tcp://*:' + PORT_PUB)
    print("Conectado")

# Initial set up for the new things


def _initial_set(_instructions, _set):
    global error_key
    try:
        for _task in _instructions:
            _set[str(_instructions[_task]['action'])](
                str(_instructions[_task]['msg']),
                str(_instructions[_task]['type']))
    except:
        error_key = 'Missing information'
        abort(400)

# Gets the Keyboard Input, used in communication with the thread


def _kbhit():
    _dr, _dw, _de = select([sys.stdin], [], [], 0)
    return _dr != []

# Initialize subscriber thread


def _start_zeromq_sub():

    _zeromq_thread = threading.Thread(target=_zeromq_sub_thread)
    _zeromq_thread.start()

# Initialize 0MQ subscribe


def _zeromq_sub_thread():
    _zero_sub = context.socket(zmq.SUB)
    _zero_sub.connect('tcp://localhost:5560')
    _zero_sub.setsockopt(zmq.SUBSCRIBE, 'REST')
    _zero_sub.setsockopt(zmq.RCVTIMEO, 1000)
    print ('Thread Start')
    _exit = False
    while _exit is False:
        try:
            [_address, _contents] = _zero_sub.recv_multipart()
        except:
            if _kbhit():
                _msg = raw_input('>')
                if _msg == 'salir':
                    _zero_sub.close()
                    context.term()
                    _exit = True
    print('Thread Stop')
    os._exit(1)

# Execute the Action thing


def _do_actions(_instructions):

    global error_key
    x = 0
    while len(_instructions) > x:
        try:
            _actions[_instructions[x]['action']](_instructions[x + 1],
                                                 _instructions[x])
        except:
            error_key = 'instruction'
            abort(400)
        x += 2

# #############################################################################
# ########################## ERROR HANDLERS ###################################
# #############################################################################


@app.errorhandler(400)
def bad_request(error):
    global error_key
    if error_key is None:
        return make_response(jsonify({'error': 'Bad request'}), 400)
    else:
        _tmp_error_key = error_key
        error_key = None
        return make_response(jsonify({'error': 'Bad request',
                                      'Cause': _error_msg[_tmp_error_key]}),
                             400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(409)
def conflict(error):
    global error_key
    _tmp_error_key = error_key
    error_key = None
    return make_response(jsonify({'error': 'Conflict',
                                  'Cause': _error_msg[_tmp_error_key]}), 409)

# ############################################################
# ################## REST METHODS ############################
# ############################################################

# Get the JSON of all your connected things


@app.route('/' + UNAME + '/<string:_key>/things', methods=['GET'])
def get_things(_key):
    if _key == IDENTIFIER or _key == JSONID or _key == METAJSONID:
        return jsonify({'Things': things.retrieve_all_col(str(_key))})
    else:
        abort(400)

# #################### Find specific things #####################


@app.route('/' + UNAME + '/find/things', methods=['GET'])
def find_things():
    return jsonify({'Things': things.find(request.json)})

# ################## Add new thing ###########################


@app.route('/' + UNAME + '/thing', methods=['POST'])
def add_thing():
    global error_key

    if not request.json:
        error_key = '400ReqJson'
    else:
        error_key = things.missing_data(request.json, '')

    if error_key is not None:
        abort(400)

    _reply = things.add(request.json)
    if _reply['error']:
        error_key = _reply['cause']
        abort(_reply['code'])

    if SETUPID in request.json[METAJSONID]:
        _initial_set(request.json[METAJSONID][SETUPID], _setup_inst)

    return jsonify({'Thing': 'New'}), 201


# ################## Modify Thing #############################


@app.route('/' + UNAME + '/thing', methods=['PUT'])
def update_task():
    global error_key

    if not request.json:
        error_key = '400ReqJson'
    else:
        error_key = things.missing_data(request.json, METAJSONID)

    if error_key is not None:
        abort(400)
    _reply = things.modify(request.json)
    if _reply['error']:
        error_key = _reply['cause']
        abort(_reply['code'])
    _do_actions(_reply)
    return jsonify({'Thing': 'Modified'}), 202

# ################## Delete Thing #############################


@app.route('/' + UNAME + '/thing', methods=['DELETE'])
def delete_thing():
    global error_key

    if not request.json:
        error_key = '400ReqJson'
    elif IDENTIFIER not in request.json:
        error_key = '400' + IDENTIFIER

    if error_key is not None:
        abort(400)
    _reply = things.delete(request.json)
    if _reply['error']:
        error_key = _reply['cause']
        abort(_reply['code'])
    if SETDOWNID in _reply:
        _initial_set(_reply[SETDOWNID], _setdown_inst)
    return jsonify({'Thing': 'Deleted'}), 201


# ############################################################
# ################ START THE SERVER ##########################
# ############################################################

if __name__ == '__main__':
    _start_zeromq_pub()
    # _start_zeromq_sub()
    app.run(host='localhost', port=8000, debug=False)

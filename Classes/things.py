from __future__ import print_function
import sqlite3 as lite
import ast

# ################### Initial configuration #####################

UNAME = 'ucloud'
SETUPID = 'setup'
SETDOWNID = 'setdown'
DB_DIR = '../DataBase/Things.db'
IDENTIFIER = 'mac'
JSONID = 'json'
METAJSONID = 'metajson'
DB_COLUMN = {
    IDENTIFIER: 'identifier',
    JSONID: 'jsonid',
    METAJSONID: 'metajsonid'
}
MANAGE_VALUE = {
    'replace': lambda _model, _init, _new, _key: _new,
    'maintain': lambda _model, _init, _new, _key: _init[_key],
    'add': lambda _model, _init, _new, _key: _create_list(
        _init[_key], _new),
    'erase': lambda _model, _init, _new, _key: '',
    'remove': lambda _model, _init, _new, _key: _remove_list(
        _init[_key], _new)
}
DB_COLUMN_NUM = {
    IDENTIFIER: 0,
    JSONID: 1,
    METAJSONID: 2
}

# ######## Append a new item into a list and return the value ########


def _create_list(_init, _new):
    _init.append(_new)
    return _init

# #################### Remove a item of a list #################


def _remove_list(_init, _new):
    _init.remove(_new)
    return _init


# ############### Retrieve everything of a column #############
def retrieve_all_col(col):
    """ Retrieve everything of a column """
    _col_connected_things = []
    _connected_things = search_db()

    for _things in range(len(_connected_things)):
        _col_connected_things.append({
            IDENTIFIER: _connected_things[_things][
                DB_COLUMN_NUM[IDENTIFIER]],
            col: _connected_things[_things][DB_COLUMN_NUM[col]]})
    return _col_connected_things

# ################# Start the Data Base connection ########################


def _start_db_connection():
    return lite.connect(DB_DIR)

# ####################### Search on the Data Base ##########


def search_db(_search_column=None, _search_filter=None,
              _ret_col=None):
    if not _ret_col:
        if not _search_column:
            _ret_col = 'all'
        else:
            _ret_col = _search_column
    _db_con = _start_db_connection()
    _columns = ''
    with _db_con:
        _db_con.row_factory = lite.Row
        _cur = _db_con.cursor()
        if not _search_filter or not _search_column:
            _cur.execute('SELECT * FROM Things ')
        else:
            _cur.execute('SELECT * FROM Things WHERE ' +
                         str(_search_column) + ' LIKE "%' +
                         str(_search_filter) + '%"')

        _all_columns = _cur.fetchall()
        for x in _all_columns:
            if _ret_col == 'all':
                _columns = (_columns + '[' + str(x['identifier']) + ',' +
                            str(x['jsonid']) + ',' + str(x['metajsonid'])
                            + '],')

            else:
                _columns = _columns + str(x[_ret_col]) + ","

    _db_con.close()

    _columns = _columns[:-1]
    try:
        _columns = ast.literal_eval(_columns)
    except:
        pass
    if 'tuple' not in str(type(_columns)) and _columns:
        _columns = _columns,
    return _columns

# ########################## Add new thing ###################


def add(new_thing):
    try:
        if search_db(DB_COLUMN[IDENTIFIER],
                     new_thing[IDENTIFIER]):
            _msg = {'error': True, 'cause': 'duplicate', 'code': 409}
        else:
            # If the name is repeated in the Data base a new name is given
            # (maybe unnecessary cuz identifier)
            x = 0
            _new_name = new_thing[JSONID]['name']
            while search_db(DB_COLUMN[JSONID],
                            '\'' + str(_new_name) + '\''):
                x += 1
                _new_name = new_thing[JSONID]['name'] + str(x)

            new_thing[JSONID]['name'] = _new_name
            _add_thing_db(new_thing)
            _msg = {'error': False}
    except Exception, e:
        if 'name' in str(e):
            _msg = {'error': True, 'cause': 'name', 'code': 400}
        elif 'integer' in str(e) or 'getitem' in str(e):
            _msg = {'error': True, 'cause': 'badtype', 'code': 400}

    return _msg

# ################# Insert new Thing in the Data Base #####################


def _add_thing_db(new_thing):

    _db_con = _start_db_connection()

    with _db_con:
        _cur = _db_con.cursor()
        _cur.execute("INSERT INTO Things VALUES(" +
                     str(new_thing[IDENTIFIER]) + ",\""
                     + str(new_thing[JSONID]) + "\",\""
                     + str(new_thing[METAJSONID]) + "\")")

    _db_con.close()

# ################ Modify record of the Data Base #########################


def _modify_db(idThing, thing):
    _db_con = _start_db_connection()
    with _db_con:
        cur = _db_con.cursor()
        cur.execute("UPDATE Things SET jsonid=\""
                    + str(thing) + "\" WHERE identifier=" + str(idThing))

    _db_con.close()

# #################### Delete from the Data Base ##########################


def _delete_db(search_filt):
    _db_con = _start_db_connection()
    with _db_con:
        cur = _db_con.cursor()
        cur.execute('DELETE FROM Things WHERE identifier LIKE "%'
                    + str(search_filt) + '%"')

    _db_con.close()

# ############## Search for matches on the Data base ######################


def modify(mod_thing):
    _target_thing = search_db(DB_COLUMN[IDENTIFIER],
                              mod_thing[IDENTIFIER], 'all')
    if not _target_thing:
        _msg = {'error': True, 'cause': None, 'code': 404}
    else:
        _target_thing = _target_thing[0] # ast.literal_eval(_target_thing)
        _json_thing = _target_thing[1].copy()
        _metajson_thing = _target_thing[2]
        _msg = _change_managment(mod_thing[JSONID], '',
                                 _json_thing, _metajson_thing)
        try:
            if _msg['error']:
                pass
            elif len(set(_json_thing.items()) ^
                     set(_target_thing[1].items())) != 0:
                _modify_db(_target_thing[0], _json_thing)
            else:
                _msg = {'error': True, 'cause': 'modifyRepeat', 'code': 409}
        except Exception, e:
            if "out of range" in str(e):
                _msg = {'error': True, 'cause': 'modifyRepeat', 'code': 409}
    return _msg

# ################### Identify the changes made ###########################


def _change_managment(_mod_json_thing, _current_dir,
                      _json_thing, _metajson_thing):
    _msg = {'error': False, 'instructions': []}
    try:
        _keys = _mod_json_thing.keys()
        x = 0
        while len(_keys) > x:
            _sub_dir = _change_managment(_mod_json_thing[_keys[x]],
                                         '/' + str(_current_dir) +
                                         str(_keys[x]),
                                         _json_thing[_keys[x]],
                                         _metajson_thing)
            if _sub_dir['error']:
                if _mod_json_thing[_keys[x]] != _json_thing[_keys[x]]:
                    _msg['instructions'].append(
                        _thing_actions(_metajson_thing[_current_dir + '/' +
                                                       str(_keys[x])],
                                       _mod_json_thing[_keys[x]],
                                       _json_thing, _keys[x]))
            else:
                return _sub_dir
            x += 1
        return _msg
    except:
        return {'error': True, 'cause': 'notDir', 'code': 409}
# #################### Make the required changes ########################


def _thing_actions(_model, _new_value, _init_value, _key,
                   _validate=True):

    _msg = {'error': False}
    if _validate:
        _msg = _validate_payload(_model['validtype'],
                                 _model['validmsg'], _new_value)
    if not _msg['error']:
        _msg = {'error': False, 'instructions': []}
        try:
            if 'item' in _model:
                _thing_actions(_model['item'], _new_value,
                               _init_value,
                               _model['item']['key'])
            else:
                _init_value[_key] = MANAGE_VALUE[_model['value']](
                    _model, _init_value, _new_value, _key)
        except:
            pass
        _msg = {'model': _model, 'value': _new_value}
        #_msg['instructions'].append({'model': _model, 'value': _new_value})
    return _msg

# ################### Check if the payload is correct ####################


def _validate_payload(_valid_type, _valid_msg, _to_val_msg):

    if type(_valid_type) is not list:
        _valid_type = _valid_type,
    if type(_valid_msg) is not list:
        _valid_msg = _valid_msg,
    _to_val_type = str(type(_to_val_msg))
    _to_val_type = _to_val_type.split("'")
    if ((_to_val_type[1] not in _valid_type and '' not in _valid_type) or
            (_to_val_msg not in _valid_msg and '' not in _valid_msg)):
        return {'error': True, 'cause': None, 'code': 400}
    else:
        return {'error': False}

# ############## Check the instructions for the port ######################


def check_inst(_inst_dir, _inst_msg, _col_name):
    _msg = []
    _targets = search_db(_col_name, _inst_dir, 'all')
    if _targets:
        for _thing in _targets:
            _target_thing = _thing
            _json_thing = _target_thing[1].copy()
            _metajson_thing = _target_thing[2][_inst_dir]
            _msg.append(_thing_actions(_metajson_thing, _inst_msg, _json_thing,
                                       _metajson_thing['dir'], False))
            if _json_thing is not _target_thing[1]:
                _modify_db(_target_thing[0], _json_thing)
        return _msg


# ###################### Delete a specific Thing ######################


def delete(_del_thing):
    _target = search_db(DB_COLUMN[IDENTIFIER],
                        _del_thing[IDENTIFIER],
                        DB_COLUMN[METAJSONID])
    if not _target:
        return {'error': True, 'cause': None, 'code': 404}
    else:
        _delete_db(_del_thing[IDENTIFIER])
        return {'error': False, 'target': _target}

# ###################### Find specific things #####################


def find(_target_filter):
    if not _target_filter:
        _target_filter = {}
    _final_things = ()
    _things_found = search_db(DB_COLUMN[METAJSONID], 'show',
                              'all')
    try:
        for _thing in range(len(_things_found)):
            _found = _things_found[_thing][DB_COLUMN_NUM
                                           [METAJSONID]]['show']
            _identifier = _things_found[_thing][DB_COLUMN_NUM
                                                [IDENTIFIER]]
            _found = _apply_filter(_found, _target_filter)
            if _found:
                _final_things = _final_things + (
                    {IDENTIFIER: _identifier, 'found':
                     _found},)
    except:
        _final_things = ()
    if not _final_things:
        _final_things = 'Not found'
    return _final_things

# ###################### Filter the Things Found  ##################


def _apply_filter(_found, _target_filter):
    _filtered = []
    for _action in range(len(_found)):
        if len(filter(lambda _filter: _target_filter[_filter] in _found[
                _action][_filter], _target_filter)) is len(_target_filter):
            _filtered.append(_found[_action])
    return _filtered

# ################### Check if any field is missing #######################


def missing_data(_req_json, _msg_exception):

    if (IDENTIFIER not in _req_json and
            _msg_exception != IDENTIFIER):

        _msg = '400' + IDENTIFIER
    elif JSONID not in _req_json and _msg_exception != JSONID:
        _msg = '400' + JSONID
    elif (METAJSONID not in _req_json and
          _msg_exception != METAJSONID):
        _msg = '400' + METAJSONID
    else:
        _msg = None

    return _msg

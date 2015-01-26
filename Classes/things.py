from __future__ import print_function
import sqlite3 as lite
import ast


class Things:

    # ################### Initial configuration #####################

    def __init__(self):
        self.DB_DIR = '../DataBase/Things.db'
        self.IDENTIFIER = 'mac'
        self.JSONID = 'json'
        self.METAJSONID = 'metajson'
        self.DB_COLUMN = {
            self.IDENTIFIER: 'identifier',
            self.JSONID: 'jsonid',
            self.METAJSONID: 'metajsonid'
        }
        self.MANAGE_VALUE = {
            'replace': lambda _model, _init, _new, _key: _new,
            'maintain': lambda _model, _init, _new, _key: _init[_key],
            'add': lambda _model, _init, _new, _key: self._create_list(
                _init[_key], _new),
            'erase': lambda _model, _init, _new, _key: '',
            'remove': lambda _model, _init, _new, _key: self._remove_list(
                _init[_key], _new)
        }
        self.DB_COLUMN_NUM = {
            self.IDENTIFIER: 0,
            self.JSONID: 1,
            self.METAJSONID: 2
        }

    # ######## Append a new item into a list and return the value ########

    def _create_list(self, _init, _new):
        _init.append(_new)
        return _init

    # #################### Remove a item of a list #################

    def _remove_list(self, _init, _new):
        _init.remove(_new)
        return _init

    # ############### Retrieve everything of a column #############
    def retrieve_all_col(self, col):
        """ Retrieve everything of a column """
        _col_connected_things = []
        _connected_things = self.search_db()

        try:
            _connected_things = ast.literal_eval(_connected_things)
        except:
            pass

        for _things in range(len(_connected_things)):
            _col_connected_things.append({
                self.IDENTIFIER: _connected_things[_things][
                    self.DB_COLUMN_NUM[self.IDENTIFIER]],
                col: _connected_things[_things][self.DB_COLUMN_NUM[col]]})
        return _col_connected_things

    # ################# Start the Data Base connection ########################

    def _start_db_connection(self):
        self._db_con = lite.connect(self.DB_DIR)

    # ################## Stop the Data Base connection #####################

    def _stop_db_connection(self):
        self._db_con.close()
    # ####################### Search on the Data Base ##########

    def search_db(self, _search_column=None, _search_filter=None,
                  _ret_col=None):
        if not _ret_col:
            if not _search_column:
                _ret_col = 'all'
            else:
                _ret_col = _search_column
        self._start_db_connection()
        _columns = ''
        with self._db_con:
            self._db_con.row_factory = lite.Row
            _cur = self._db_con.cursor()
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

        self._stop_db_connection()

        _columns = _columns[:-1]
        return _columns

    # ########################## Add new thing ###################

    def add(self, new_thing):
        if self.search_db(self.DB_COLUMN[self.IDENTIFIER],
                          new_thing[self.IDENTIFIER]):
            _msg = (False, 'duplicate', 409)
        else:
            # If the name is repeated in the Data base a new name is given
            # (maybe unnecessary cuz identifier)

            x = 0
            _new_name = new_thing[self.JSONID]['name']
            while self.search_db(self.DB_COLUMN[self.JSONID],
                                 '\'' + str(_new_name) + '\''):
                x += 1
                _new_name = new_thing[self.JSONID]['name'] + str(x)

            new_thing[self.JSONID]['name'] = _new_name
            if('int' not in str(type(new_thing[self.IDENTIFIER])) or
               'dict' not in str(type(new_thing[self.JSONID])) or
               'dict' not in str(type(new_thing[self.METAJSONID]))):
                _msg = (False, 'badtype', 400)
            else:
                self._add_thing_db(new_thing)
                _msg = True,
        return _msg

    # ################# Insert new Thing in the Data Base #####################

    def _add_thing_db(self, new_thing):

        self._start_db_connection()

        with self._db_con:
            _cur = self._db_con.cursor()
            _cur.execute("INSERT INTO Things VALUES(" +
                         str(new_thing[self.IDENTIFIER]) + ",\""
                         + str(new_thing[self.JSONID]) + "\",\""
                         + str(new_thing[self.METAJSONID]) + "\")")

        self._stop_db_connection()

    # ################ Modify record of the Data Base #########################

    def _modify_db(self, idThing, thing):
        self._start_db_connection()
        with self._db_con:
            cur = self._db_con.cursor()
            cur.execute("UPDATE Things SET jsonid=\""
                        + str(thing) + "\" WHERE identifier=" + str(idThing))

        self._stop_db_connection()

    # #################### Delete from the Data Base ##########################

    def _delete_db(self, search_filt):
        self._start_db_connection()
        with self._db_con:
            cur = self._db_con.cursor()
            cur.execute('DELETE FROM Things WHERE identifier LIKE "%'
                        + str(search_filt) + '%"')

        self._stop_db_connection()

    # ############## Search for matches on the Data base ######################

    def modify(self, mod_thing):
        _target_thing = self.search_db(self.DB_COLUMN[self.IDENTIFIER],
                                       mod_thing[self.IDENTIFIER], 'all')
        if not _target_thing:
            _msg = (False, None, 404)
        else:
            _target_thing = ast.literal_eval(_target_thing)
            _json_thing = _target_thing[1].copy()
            _metajson_thing = _target_thing[2]
            _msg = self._change_managment(mod_thing[self.JSONID], '',
                                          _json_thing, _metajson_thing)
            if _json_thing is not _target_thing[1] and _msg[0]:
                self._modify_db(_target_thing[0], _json_thing)
        return _msg

    # ############## Check the instructions for the port ######################

    def check_inst(self, _inst_dir, _inst_msg, _col_name):

        _target_thing = self.search_db(_col_name, _inst_dir, 'all')
        if _target_thing:
            _target_thing = ast.literal_eval(_target_thing)
            _json_thing = _target_thing[1].copy()
            _metajson_thing = _target_thing[2][_inst_dir]
            _msg = self._thing_actions(_metajson_thing, _inst_msg, _json_thing,
                                       _metajson_thing['dir'], False)
            if _json_thing is not _target_thing[1]:
                self._modify_db(_target_thing[0], _json_thing)
            return _msg

    # ################### Identify the changes made ###########################

    def _change_managment(self, _mod_json_thing, _current_dir,
                          _json_thing, _metajson_thing):
        _msg = ()
        try:
            _keys = _mod_json_thing.keys()
            x = 0
            while len(_keys) > x:
                _sub_dir = self._change_managment(_mod_json_thing[_keys[x]],
                                                  '/' + str(_current_dir) +
                                                  str(_keys[x]),
                                                  _json_thing[_keys[x]],
                                                  _metajson_thing)
                if not _sub_dir[0]:
                    if _mod_json_thing[_keys[x]] is not _json_thing[_keys[x]]:
                        _msg = _msg + self._thing_actions(
                            _metajson_thing[_current_dir + '/' +
                                            str(_keys[x])],
                            _mod_json_thing[_keys[x]],
                            _json_thing, _keys[x])
                else:
                    return _sub_dir
                x += 1
            return _msg
        except:
            return False,

    # #################### Make the required changes ########################

    def _thing_actions(self, _model, _new_value, _init_value, _key,
                       _validate=True):

        _msg = True,
        if _validate:
            _msg = self._validate_payload(_model['validtype'],
                                          _model['validmsg'], _new_value)
        if _msg[0]:
            _msg = ()
            try:
                if 'item' in _model:
                    self._thing_actions(_model['item'], _new_value,
                                        _init_value,
                                        _model['item']['key'])
                else:
                    _init_value[_key] = self.MANAGE_VALUE[_model['value']](
                        _model, _init_value, _new_value, _key)
            except Exception:
                pass
            _msg = _msg + (_model, _new_value)
        return _msg

    # ################### Check if the payload is correct ####################

    def _validate_payload(self, _valid_type, _valid_msg, _to_val_msg):

        if type(_valid_type) is not list:
            _valid_type = _valid_type,
        if type(_valid_msg) is not list:
            _valid_msg = _valid_msg,
        _to_val_type = str(type(_to_val_msg))
        _to_val_type = _to_val_type.split("'")
        if ((_to_val_type[1] not in _valid_type and '' not in _valid_type) or
                (_to_val_msg not in _valid_msg and '' not in _valid_msg)):
            _msg = (False, None, 400)
        else:
            _msg = True,

        return _msg

    # ###################### Delete a specific Thing ######################

    def delete(self, _del_thing):
        _target = self.search_db(self.DB_COLUMN[self.IDENTIFIER],
                                 _del_thing[self.IDENTIFIER],
                                 self.DB_COLUMN[self.METAJSONID])
        if not _target:
            _msg = (False, None, 404)
        else:
            self._delete_db(_del_thing[self.IDENTIFIER])
            _msg = _target
        return _msg

    # ###################### Find specific things #####################

    def find(self, _target_type, _target_filter=None):
        _final_things = ()
        _things_found = self.search_db(self.DB_COLUMN[self.METAJSONID], 'show',
                                       'all')
        try:
            _things_found = ast.literal_eval(_things_found)
            for _thing in range(len(_things_found)):
                _found = _things_found[_thing][self.DB_COLUMN_NUM
                                               [self.METAJSONID]]['show']
                _identifier = _things_found[_thing][self.DB_COLUMN_NUM
                                                    [self.IDENTIFIER]]
                if _target_filter:
                    _found = self._apply_filter(_found, _target_filter)
                if _found:
                    _final_things = _final_things + (
                        {self.IDENTIFIER: _identifier, 'found':
                         _found},)
        except Exception, e:
            print(e)
            _final_things = ()
        if not _final_things:
            _final_things = 'Not Found'
        return _final_things
    # ###################### Filter the Things Found  ##################

    def _apply_filter(self, _found, _target_filter):
        _filtered = []
        for _action in range(len(_found)):
            if filter(lambda _filter: _target_filter[_filter] in _found[
                    _action][_filter], _target_filter):
                _filtered.append(_found[_action])
        return _filtered

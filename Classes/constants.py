import ast

# ##### Read the JSON files containing the defined constants #####

base_directory = '../Constants/'


def retrieve(_file_direction):
    try:
        _text = open(base_directory + _file_direction, 'r')
        _constants = _text.read()
        _constants = ast.literal_eval(_constants)
        _text.close()
    except Exception, e:
        _constants = 'ERROR: ' + str(e)
    return _constants

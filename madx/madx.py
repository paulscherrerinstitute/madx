import subprocess
import re
import uuid
import os
import logging
import pandas

# Different kind of regex patterns for matching different outputs of madx
pattern_twiss = re.compile(r'^(twiss.*,file=")[a-z,A-Z,0-9,.]+(";)$', flags=re.MULTILINE)
pattern_save = re.compile(r'^(save.*,file=")[a-z,A-Z,0-9,.]+(";)$', flags=re.MULTILINE)
pattern_write = re.compile(r'^(write.*,file=")[a-z,A-Z,0-9,.]+(";)$', flags=re.MULTILINE)

# Output mode depending on what pattern matched
TWISS = 1
SAVE = 2
WRITE = 3

madx_binary = None


def get_madx_binary():
    """
    Initialize module to find out the location of the packaged madx binary
    :return:
    """

    global madx_binary
    if madx_binary:
        return madx_binary

    import platform
    import pkg_resources

    if platform.uname()[0].lower() == 'darwin':
        if platform.architecture()[0] == '64bit':
            madx_binary = pkg_resources.resource_filename('madx', 'madx-macosx64')
    elif platform.uname()[0].lower() == 'linux':
        if platform.architecture()[0] == '64bit':
            madx_binary = pkg_resources.resource_filename('madx', 'madx-linux64')

    return madx_binary


def execute(instructions='', raw_results=False):
    """
    Execute madx with the passed instructions

    :param instructions:    Instruction to be executed by madx
    :return:                Output of madx
    """

    temporary_file = '/tmp/'+str(uuid.uuid4())

    if isinstance(instructions, list):
        instructions = '\n'.join(instructions)

    # Process instructions to ensure that we capture the output
    # i.e. find statements like this and add a temporary file for the output
    # twiss, range=#s/#e, sequence=swissfel,betx=betax0,bety=betay0,alfx=alphax0,alfy=alphay0,file="OptServScript.dat";

    output_mode = None

    results = pattern_twiss.subn(r'\1%s\2' % temporary_file, instructions)
    # Needs to match: 'twiss, range=#s/#e, sequence=swissfel,betx=betax0,bety=betay0,alfx=alphax0,alfy=alphay0,file="%s.dat";\n' % filename
    instructions = results[0]
    no_matches = results[1]
    if no_matches:
        logging.info('Matched for twiss output')
        output_mode = TWISS

    # will always return one or more per each line `variable = value;`
    # sometimes there will be `:=` instead of `=`
    results = pattern_save.subn(r'\1%s\2' % temporary_file, instructions)
    # Needs to match: 'save,file="OptServValues.angle";\n'
    instructions = results[0]
    no_matches = results[1]
    if no_matches:
        logging.info('Matched for save output')
        output_mode = SAVE

    # OptServValues.R56
    results = pattern_write.subn(r'\1%s\2' % temporary_file, instructions)
    # Needs to match: 'write,table=r56data,file="OptServValues.R56";\n'
    instructions = results[0]
    no_matches = results[1]
    if no_matches:
        logging.info('Matched for write output')
        output_mode = WRITE

    try:
        # Create madx process
        process = subprocess.Popen([get_madx_binary()], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Pass instructions to stdin
        output = process.communicate(instructions.encode())[0]

        # Read the results
        if os.path.isfile(temporary_file):
            try:
                logging.info('Parsing result files')
                if raw_results:
                    with open(temporary_file, 'r') as t_file:
                        results = t_file.read().splitlines()
                else:
                    if output_mode == SAVE:
                        results = read_save_data(temporary_file)
                    elif output_mode == TWISS or output_mode == WRITE:
                        results = read_twiss_write_data(temporary_file)
                    else:
                        logging.warning('Output mode not supported')

            except Exception:
                logging.debug('Unable to read output file')
                results = None
        else:
            results = None

    finally:
        if os.path.isfile(temporary_file):
            # Ensure that temporary file gets deleted
            os.remove(temporary_file)

    return Result(results, output.decode().split('\n'))


def resolve_type(formatting, value):
    """
    Resolve value type based on formatting string
    :param formatting:
    :param value:
    :return:
    """
    if formatting.endswith('s'):
        return value.rstrip('"').lstrip('"')
    elif formatting == '%le':
        return float(value)
    else:
        logging.info('Cannot determine type of variable')
        return value


def read_twiss_write_data(filename):
    """
    Read the data from the madx twiss and write commands

    Structure of the output:
    ----
    ^@ (global) variables - [name] [format] [value]
    ^* name of column
    ^$ format/type
    values

    :param filename: Name of the data file
    :return:
    """

    with open(filename, 'r') as f:
        lines = f.readlines()

    global_variables = dict()
    pattern_global_variable = re.compile(r'^@\s+(\S+)\s+(%\S+)\s+(.+)$')

    pattern_column_names = re.compile(r'^\*\s+((\S+)\s+)*$')
    pattern_column_format = re.compile(r'^\$\s+((\S+)\s+)*$')
    pattern_data = re.compile(r'^\s*((\S+)\s*)*$')

    data_list = []

    for line in lines:
        # Check if lines holds global variables
        result = pattern_global_variable.match(line)
        if result:
            global_variables[result.group(1)] = resolve_type(result.group(2), result.group(3))
            continue

        # ---- DATA SECTION OF FILE

        # Check if line holds column names
        result = pattern_column_names.match(line)
        if result:
            columns = result.group(0).lstrip('*').split()
            continue

        # Check if line holds column formats
        result = pattern_column_format.match(line)
        if result:
            column_formats = result.group(0).lstrip('$').split()
            continue

        # Check if line holds data
        result = pattern_data.match(line)
        if result:
            data = line.split()
            # Resolve data type
            for i in range(len(data)):
                data[i] = resolve_type(column_formats[i], data[i])
            data_list.append(data)

    return Data(global_variables, None, pandas.DataFrame(data_list, columns=columns))


def read_save_data(filename):
    """
    Read data from madx save command
    :param filename: name of the file to read
    :return: Dictionary of variables
    """
    with open(filename, 'r') as f:
        lines = f.readlines()

    variables = dict()
    pattern_variable = re.compile(r'^(\S+)\s+=\s+(.+);$')

    for line in lines:
        result = pattern_variable.match(line)
        if result:
            variables[result.group(1)] = float(result.group(2))
    return Data(None, variables, None)


class Result:
    def __init__(self, data, output):
        self.data = data
        self.output = output


class Data:
    def __init__(self, global_variables, variables, table):
        self.global_variables = global_variables
        self.variables = variables
        self.table = table


class Instructions:

    def __init__(self):
        self.buffer = []

    def append(self, instruction):
        self.buffer.append(instruction)

    def clear(self):
        self.buffer = []

    def execute(self, raw_results=False):
        return execute(self.buffer, raw_results=raw_results)


if __name__ == '__main__':

    import argparse
    import sys
    # temporary_file = '/tmp/' + str(uuid.uuid4())

    argsPars = argparse.ArgumentParser()
    argsPars.add_argument('file', help="madx input file")
    argsPars.add_argument('-r', '--raw', action="store_true", help='Return raw output of madx')

    arguments = argsPars.parse_args()

    input_file = arguments.file
    raw_output = arguments.raw

    with open(input_file, 'r') as f:
        inp = f.read().splitlines()

    if raw_output:
        print('\n'.join(execute(inp, raw_results=True).results))
    else:
        print(execute(inp).data.table)


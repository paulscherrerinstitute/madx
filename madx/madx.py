import subprocess
import re
import uuid
import os
import logging

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


def execute(instructions=''):
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


    # Table will be
    # ^@ (global) variables
    # @ name format value
    # ^* name of column
    # ^$ format/type
    # values

    # Each table has a name

    try:
        # Create madx process
        process = subprocess.Popen([get_madx_binary()], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Pass instructions to stdin
        output = process.communicate(instructions.encode())[0]

        # Read the results
        if os.path.isfile(temporary_file):
            try:
                with open(temporary_file, 'r') as t_file:
                    results = t_file.read().splitlines()

                    logging.info('Parsing result files')
                    # TODO need to handle the output
                    # TODO need to parse results based on output_mode

            except Exception:
                logging.debug('Unable to read output file')
                results = None
        else:
            results = None

    finally:
        if os.path.isfile(temporary_file):
            # Ensure that temporary file gets deleted
            os.remove(temporary_file)

    return results, output.decode().split('\n')


class Script:

    def __init__(self):
        self.buffer = []

    def append(self, instruction):
        self.buffer.append(instruction)

    def clear(self):
        self.buffer = []

    def execute(self):
        return execute(self.buffer)


if __name__ == '__main__':

    import sys
    # temporary_file = '/tmp/' + str(uuid.uuid4())

    with open(sys.argv[1], 'r') as f:
        inp = f.read().splitlines()
        # inp = '\n'.join(inp)
        # inp = re.sub(r'^(twiss.*,file=")OptServScript.dat(";)$', r'\1%s\2' % temporary_file, inp, flags=re.MULTILINE)
        #
        # print(inp)

    # print(get_madx_binary())
    print('\n'.join(execute(inp)[0]))

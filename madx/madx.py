import subprocess
import re
import uuid
import os

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
    instructions = re.sub(r'^(twiss.*,file=")OptServScript.dat(";)$', r'\1%s\2' % temporary_file, instructions, flags=re.MULTILINE)

    try:
        # Create madx process
        process = subprocess.Popen([get_madx_binary()], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Pass instructions to stdin
        output = process.communicate(instructions.encode())[0]

        # Read the results
        with open(temporary_file, 'r') as t_file:
            results = t_file.read().splitlines()

    finally:
        # Ensure that temporary file gets deleted
        os.remove(temporary_file)

    return results, output.decode().split('\n')


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

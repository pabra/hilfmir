from os.path import dirname
from os.path import realpath
import os
import subprocess
import sys


PATH = realpath(dirname(__file__))


def echo(*msg, initial_newline=False, final_newline=False, color_fn=None):
    if initial_newline:
        print()

    content = ' '.join(map(str, msg))

    if color_fn:
        content = color_fn(content)

    print(content)

    if final_newline:
        print()


def error(*msg):
    print(' '.join(map(str, (term_red('ERROR:'),) + msg)), file=sys.stderr)
    sys.exit(1)


def term(txt, color_code='0;31'):
    if os.isatty(1):
        return '\033[{}m{}\033[1;0m'.format(color_code, txt)

    return txt


def term_red(txt):
    return term(txt, '0;31')


def term_green(txt):
    return term(txt, '0;32')


def term_brown(txt):
    return term(txt, '0;33')


def term_blue(txt):
    return term(txt, '0;34')


def term_plum(txt):
    return term(txt, '0;35')


def input_str(prompt, default=None, allow_empty=False):
    if default is not None and allow_empty:
        raise ValueError('default and allow_empty')

    value = None
    prompt_value = prompt
    default_str = ''

    if default is not None:
        default_str = str(default)
        prompt_value += ' [{0!r}]'.format(default_str)

    prompt_value += ': '

    while value is None or (not allow_empty and not value):
        value = input(term_green(prompt_value)).strip()

        if not value and default is not None:
            value = default_str

    return value


def input_int(prompt, default=None, min_value=0, max_value=999999):
    if not isinstance(default, (int, type(None))):
        raise ValueError()

    if not isinstance(min_value, (int, type(None))):
        raise ValueError()

    if not isinstance(max_value, (int, type(None))):
        raise ValueError()

    if min_value is not None and default is not None and default < min_value:
        raise ValueError()

    if max_value is not None and default is not None and default > max_value:
        raise ValueError()

    value = None
    prompt_value = prompt

    if min_value is not None or max_value is not None:
        min_max_str = []

        if min_value is not None:
            min_max_str.append('>={}'.format(min_value))

        if max_value is not None:
            min_max_str.append('<={}'.format(max_value))

        prompt_value += ' ({})'.format(', '.join(min_max_str))

    if default is not None:
        prompt_value += ' [{}]'.format(default)

    prompt_value += ': '

    while value is None:
        value = input(term_green(prompt_value)).strip()

        if not value:
            value = default

        try:
            value = int(value)
        except ValueError:
            value = None
        else:
            if min_value is not None and value < min_value:
                value = None
            elif max_value is not None and value > max_value:
                value = None

    return value


def input_bool(prompt, default=None):
    true_val = ('yes', 'y')
    false_val = ('no', 'n')
    value = None

    if default not in (True, False, None):
        raise ValueError('default not in (True, False, None)')

    prompt_value = '{prompt} [{yes}/{no}]: '.format(
        prompt=prompt,
        yes=true_val[0].upper() if default is True else true_val[0],
        no=false_val[0].upper() if default is False else false_val[0],
        )

    while value not in (True, False):
        value = input(term_green(prompt_value)).strip().lower()

        if not value and default is not None:
            value = default

        if value in true_val:
            value = True
        elif value in false_val:
            value = False

    return value


def execute(*args, **kwargs):
    """Execute a command and return its stdout, stderr and return-/exitcode

    >>> execute(['echo', 'test'])
    {'returncode': 0, 'stderr': '', 'stdout': 'test\\n'}

    >>> execute(['which', 'not-existing'])
    {'returncode': 1, 'stderr': '', 'stdout': ''}

    >>> execute('echo "test" >&2', shell=True)
    {'returncode': 0, 'stderr': 'test\\n', 'stdout': ''}
    """
    p = subprocess.Popen(*args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    stdout, stderr = p.communicate()
    returncode = p.returncode

    return {'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode}

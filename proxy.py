#!/usr/bin/env python3
"""hilfmir ssh proy

Usage:
    proxy.py init
    proxy.py helper (add|remove|update) <name>
    proxy.py seeker (add|remove|update) <name>
    proxy.py list_seekers
    proxy.py (-h | --help)

Options:
    -h --help     Show this screen.
"""


from os.path import expanduser
from os.path import join as pjoin
import json
import os
import re

from docopt import docopt

from utils import PATH
from utils import echo
from utils import error
from utils import input_bool
from utils import input_int
from utils import input_str
from utils import term_brown


CONFIG_TEMPLATE = {
    'helpers': {},
    'seekers': {},
    'ssh_proxy': 'example.org',
    'ssh_port': 22,
    'ssh_user': 'hilfmir',
}
CONFIG_FILE = pjoin(PATH, 'proxy_conf.json')
_CONFIG_CONTENT = None
AUTHORIZED_KEYS_FILE = pjoin(expanduser('~'), '.ssh', 'authorized_keys')
AUTHORIZED_KEYS_TEMPLATE = (
        'restrict,port-forwarding,'
        'command="~/hilfmir/proxy_venv_wrapper.sh list_seekers" '
        '{pub_key} {name} as {helper_or_seeker}'
        )
VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{2,63}$')
VALID_PUB_KEY_PATTERN = re.compile('^(ssh-rsa [a-zA-Z0-9/=+]+)(:? .*)?$')
PORT_MIN = 41300
PORT_MAX = 41399


def get_config(force_read=False):
    global _CONFIG_CONTENT

    if _CONFIG_CONTENT is None or force_read:
        try:
            with open(CONFIG_FILE) as f:
                _CONFIG_CONTENT = json.load(f)
        except FileNotFoundError:
            error('No config file found at {0!r}.'.format(CONFIG_FILE))

    return _CONFIG_CONTENT.copy()


def write_config(config):
    global _CONFIG_CONTENT

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4)

    _CONFIG_CONTENT = None


def test_name(name):
    if not VALID_NAME_PATTERN.match(name):
        raise ValueError('Name {0!r} does not match expression {1!r}.'.format(
            name,
            VALID_NAME_PATTERN.pattern,
            ))


def clean_pubkey(pubkey):
    err_str = 'Public key {0!r} does not match expression {1!r}.'
    match = VALID_PUB_KEY_PATTERN.match(pubkey)
    if not match:
        raise ValueError(err_str.format(
            pubkey,
            VALID_PUB_KEY_PATTERN.pattern,
            ))

    return match.group(1)


def get_used_ports():
    config = get_config()
    return [data['port'] for data in config['seekers'].values()]


def get_next_free_port():
    used_ports = get_used_ports()

    for port in range(PORT_MIN, PORT_MAX + 1):
        if port not in used_ports:
            return port

    raise Exception('No more free ports ({}-{}).'.format(PORT_MIN, PORT_MAX))


def init_proxy():
    echo('You should only continue after you have followed the',
         '\n`setup the ssh proxy` section in the README file.')

    if not input_bool('continue', default=False):
        return

    echo('You will overwrite all settings previously made.',
         color_fn=term_brown)

    if not input_bool('continue', default=False):
        return

    config = CONFIG_TEMPLATE.copy()
    config['ssh_proxy'] = input_str('Hostname of SSH proxy',
                                    default=config['ssh_proxy'])
    config['ssh_port'] = input_int('SSH port of proxy',
                                   default=config['ssh_port'])
    config['ssh_user'] = input_str('User name on SSH proxy',
                                   default=config['ssh_user'])

    write_config(config)


def list_seekers():
    config = get_config()

    for name, data in config['seekers'].items():
        echo('{},{},{}'.format(name, data['user_name'], data['port']),
             final_newline=False)


def handle_authorized_keys(pub_key, name, helper_or_seeker, remove=False):
    if helper_or_seeker not in ('helper', 'seeker'):
        raise ValueError()

    if remove:
        lines_to_keep = []
        file_will_change = False
        for line in open(AUTHORIZED_KEYS_FILE):
            if (pub_key in line
                    and name in line
                    and helper_or_seeker in line):
                file_will_change = True
            else:
                lines_to_keep.append(line)

        if file_will_change:
            with open(AUTHORIZED_KEYS_FILE, 'w') as fd:
                fd.writelines(lines_to_keep)

    else:
        new_line = AUTHORIZED_KEYS_TEMPLATE \
                   .format(pub_key=pub_key,
                           name=name,
                           helper_or_seeker=helper_or_seeker)

        with open(AUTHORIZED_KEYS_FILE, 'a') as fd:
            fd.write(new_line + '\n')


def remove_helper(name):
    config = get_config()

    if name not in config['helpers']:
        raise ValueError('Helper {0!r} does not exist.'.format(name))

    handle_authorized_keys(config['helpers'], name, 'helper', remove=True)
    config['helpers'].pop(name)
    write_config(config)


def update_helper(name, is_new=True):
    test_name(name)
    config = get_config()

    if name in config['helpers'] and is_new:
        raise ValueError('Helper {0!r} already exists.'.format(name))
    elif name not in config['helpers'] and not is_new:
        raise ValueError('Helper {0!r} does not exist.'.format(name))

    echo('You could create a new SSH RSA key pair with')
    echo('ssh-keygen -b 2048 -t rsa -C "${USER}@hilfmir"',
         '-N "" -f ./helper',
         '&& cat ./helper.pub',
         final_newline=True,
         color_fn=term_brown)

    pub_key = input_str('Enter public key for {0!r}'.format(name),
                        default=(None if is_new
                                 else config['helpers'][name]['public_key']))
    pub_key = clean_pubkey(pub_key)

    if not is_new:
        handle_authorized_keys(config['helpers'][name]['public_key'],
                               name,
                               'helper',
                               remove=True)

    handle_authorized_keys(pub_key, name, 'helper')
    config['helpers'][name] = {'public_key': pub_key}
    write_config(config)


def remove_seeker(name):
    config = get_config()

    if name not in config['seekers']:
        raise ValueError('Seeker {0!r} does not exist.'.format(name))

    handle_authorized_keys(config['seekers'], name, 'seeker', remove=True)
    config['seekers'].pop(name)
    write_config(config)


def update_seeker(name, is_new=True):
    test_name(name)
    config = get_config()

    if name in config['seekers'] and is_new:
        raise ValueError('Seeker {0!r} already exists.'.format(name))
    elif name not in config['seekers'] and not is_new:
        raise ValueError('Seeker {0!r} does not exist.'.format(name))

    port = get_next_free_port() if is_new else config['seekers'][name]['port']
    user_name = input_str('Enter user name of {0!r}'.format(name),
                          name if is_new
                          else config['seekers'][name]['user_name'])

    echo('You could create a new SSH RSA key pair with')
    echo('ssh-keygen -b 2048 -t rsa -C "${USER}@hilfmir"',
         '-N "" -f ./seeker',
         '&& cat ./seeker.pub',
         final_newline=True,
         color_fn=term_brown)

    pub_key = input_str('Enter public key for {0!r}'.format(name),
                        default=(None if is_new
                                 else config['seekers'][name]['public_key']))
    pub_key = clean_pubkey(pub_key)

    if not is_new:
        handle_authorized_keys(config['seekers'][name]['public_key'],
                               name,
                               'seeker',
                               remove=True)

    handle_authorized_keys(pub_key, name, 'seeker')
    config['seekers'][name] = {'port': port,
                               'user_name': user_name,
                               'public_key': pub_key}
    write_config(config)


def main():
    arguments = docopt(__doc__)
    print(arguments)

    if arguments['init']:
        init_proxy()
    elif arguments['list_seekers']:
        list_seekers()
    elif arguments['helper']:
        if arguments['remove']:
            remove_helper(arguments['<name>'])
        else:
            update_helper(arguments['<name>'], is_new=arguments['add'])
    elif arguments['seeker']:
        if arguments['remove']:
            remove_seeker(arguments['<name>'])
        else:
            update_seeker(arguments['<name>'], is_new=arguments['add'])


if __name__ == '__main__':
    if os.getuid() == 0:
        error('Do not run {0!r} as root'.format(__file__))

    main()

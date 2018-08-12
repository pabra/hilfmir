#!/usr/bin/env python3

from os.path import basename
from os.path import dirname
from os.path import extsep
from os.path import join as pjoin
from os.path import realpath
from os.path import splitext
import argparse
import json
import re
import sys

from utils import echo, error, term_brown, term_green, term_red


CONFIG_FILE = pjoin(realpath(dirname(__file__)),
                    extsep.join([splitext(basename(__file__))[0],
                                 'json']))
CONFIG_TEMPLATE = {
    'helpers': {},
    'seekers': {},
    'ssh_proxy': 'example.org',
    'ssh_port': 22,
    'ssh_user': 'hilfmir',
}
VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{2,63}$')
VALID_PUB_KEY_PATTERN = re.compile('^(ssh-rsa [a-zA-Z0-9/=+]+)(:? .*)?$')
PORT_MIN = 41300
PORT_MAX = 41399
REPO_URL = 'https://github.com/pabra/hilfmir.git'
UBUNTU_SEEKER_PACKAGES = ['openssh-server',
                          'x11vnc',
                          'git']


def get_config():
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    except FileNotFoundError:
        config = CONFIG_TEMPLATE

    return config


def get_used_ports():
    config = get_config()
    return [data['port'] for data in config['seekers'].values()]


def get_next_free_port():
    used_ports = get_used_ports()

    for port in range(PORT_MIN, PORT_MAX + 1):
        if port not in used_ports:
            return port

    raise Exception('No more free ports ({}-{}).'.format(PORT_MIN, PORT_MAX))


def write_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, sort_keys=True, indent=4)


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


def add_seeker(name=None):
    if name is None:
        name = input_str('Enter name of new seeker')

    test_name(name)
    config = get_config()

    if name in config['seekers']:
        raise ValueError('Name {0!r} already exists as seeker.'.format(name))

    user_name = input_str('Enter user name of {0!r}'.format(name), name)

    port = get_next_free_port()
    echo('On a new seeker machine the following (Ubuntu) packages should be '
         'installed:', final_newline=False)
    echo('  ' + ' '.join(UBUNTU_SEEKER_PACKAGES), color_fn=term_brown)
    echo('Clone the repository:', final_newline=False)
    echo('  cd ~ && git clone {} .hilfmir && cd .hilfmir'.format(REPO_URL),
         color_fn=term_brown)
    echo('Generate a new SSH (RSA) key:', final_newline=False)
    echo('  ssh-keygen -b 2048 -t rsa -C "${USER}@hilfmir" -N "" -f ./seeker',
         color_fn=term_brown)
    echo('Provide the public key:', final_newline=False)
    echo('  cat seeker.pub', color_fn=term_brown)

    pub_key = input_str('Enter public key for {0!r}'.format(name))
    pub_key = clean_pubkey(pub_key)

    config['seekers'][name] = {'port': port,
                               'user_name': user_name,
                               'public_key': pub_key}

    write_config(config)

    all_helpers = list(config['helpers'].keys())
    echo('Enter space separated list of helpers who should get access to '
         'the seekers machine.', final_newline=False)
    echo('Possible helpers are:', final_newline=False)
    echo('  ' + ' '.join(all_helpers), color_fn=term_brown)
    add_helpers = input_str('Helper names', ' '.join(all_helpers))
    add_helpers_list = add_helpers.split(' ')
    if not all(h in all_helpers for h in add_helpers_list):
        raise ValueError('Not all helpers are known.')

    authorized_keys_str = '\n'.join('{} {}@helpers'.format(data['public_key'],
                                                           name)
                                    for name, data
                                    in config['helpers'].items()
                                    if name in add_helpers_list)

    echo('add helper keys to authorized_keys file of current user ({0!r}) '
         'and \'root\' as desired:'.format(user_name), final_newline=False)
    echo('For current user ({0!r}):'.format(user_name), final_newline=False)
    echo('[ ! -d ~/.ssh ] && mkdir -v ~/.ssh && chmod -v 0700 ~/.ssh; '
         'echo \'{}\' >> ~/.ssh/authorized_keys'.format(authorized_keys_str),
         color_fn=term_brown)
    echo('For user \'root\' (run as root):', final_newline=False)
    echo('[ ! -d /root/.ssh ] && mkdir -v /root/.ssh && '
         'chmod -v 0700 /root/.ssh; '
         'echo \'{}\' >> ~/.ssh/authorized_keys'.format(authorized_keys_str),
         color_fn=term_brown)


def remove_seeker(name):
    config = get_config()

    if name is None:
        echo('List of seekers:', final_newline=False)
        echo('  ' + ', '.join(map(term_brown, config['seekers'].keys())))
        name = input_str('Enter name of seeker to remove')

    if name not in config['seekers']:
        raise ValueError('Unknown seeker name {0!r}.'.format(name))

    config['seekers'].pop(name)

    write_config(config)


def add_helper(name=None):
    if name is None:
        name = input_str('Enter name of new helper')

    test_name(name)
    config = get_config()

    if name in config['helpers']:
        raise ValueError('Name {0!r} already exists as helper.'.format(name))

    echo('To create a new SSH RSA key pair, run as {0!r}'.format(name),
         final_newline=False)
    echo('  ssh-keygen -b 2048 -t rsa -C "${USER}@hilfmir" -N "" -f ./helper '
         '&& cat ./helper.pub',
         color_fn=term_brown)
    pub_key = input_str('Enter public key for {0!r}'.format(name))
    pub_key = clean_pubkey(pub_key)

    config['helpers'][name] = {'public_key': pub_key}

    write_config(config)

    echo('Add helper key to authorized keys file on ssh proxy.',
         final_newline=False)
    echo('  echo \'restrict,port-forwarding,'
         'command="~/hilfmir/manage.py show-seekers" '
         '{} {}@helper\' >> /home/{}/.ssh/authorized_keys'
         .format(pub_key, name, config['ssh_user']),
         color_fn=term_brown)


def remove_helper(name):
    config = get_config()

    if name is None:
        echo('List of helpers:', final_newline=False)
        echo('  ' + ', '.join(map(term_brown, config['helpers'].keys())))
        name = input_str('Enter name of helper to remove')

    if name not in config['helpers']:
        raise ValueError('Unknown helper name {0!r}.'.format(name))

    config['helpers'].pop(name)

    write_config(config)


def show_seekers():
    config = get_config()

    for name, data in config['seekers'].items():
        echo('{},{},{}'.format(name, data['user_name'], data['port']),
             final_newline=False)


def init_proxy():
    echo('This will overwrite an existing config.', color_fn=term_red)
    confirm = input_bool('Continue', default=False)

    if not confirm:
        return

    config = CONFIG_TEMPLATE
    config['ssh_proxy'] = input_str('Hostname of SSH proxy',
                                    default=config['ssh_proxy'])
    config['ssh_port'] = input_int('SSH port of proxy',
                                   default=config['ssh_port'])
    config['ssh_user'] = input_str('User name on SSH proxy',
                                   default=config['ssh_user'])

    write_config(config)

    #  userdel --force --remove hilfmir
    echo('Add the user on the proxy host.', final_newline=False)
    echo('  ' + 'useradd --no-user-group --gid nogroup --create-home '
         '--shell /bin/bash {}'.format(config['ssh_user']),
         color_fn=term_brown)
    echo('Prepare directories and files.', final_newline=False)
    echo('  ' + 'mkdir -v -m 0700 /home/{user}/.ssh && '
         'touch /home/{user}/.ssh/authorized_keys && '
         'chown -R {user}:nogroup /home/{user}/.ssh'
         .format(user=config['ssh_user']),
         color_fn=term_brown)
    echo('Clone this repository (as user {0!r}).', final_newline=False)
    echo('  cd ~ && git clone {} hilfmir && cd hilfmir'.format(REPO_URL),
         color_fn=term_brown)
    echo('Run init.', final_newline=False)
    echo('  ./{} init'.format(basename(__file__)),
         color_fn=term_brown)


def main():
    parser = argparse.ArgumentParser(description='Manage Users and keys.')
    parser.add_argument('action',
                        choices=['init',
                                 'show-helper',
                                 'show-seeker',
                                 'show-seekers',
                                 'add-helper',
                                 'remove-helper',
                                 'add-seeker',
                                 'remove-seeker'],
                        help='Action to do')
    parser.add_argument('-n', '--name', required=False)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()

    if args.action == 'show':
        get_config()

    elif args.action == 'init':
        #  useradd --no-user-group --gid nogroup --create-home --shell /bin/bash hilfmir
        #  mkdir -v -m 0700 /home/hilfmir/.ssh && touch /home/hilfmir/.ssh/authorized_keys
        #  userdel --force --remove hilfmir
        #  config = CONFIG_TEMPLATE

        #  write_config(config)
        init_proxy()

    elif args.action == 'add-seeker':
        add_seeker(args.name)

    elif args.action == 'remove-seeker':
        remove_seeker(args.name)

    elif args.action == 'add-helper':
        add_helper(args.name)

    elif args.action == 'remove-helper':
        remove_helper(args.name)

    elif args.action == 'show-seekers':
        show_seekers()


if __name__ == '__main__':
    main()

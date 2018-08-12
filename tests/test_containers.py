from os.path import join as pjoin
import pytest
import re
import subprocess


def execute(*args, **kwargs):
    """Execute a command and return its stdout, stderr and return-/exitcode

    >>> execute(['echo', 'test'])
    {'returncode': 0, 'stderr': '', 'stdout': 'test\\n'}

    >>> execute(['which', 'not-existing'])
    {'returncode': 1, 'stderr': '', 'stdout': ''}

    >>> execute('echo "test" >&2', shell=True)
    {'returncode': 0, 'stderr': 'test\\n', 'stdout': ''}
    """
    p = subprocess.Popen(*args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         **kwargs)
    stdout, stderr = p.communicate()
    if isinstance(stdout, bytes):
        stdout = stdout.decode()

    if isinstance(stderr, bytes):
        stderr = stderr.decode()

    returncode = p.returncode

    return {'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode}


def check_returncode(execute_return):
    assert execute_return['returncode'] == 0, (execute_return['stdout'] +
                                               '\n' + execute_return['stderr'])


def get_container_names(output):
    container_names = {'proxy': None, 'helper': None, 'seeker': None}

    for match in re.finditer(r'Creating\s+([a-zA-Z0-9_-]+)\s+\.\.\.\s+done',
                             output):
        hit = match.group(1)
        if 'proxy' in hit:
            container_names['proxy'] = hit
        elif 'helper' in hit:
            container_names['helper'] = hit
        elif 'seeker' in hit:
            container_names['seeker'] = hit

    return container_names


@pytest.fixture(scope='module')
def running_containers():
    dc_build = execute(['docker-compose', 'build', '--pull'])
    check_returncode(dc_build)

    dc_up = execute(['docker-compose', '--no-ansi', 'up', '-d'])
    check_returncode(dc_up)

    containers = get_container_names(dc_up["stderr"])
    assert containers['proxy'] is not None
    assert containers['helper'] is not None
    assert containers['seeker'] is not None

    def exec_proxy(*cmd, user=None, get='stdout'):
        pre_cmd = ['docker', 'exec', containers['proxy']]
        if user is not None:
            pre_cmd.insert(2, '--user')
            pre_cmd.insert(3, str(user))
            if isinstance(user, str):
                pre_cmd.insert(4, '--workdir')
                pre_cmd.insert(5, pjoin('/', 'home', user))
        ret = execute(pre_cmd + list(cmd))
        check_returncode(ret)
        return ret[get]

    containers['exec_proxy'] = exec_proxy

    exec_proxy('useradd',
               '--no-user-group',
               '--gid', 'nogroup',
               '--create-home',
               '--shell',
               '/bin/bash',
               'hilfmir')

    exec_proxy('mkdir', '-v', '-m', '0700', '/home/hilfmir/.ssh',
               user='hilfmir')
    exec_proxy('touch', '/home/hilfmir/.ssh/authorized_keys', user='hilfmir')

    yield containers

    dc_down = execute(['docker-compose', 'down'])
    check_returncode(dc_down)


def test_proxy_config(running_containers):
    auth_keys = running_containers['exec_proxy'](
        'cat',
        '.ssh/authorized_keys',
        user='hilfmir',
    )
    assert auth_keys == 'abc'

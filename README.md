setup the ssh proxy
===================

```bash
# install required (Ubuntu) packages
apt install python-virtualenv openssh-server

# create a user (default: hilfmir)
useradd --no-user-group --gid nogroup --create-home --shell /bin/bash hilfmir

# become this user and prepare .ssh directory
su - hilfmir
mkdir -v -m 0700 .ssh
touch .ssh/authorized_keys

# clone the repo
git clone https://github.com/pabra/hilfmir.git hilfmir
cd hilfmir
```


add helper
==========

on the helper machine
---------------------

```bash
# the helper only needs an ssh and vnc client
apt install openssh-client xvnc4viewer

# prepare .ssh directory
[ ! -d ~/.ssh ] && mkdir -v -m 0700 ~/.ssh && touch ~/.ssh/authorized_keys

# generate a new key if required
ssh-keygen -b 2048 -t rsa -C "${USER} as hilfmir helper" -N "" -f ~/.ssh/helper
```

the ~/.ssh/config
```ssh_config
# you may want to add these lines at the top (optional)
# enable connection sharing
ControlMaster auto
# setup socket for shared connection
ControlPath ~/.ssh/sock-%r@%h:%p
# send keep alive messages
ServerAliveInterval 120
# use local agent on remote
ForwardAgent yes

# add the hilfmir ssh proxy (required)
Host hilfmir-ssh-proxy
    Hostname <actual-ssh-proxy-hostname>
    Port 22
    User hilfmir
    IdentityFile ~/.ssh/helper
    IdentitiesOnly yes
```

on the ssh proxy
----------------

Create/add an entry in the authorized_key file of user `hilfmir` at the ssh proxy.
```
restrict,port-forwarding,command="/bin/false" <ssh-rsa public_key> USERNAME as hilfmir helper
```


add help seeker
===============

on the help seeker machine
--------------------------

```bash
# install dependencies
apt install openssh-server x11vnc

# prepare .ssh directory
[ ! -d ~/.ssh ] && mkdir -v -m 0700 ~/.ssh && touch ~/.ssh/authorized_keys

# generate a new ssh key
ssh-keygen -b 2048 -t rsa -C "${USER} as hilfmir help seeker" -N "" -f ~/.ssh/help_seeker

# add one line per helper public key in ~/.ssh/authorized_keys
```

the ~/.ssh/config
```ssh_config
# add the hilfmir ssh proxy (required)
Host hilfmir-seeker-ssh-proxy
    Hostname <actual-ssh-proxy-hostname>
    Port 22
    User hilfmir
    RemoteForward localhost:41300 localhost:22
    IdentityFile ~/.ssh/help_seeker
    IdentitiesOnly yes
```

on the ssh proxy
----------------

Create/add an entry in the authorized_key file of user `hilfmir` at the ssh proxy.
```
restrict,port-forwarding,command="/bin/false" <ssh-rsa public_key> USERNAME as hilfmir help seeker on port 41300
```

on the helper machine
---------------------

add an entry to your ~/.ssh/config
```ssh_config
Host <help-seeker-name>
    ProxyCommand ssh hilfmir-ssh-proxy -W %h:%p
    User <USER>
    HostName localhost
    Port 41300
    IdentityFile ~/.ssh/helper
    IdentitiesOnly yes
```

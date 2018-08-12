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

# setup virtual environment for Python 3
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install -r requirements.txt

# run initial setup
./proxy.py init
```

FROM ubuntu:18.04

RUN apt-get update \
    && apt-get install -y \
        openssh-server \
        python-virtualenv \
        git \
        bind9-host \
        iputils-ping \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -v /run/sshd

CMD ["/usr/sbin/sshd", "-D"]

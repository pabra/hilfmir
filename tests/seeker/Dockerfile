FROM ubuntu:18.04

RUN apt-get update \
    && apt-get install -y \
        openssh-server \
        git \
        bind9-host \
        iputils-ping \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -v /run/sshd \
    && useradd -ms /bin/bash seeker

CMD ["/usr/sbin/sshd", "-D"]

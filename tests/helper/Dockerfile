FROM ubuntu:18.04

RUN apt-get update \
    && apt-get install -y \
        openssh-client \
        git \
        bind9-host \
        iputils-ping \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash helper

CMD ["/bin/sh"]

FROM ubuntu:18.04

RUN apt-get update \
    && apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        software-properties-common \
        python3-pip \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    && apt-key fingerprint 0EBFCD88 | grep -E '9DC8\s+5822\s+9FC7\s+DD38\s+854A\s+E2D8\s+8D81\s+803C\s+0EBF\s+CD88' \
    && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    && apt-get update \
    && apt-get install -y \
        docker-ce \
    && pip3 install \
        docker-compose \
        pytest \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /hilfmir/tests

CMD ["pytest", "-vv", "--show-capture=all"]

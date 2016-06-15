FROM debian:jessie
MAINTAINER Tim Gerhard <t_gerhard10@cs.uni-kl.de>

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  ca-certificates libssl-dev libsnappy-dev curl sudo file busybox gcc && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain nightly
ENV PATH "/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
RUN ln -s /root/.cargo /.cargo && ln -s /root/.multirust /.multirust

ADD code/ /code/
WORKDIR /code/service

ADD init.sh /init.sh
ADD inittab /etc/inittab
ADD server.sh /code/server.sh

RUN mkdir -p /config /logs /data \
    && ln -s /config /etc/tomato \
    && ln -s /logs /var/log/tomato \
    && ln -s /data /var/lib/tomato

ENV PYTHONUNBUFFERED 0
ENV TIMEZONE UTC
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

VOLUME ["/config", "/logs", "/code", "/data", "/root/.cargo/registry", "/code/service/target"]

CMD ["busybox", "init"]

FROM debian:jessie
MAINTAINER Dennis Schwerdel <schwerdel@googlemail.com>

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  python python-pip build-essential python-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install mongoengine

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  python-openssl bittorrent busybox \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /config /logs /code /data/templates \
    && ln -s /config /etc/tomato \
    && ln -s /logs /var/log/tomato \
    && ln -s /data /var/lib/tomato

ADD code/ /code/
ADD init.sh /init.sh
ADD inittab /etc/inittab

VOLUME ["/config", "/logs", "/code", "/data"]
EXPOSE 8000 8001 8002

CMD ["busybox", "init"]

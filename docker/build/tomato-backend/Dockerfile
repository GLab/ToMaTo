FROM debian:jessie
MAINTAINER Dennis Schwerdel <schwerdel@googlemail.com>

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  python python-pip build-essential python-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install mongoengine\>=0.10,\<0.11 pymongo\>=3.0,\<3.1 ujson\>=1,\<2

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

ENV PYTHONUNBUFFERED 0

VOLUME ["/config", "/logs", "/code", "/data"]
EXPOSE 8000 8001 8002 8010 8011 8012 8013 8014 8015 8016 8017 8018 8019 8020

CMD ["busybox", "init"]

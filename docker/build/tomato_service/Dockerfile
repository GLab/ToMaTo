FROM debian:jessie
MAINTAINER Dennis Schwerdel <schwerdel@googlemail.com>

RUN echo "deb http://httpredir.debian.org/debian unstable main" >> /etc/apt/sources.list
ADD 01pinning /etc/apt/preferences.d/01pinning

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  ca-certificates libssl-dev build-essential python-dev pypy busybox locales libsnappy1 libsnappy-dev wget \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN rm /usr/bin/python; ln -s pypy /usr/bin/python
  
ADD get-pip.py /tmp/get-pip.py
RUN python /tmp/get-pip.py; rm /tmp/get-pip.py
  
RUN pip install mongoengine\>=0.10,\<0.11 pymongo\>=3.0,\<3.1 cryptography\<1.0 pyopenssl\<0.16 msgpack-python\<0.5 pyyaml

RUN mkdir -p /tmp/snappy; cd /tmp/snappy; \
    wget https://github.com/andrix/python-snappy/archive/ca913c70193441045f7c95ddcf0de419f195d0b6.tar.gz -O - | tar -xzv; \
    cd python-snappy-*; pip install . ; \
    cd /; rm -rf /tmp/snappy

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen; \
    /usr/sbin/locale-gen; \
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

RUN mkdir -p /config /logs /code /data \
    && ln -s /config /etc/tomato \
    && ln -s /logs /var/log/tomato \
    && ln -s /data /var/lib/tomato

ADD init.sh /init.sh
ADD inittab /etc/inittab

ENV PYTHONUNBUFFERED 0
ENV TIMEZONE UTC
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

VOLUME ["/config", "/logs", "/code", "/data"]
EXPOSE 8000

CMD ["busybox", "init"]

FROM tomato_service
MAINTAINER Dennis Schwerdel <schwerdel@googlemail.com>

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  bittorrent \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN cp -a /usr/lib/pymodules/python2.7/BitTorrent /usr/lib/pypy/dist-packages/

RUN mkdir -p /data/templates

ADD code/ /code/

EXPOSE 8000 8001 8002 8010 8011 8012 8013 8014 8015 8016 8017 8018 8019 8020
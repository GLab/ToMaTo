FROM tomato_service
MAINTAINER Dennis Schwerdel <schwerdel@googlemail.com>

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  aria2 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data/templates

ADD code/ /code/

EXPOSE 8000 8001 8002

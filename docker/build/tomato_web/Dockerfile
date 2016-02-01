FROM debian:jessie
MAINTAINER Dennis Schwerdel <schwerdel@googlemail.com>

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  python python-pip build-essential python-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install github3.py\>=0.9.4,\<0.10

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  python-openssl python-django apache2 libapache2-mod-wsgi busybox \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /config /code \
    && ln -s /config /etc/tomato

ADD code/ /code/
ADD init.sh /init.sh
ADD inittab /etc/inittab
ADD tomato-web.apache /etc/apache2/sites-available/tomato-web.conf

RUN a2ensite tomato-web; a2dissite 000-default; a2dismod mpm_event; a2enmod mpm_worker; a2enmod ssl; a2enmod rewrite

ENV PYTHONUNBUFFERED 0
ENV TIMEZONE UTC

VOLUME ["/config", "/code", "/var/log/apache2"]
EXPOSE 80 443

CMD ["busybox", "init"]

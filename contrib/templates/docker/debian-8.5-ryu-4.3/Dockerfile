FROM debian:8.5

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  python httpie python-pip python-lxml python-greenlet python-paramiko python-eventlet python-routes python-webob python-netaddr \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install --no-install-recommends -y \
  build-essential python-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade netaddr && pip install ryu==4.3 six==1.9

RUN DEBIAN_FRONTEND=noninteractive apt-get remove -y build-essential python-dev && apt-get -y autoremove

ADD prepare_vm.sh /prepare_vm.sh

RUN /prepare_vm.sh && rm /prepare_vm.sh


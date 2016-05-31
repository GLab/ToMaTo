# ToMaTo - Topology Management Tool

 The Topology Management Tool (ToMaTo) is a topology-centric network
testbed, giving researchers the possibility to run their software in
specifically designed virtual networking topologies. ToMaTo utilizes
Proxmox virtualization technology (OpenVZ and KVM), Tinc VPN and
Dummynet  ink emulation to organize virtual machines in virtual
topologies.

Homepage: http://www.tomato-lab.org

Copyright (c) 2010-2016 by the Integrated Communication Systems Lab
of the University of Kaiserslautern (http://www.icsy.de)

License: GNU Affero GPL 3 (see agpl-3.0.txt)


## Running ToMaTo

### Hostmanager
The hostmanager is the software that has to run on every node. To 
start it, run ```./server.py``` in the ```hostmanager``` directory

### Backend and Webfrontend
The backend is the central management of ToMaTo. It consists of
multiple services, each running in their own Docker container.
The webfrontend is one client of ToMaTo which provides a web 
interface to ToMaTo which can be used in the browser. It also runs 
in its own Docker container.

You can use the ```tomato-ctl``` tool in the ```docker/run```
directory. Use ```./tomato-ctl.py --help``` in order to learn more.  
In order to run the docker containers, you have to make the images 
by running ```make``` in the ```docker/build``` directory.


## Accessing ToMaTo

The default user is *admin* with the password *changeme*.

### Graphical User interface
You can access the ToMaTo webfrontend via your web browser, and
manage users from there.

### Command-Line Interface
You can also access an API shell by using the ```tomato``` tool in
the ```cli``` directory. Run ```./tomato.py --help``` to learn more
about how to connect. See [the API Tutorial](https://github.com/GLab/ToMaTo/wiki/APITutorial)
for more information about the API syntax.


## Testing changes
Testes are available in the ```test``` directory.
Run ```./automatic_testing.sh``` to automatically set up a new 
ToMaTo instance, register the hosts from ```testhosts.json``` and 
the templates from ```testtemplates.json```, run the tests, and stop
the ToMaTo test instance.
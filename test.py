# -*- coding: utf-8 -*-
from xml.dom import minidom

from glabnetem.topology import *

top = Topology( minidom.parse ( "example.xml" ) ) 
top.output()
top.deploy("deploy")

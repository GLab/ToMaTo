# Explicitly import all django models
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


from elements import Element #@UnusedImport
from elements.kvm import KVM, KVM_Interface #@UnusedImport
from elements.openvz import OpenVZ, OpenVZ_Interface #@UnusedImport
from elements.lxc import LXC, LXC_Interface #@UnusedImport
from connections import Connection #@UnusedImport
from connections.bridge import Bridge #@UnusedImport
from resources import Resource #@UnusedImport
from resources.template import Template #@UnusedImport
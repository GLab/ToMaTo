# -*- coding: utf-8 -*-
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

from lib import cmd #@UnresolvedImport
import threading
from resources import network

_enabled_bridges = [] #multiset containing all bridges which have ebtables entries. The number of entries is the current counter (see doc of add_bridge and delete_bridge)
lock = threading.Lock()

def _run_ebtables_cmd(bridge,add_bool):
    
    """
    Runs all ebtables commands to set up proper firewall.
    currently, this means filtering out DHCP_OFFERS, so that dhcp servers running on an element cannot set ip addresses outside the topology.
    The rule can either be added or deleted.
    
    Parameter *bridge*
      This is the bridge the rule will be applied to.
      
    Üarameter *add_bool*
      If True, the rule will be added. If False, the rule will be deleted.
    """
    
    add_delete = "-D"
    if add_bool:
        add_delete = "-A"
        
    cmd.run(["ebtables",
                 add_delete,"FORWARD",
                 
                 "--protocol","0x0800", #ipv4
                 
                 "--in-interface","!","eth+",
                 "--logical-in",bridge,
                 
                 "--ip-protocol","17", #udp
                 "--ip-source-port","67",
                 "--ip-destination-port","68"
                 
                 "-j","DROP"])
    
    
def add_bridge(bridge):
    """
    Every bridge has a counter how often it has been enabled. This counter is increased by 1 when calling this command.
    If the counter was 0 before running this command, ebtables entries will be added.If it reaches 0, the ebtables entries will be removed.
    
    Parameter *bridge*
      The bridge to be added.
    """
    with lock:
        if not bridge in _enabled_bridges:
            _run_ebtables_cmd(bridge, True)
        _enabled_bridges.append(bridge)
            
def remove_bridge(bridge):
    """
    Decreases the counter of the bridge by one (minimum 0).
    If it reaches 0, the ebtables entries will be removed.
    
    Parameter *bridge*
      The bridge to be removed.
    """
    with lock:
        if bridge in _enabled_bridges:
            _enabled_bridges.remove(bridge)
        if not bridge in _enabled_bridges:
            _run_ebtables_cmd(bridge, False)
            
            
def add_all_networks():
    """
    Iterate over all networks and add all bridges by these networks to the firewall.
    The counter of each bridge will then be equal to the number of occurences.
    Should be run on program startup.
    """
    for nw in network.getAll():
        add_bridge(nw.getBridge)
        
def remove_all_networks():
    """
    Iterate over all networks and remove them from the firewall.
    Should be run on program shutdown.
    """
    for nw in network.getAll():
        remove_bridge(nw.getBridge)
        
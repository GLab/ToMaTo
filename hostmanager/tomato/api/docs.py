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

from tomato import elements, connections

def _docFn(docstr):
    def wrapper(fn):
        def call():
            return docstr
        call.__doc__ = docstr
        call.__name__ = fn.__name__
        return call
    return wrapper

@_docFn(elements.kvmqm.DOC)
def DOC_ELEMENT_KVMQM():
    pass

@_docFn(elements.kvmqm.DOC_IFACE)
def DOC_ELEMENT_KVMQM_INTERFACE():
    pass


@_docFn(elements.openvz.DOC)
def DOC_ELEMENT_OPENVZ():
    pass

@_docFn(elements.openvz.DOC_IFACE)
def DOC_ELEMENT_OPENVZ_INTERFACE():
    pass


@_docFn(elements.repy.DOC)
def DOC_ELEMENT_REPY():
    pass

@_docFn(elements.repy.DOC_IFACE)
def DOC_ELEMENT_REPY_INTERFACE():
    pass


@_docFn(elements.external_network.DOC)
def DOC_ELEMENT_EXTERNAL_NETWORK():
    pass


@_docFn(elements.udp_tunnel.DOC)
def DOC_ELEMENT_UDP_TUNNEL():
    pass


@_docFn(elements.tinc.DOC)
def DOC_ELEMENT_TINC():
    pass


@_docFn(connections.bridge.DOC)
def DOC_CONNECTION_BRIDGE():
    pass

@_docFn(connections.fixed_bridge.DOC)
def DOC_CONNECTION_FIXED_BRIDGE():
    pass

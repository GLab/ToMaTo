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

from .. import elements, connections

def docs():
    return {
        "elements": dict([(name, cls.DOC) for name, cls in elements.TYPES.iteritems()]),
        "connections": {"default": connections.Connection.DOC},
    }

def _docFn(docstr):
    def wrapper(fn):
        def call():
            return docstr
        call.__doc__ = docstr
        call.__name__ = fn.__name__
        return call
    return wrapper
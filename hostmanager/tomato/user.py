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

from .db import *
from .generic import *

class User(Entity, BaseDocument):
	name = StringField(required=True) #@ReservedAssignment
	# elements: [Element]
	# connections: [Connection]
	# templates: [Template]
	# networks: [Network]

	ATTRIBUTES = {
		"id": IdAttribute(),
		"name": Attribute(field=name, schema=schema.String())
	}

	meta = {
		'ordering': ['name'],
		'indexes': [
			'name'
		]
	}


	@property
	def elements(self):
		from .elements import Element
		return Element.objects(owner=self)

	@property
	def connections(self):
		from .connections import Connection
		return Connection.objects(owner=self)

	@property
	def templates(self):
		from .resources.template import Template
		return Template.objects(owner=self)

	@property
	def networks(self):
		from .resources.network import Network
		return Network.objects(owner=self)

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

class CommandError(Exception):
	def __init__(self, hostname, command, errorCode, errorMessage, mustLog=True):
		self.command = command
		self.errorMessage = errorMessage
		self.hostname = hostname
		self.errorCode = errorCode
		self.mustLog = mustLog
	def __str__(self):
		return "Error executing command '%s' on %s: [%d] %s" % (self.command, self.hostname, self.errorCode, self.errorMessage)
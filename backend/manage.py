#!/usr/bin/env python

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

import os, sys

if __name__ == "__main__":
	opt = sys.argv[1]
	if opt in ("cleanup", "compilemessages", "convert_to_south", "createcachetable", \
			"makemessages", "runfcgi", "runserver", "startapp", "testserver"):
		print "This command is not supported in ToMaTo"
	else:
		os.environ['TOMATO_MAINTENANCE']="true"
		os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tomato.config")
		from django.core.management import execute_from_command_line
		execute_from_command_line(sys.argv)

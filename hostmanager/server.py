#!/usr/bin/python
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


def run():
	import tomato, time
	tomato.startFileserver()
	tomato.startRPCserver()
	try:
		while True:
			time.sleep(60)
	except KeyboardInterrupt:
		tomato.stopRPCserver()
		tomato.stopFileserver()

if __name__ == "__main__":
	import sys
	if len(sys.argv) == 1:
		run()
	elif sys.argv[1] == "--coverage":
		import coverage
		cov = coverage.coverage()
		cov.start()
		run()
		print "stop"
		cov.stop()
		sys.stdout = open("coverage.txt", "w")
		cov.report()
	elif sys.argv[1] == "--profile":
		import cProfile as profile
		profile.run("run()", "profile")
		import pstats
		stat = pstats.Stats("profile")
		stat.sort_stats("cum")
		sys.stderr = open("profile.txt", "w")
		stat.print_stats("tomato")
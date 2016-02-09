#!/usr/bin/env python
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

if __name__ == "__main__":
	import sys
	if len(sys.argv) == 1:
		from tomato import run
		run()
	elif sys.argv[1] == "--coverage":
		import coverage #@UnresolvedImport
		cov = coverage.coverage(source=["tomato", "tomato.lib"], omit=["tomato/migrations/*", "../shared/lib/*"])
		cov.start()
		from tomato import run
		run()
		cov.stop()
		cov.save()
		cov.html_report()
	elif sys.argv[1] == "--profile":
		import cProfile as profile
		import signal
		from tomato import run
		pr = profile.Profile()
		def stats(*args):
			pr.create_stats()
			pr.dump_stats("profile")
			pr.enable()
		signal.signal(signal.SIGUSR1, stats)
		pr.enable()
		run()
		pr.disable()
		pr.dump_stats("profile")
		import pstats
		stat = pstats.Stats("profile")
		stat.sort_stats("cum")
		sys.stderr = open("profile.txt", "w")
		stat.print_stats("tomato")

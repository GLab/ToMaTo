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

from tomato.host import run
import os

def exists(pid):
	return os.path.exists("/proc/%d" % pid)

def kill(pid, force=False):
	run(["kill", str(pid), "-9" if force else "-15"])
	
def jiffiesPerSecond():
	cpus = 0
	with open("/proc/stat") as fp:
		jiffies = sum(map(int, fp.readline().split()[1:]))
		while fp.readline().startswith("cpu"):
			cpus += 1
	with open("/proc/uptime") as fp:
		seconds = float(fp.readline().split()[0])
	return jiffies / seconds / cpus
	
def cputime(pid):
	with open("/proc/%d/stat" % pid) as fp:
		jiffies = sum(map(int, fp.readline().split()[13:17]))
	return jiffies/jiffiesPerSecond()

def memory(pid):
	with open("/proc/%d/stat" % pid) as fp:
		return int(fp.readline().split()[23]) * 4096
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

from . import run, CommandError
import os

def exists(pid):
	return os.path.exists("/proc/%d" % pid)

def kill(pid, force=False):
	try:
		run(["kill", "-s", "9" if force else "15", str(pid)])
	except CommandError:
		pass
	
def killTree(pid, force=False, tree=None):
	pid = int(pid)
	tree = tree or getTree()
	kill(pid, force)
	if pid in tree:
		for child in tree[pid]:
			killTree(child, force, tree)
	
def getTree():
	tree = {}
	for pid in [int(pid) for pid in os.listdir('/proc') if pid.isdigit()]:
		try:
			with open('/proc/%d/stat' % pid) as fp:
				stat = fp.readline()
				parent = int(stat.split()[3])
			tree[parent] = tree.get(parent, []) + [pid]
		except:
			pass #process terminated during scan
	return tree
	
_jiffiesPerSecond = None 	
def jiffiesPerSecond():
	global _jiffiesPerSecond
	if _jiffiesPerSecond:
		return _jiffiesPerSecond
	cpus = 0
	with open("/proc/stat") as fp:
		jiffies = sum(map(int, fp.readline().split()[1:]))
		while fp.readline().startswith("cpu"):
			cpus += 1
	with open("/proc/uptime") as fp:
		seconds = float(fp.readline().split()[0])
	_jiffiesPerSecond = jiffies / seconds / cpus 
	return jiffies / seconds / cpus
	
def cputime(pid):
	try:
		with open("/proc/%d/stat" % pid) as fp:
			jiffies = sum(map(int, fp.readline().split()[13:17]))
		return jiffies/jiffiesPerSecond()
	except:
		return 0

def memory(pid):
	try:
		with open("/proc/%d/stat" % pid) as fp:
			return int(fp.readline().split()[23]) * 4096
	except:
		return 0
	
class IoPolicy:
	Idle = 3
	BestEffort = 2
	Realtime = 1

def ionice(pid, policy, priority=4):
	run(["ionice", "-c", str(policy), "-n", str(priority), "-p", str(pid)])
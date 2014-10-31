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

import platform
import os
import time
import socket

from . import run, getDpkgVersionStr
import net
from ... import config
from ..lib.newcmd.util.cache import cached


external_hostname = "tomato-lab.org" # should also be pingable.
external_ip = "8.8.8.8"

@cached(timeout=None)
def cpuinfo():
	with open("/proc/cpuinfo", "r") as fp:
		bogomips = []
		models = []
		for line in fp:
			if line.startswith("bogomips"):
				bogomips.append(float(line.split()[2]))
			if line.startswith("model name"):
				models.append(line.split(":")[1].strip())
	return {"count": len(models), "bogomips_avg": sum(bogomips)/len(bogomips), "model": models[0]}

def meminfo():
	with open("/proc/meminfo", "r") as fp:
		data = {}
		for line in fp:
			key, value = line.split(":")
			data[key.lower()] = int(value.strip().split()[0])
		return {"total": data["memtotal"], "used": (data["memtotal"]-data["memfree"]-data["cached"]-data["buffers"])}
	
def loadavg():
	with open("/proc/loadavg", "r") as fp:
		return map(float, fp.readline().split()[:3])
	
def uptime():
	with open("/proc/uptime", "r") as fp:
		return float(fp.readline().split()[0])

@cached(timeout=24*3600)
def hostmanagerVersion():
	return getDpkgVersionStr("tomato-hostmanager") or "devel"

@cached(timeout=24*3600)
def updaterVersion():
	return getDpkgVersionStr("tomato-updater")

@cached(timeout=24*3600)
def system():
	pve_ver = getDpkgVersionStr("pve-manager")
	return {
		"kernel": platform.release(),
		"distribution": ("proxmox", pve_ver, "") if pve_ver else platform.dist(),
		"python": platform.python_version(),
		"processor": platform.machine()
	}

def diskinfo(path):
	out = run(["df", path])
	data = out.splitlines()[1].split()
	return {"total": data[1], "used": data[2], "free": data[3]}

def problems():
	problems = []
	
	#disk problems
	for disk in [config.DATA_DIR]:
		probs = diskproblems(disk)  
		if probs:
			problems.append("Disk: %s on %s" % (probs, disk))
			
	#/etc/vz/conf readable?
	if not os.access("/etc/vz/conf", os.F_OK):
		problems.append("Config: /etc/vz/conf does not exist")
	else:
		if not os.access("/etc/vz/conf", os.R_OK):
			problems.append("Config: /etc/vz/conf is not readable")
			
	#hostname resolvable?
	try:
		etchostname = socket.gethostname()
		try:
			hostnameip = socket.gethostbyname(etchostname)
		except:
			problems.append("Config: cannot resolve hostname from /etc/hostname")
	except:
		problems.append("Config: Cannot read own hostname")
		
	#try to resolve external_hostname
	try:
		ip = socket.gethostbyname(external_hostname)
	except:
		problems.append("Network: Cannot resolve %s" % external_hostname)
	
	#try to ping external_ip
	if not ping_test(external_ip):
		problems.append("Network: ping test to %s failed" % external_ip)
	
	return problems

def ping_test(ip_address): #return a boolean whether the test was successful
	return net.ping(ip_address, count=1)["received"] == 1

def diskproblems(path):
	testFile = os.path.join(path, ".test")
	testData = str(time.time())
	match = False
	try:
		with open(testFile, "w") as fp:
			fp.write(testData)
	except:
		return "Failed to write"
	try:
		with open(testFile, "r") as fp:
			match = fp.read() == testData
	except:
		return "Failed to read"
	try:
		os.unlink(testFile)
	except:
		return "Failed to delete"
	if not match:
		return "Read wrong data"
	return None
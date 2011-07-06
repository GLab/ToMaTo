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

import re, uuid

from tomato import config, generic
from tomato.lib import util

import fileutil, process, ifaceutil

def _qm(host, vmid, cmd, params=""):
	return host.execute("qm %s %d %s" % (cmd, vmid, params))

def _monitor(host, vmid, cmd, timeout=60):
	assert getState(host, vmid) == generic.State.STARTED, "VM must be running to access monitor"
	return host.execute("echo -e \"%(cmd)s\\n\" | socat - unix-connect:/var/run/qemu-server/%(vmid)d.mon; timeout %(timeout)d socat -u unix-connect:/var/run/qemu-server/%(vmid)d.mon - 2>&1 | dd count=0 2>/dev/null" % {"cmd": cmd, "vmid": vmid, "timeout": timeout})

def _imagePathDir(vmid):
	return "/var/lib/vz/images/%d" % vmid

def _imagePath(vmid):
	return _imagePathDir(vmid) + "/disk.qcow2"

def _translateKeycode(keycode):
	trans = {"enter": "ret", "\n": "ret", "return": "ret",
			"-": "minus", "+": "plus"}
	if len(keycode) == 1:
		if keycode.islower():
			return keycode
		if keycode.isupper():
			return "shift-%s" % keycode.lower()
	for (key, value) in trans.iteritems():
		if keycode == key:
			return value
	return keycode

def sendKeys(host, vmid, keycodes):
	return _monitor(host, vmid, "\n".join(map(lambda k: "sendkey %s 10" % _translateKeycode(k), keycodes)))

def getState(host, vmid):
	if not vmid:
		return generic.State.CREATED
	res = _qm(host, vmid, "status")
	if "running" in res:
		return generic.State.STARTED
	if "stopped" in res:
		return generic.State.PREPARED
	if "unknown" in res:
		return generic.State.CREATED
	assert False, "Unable to determine kvm state"

def useImage(host, vmid, image, move=False):
	assert fileutil.existsFile(host, image), "Image file does not exist"
	assert getState(host, vmid) == generic.State.PREPARED, "VM must be stopped to change image"
	_qm(host, vmid, "set", "--ide0 undef")
	imagePath = _imagePath(vmid)
	fileutil.mkdir(host, _imagePathDir(vmid))
	if move:
		fileutil.move(host, image, imagePath)
	else:
		fileutil.copy(host, image, imagePath)
	fileutil.chown(host, imagePath, "root:root")
	_qm(host, vmid, "set", "--ide0=local:%s/disk.qcow2" % vmid)
	assert fileutil.existsFile(host, imagePath)

def _vncPidfile(vmid):
	return "%s/vnc-%s.pid" % (config.REMOTE_DIR, vmid)

def vncRunning(host, vmid, port):
	return process.processRunning(host, _vncPidfile(vmid), "tcpserver")

def startVnc(host, vmid, port, password):
	assert getState(host, vmid) == generic.State.STARTED, "VM must be running to start vnc"
	assert process.portFree(host, port)
	host.execute("tcpserver -qHRl 0 0 %s qm vncproxy %s %s & echo $! > %s" % ( port, vmid, password, _vncPidfile(vmid) ))
	assert not process.portFree(host, port)

def stopVnc(host, vmid, port):
	process.killPidfile(host, _vncPidfile(vmid))
	assert process.portFree(host, port)
	
def _templatePath(name):
	return "/var/lib/vz/template/qemu/%s.qcow2" % name
	
def useTemplate(host, vmid, template):
	return useImage(host, vmid, _templatePath(template))

def setName(host, vmid, name):
	assert getState(host, vmid) != generic.State.CREATED, "VM must exist to change the name"
	_qm(host, vmid, "set", "--name \"%s\"" % name)

def addInterface(host, vmid, iface):
	assert getState(host, vmid) == generic.State.PREPARED, "VM must be stopped to add interfaces"
	iface_id = int(re.match("eth(\d+)", iface).group(1))
	# qm automatically connects ethN to vmbrN
	# if this bridge does not exist, kvm start fails
	if not ifaceutil.interfaceExists(host, "vmbr%d" % iface_id):
		ifaceutil.bridgeCreate(host, "vmbr%d" % iface_id)
	_qm(host, vmid, "set", "--vlan%d e1000" % iface_id)			
	
def deleteInterface(host, vmid, iface):
	assert getState(host, vmid) == generic.State.PREPARED, "VM must be stopped to remove interfaces"
	iface_id = int(re.match("eth(\d+)", iface).group(1))
	_qm(host, vmid, "set", "--vlan%d undef\n" % iface_id)			
		
def copyImage(host, vmid, file):
	assert getState(host, vmid) != generic.State.CREATED, "VM must be prepared"
	fileutil.copy(host, _imagePath(vmid), file)
	assert fileutil.existsFile(host, file)
		
def getDiskUsage(host, vmid):
	if getState(host, vmid) != generic.State.CREATED:
		return int(host.execute("[ -s %(path)s ] && stat -c %%s %(path)s || echo 0" % {"path": _imagePath(vmid)}))
	else:
		return 0
	
def getMemoryUsage(host, vmid):
	if getState(host, vmid) == generic.State.STARTED:
		return int(host.execute("( [ -s /var/run/qemu-server/%(vmid)s.pid ] && PROC=`cat /var/run/qemu-server/%(vmid)s.pid` && [ -e /proc/$PROC/stat ] && cat /proc/$PROC/stat ) 2>/dev/null | awk '{print ($24 * 4096)}' || echo 0" % {"vmid": vmid}))
	else:
		return 0
	
def waitForInterface(host, vmid, iface):
	util.waitFor(lambda :interfaceDevice(host, vmid, iface, failSilent=True))
	
def interfaceDevice(host, vmid, iface, failSilent=False):
	"""
	Returns the name of the host device for the given interface
	
	Note: Proxmox changes the names of the interface devices with every 
	release of qemu-server. Here the current list of naming schemes:
	qemu-server 1.1-22 vmtab1000i0 
	qemu-server 1.1-25 vmtab1000i0d0
	qemu-server 1.1-28 tap1000i0d0 or tap1000i0
	Due to this naming chaos the name must determined on the host with a
	command, so	this can only be determined for started devices.
		
	@param iface: interface object
	@type iface: generic.Interface
	@return: name of host device
	@rtype: string
	"""
	iface_id = re.match("eth(\d+)", iface).group(1)
	assert getState(host, vmid) == generic.State.STARTED, "Cannot determine KVM host device names when not running"
	names = host.execute("(cd /sys/class/net; ls -d vmtab%(vmid)si%(iface_id)s vmtab%(vmid)si%(iface_id)sd0 tap%(vmid)si%(iface_id)s tap%(vmid)si%(iface_id)sd0 2>/dev/null)" % { "vmid": vmid, "iface_id": iface_id }).strip().split()
	assert failSilent or len(names) == 1, "Failed to determine kvm interface name, got %d names: %s" % (len(names), names)
	return names[0] if len(names) == 1 else None

def create(host, vmid):
	assert getState(host, vmid) == generic.State.CREATED, "VM already exists"
	res = _qm(host, vmid, "create")
	assert getState(host, vmid) == generic.State.PREPARED, "Failed to create VM: %s" % res
	
def start(host, vmid):
	assert getState(host, vmid) == generic.State.PREPARED, "VM already running"
	res = _qm(host, vmid, "start")
	assert getState(host, vmid) == generic.State.STARTED, "Failed to start VM: %s" % res

def stop(host, vmid):
	assert getState(host, vmid) != generic.State.CREATED, "VM not running"
	res = _qm(host, vmid, "stop")
	assert getState(host, vmid) == generic.State.PREPARED, "Failed to stop VM: %s" % res

def destroy(host, vmid):
	assert getState(host, vmid) != generic.State.STARTED, "VM not stopped"
	res = _qm(host, vmid, "destroy")
	assert getState(host, vmid) == generic.State.CREATED, "Failed to destroy VM: %s" % res

def migrate(src_host, src_vmid, dst_host, dst_vmid, ifaces):
	assert getState(dst_host, dst_vmid) == generic.State.CREATED, "Destination VM already exists"
	state = getState(src_host, src_vmid)
	if state == generic.State.CREATED:
		#nothing to do
		return
	#create a tmp directory on both hosts
	src_tmp = "/tmp/%s" % uuid.uuid1()
	dst_tmp = "/tmp/%s" % uuid.uuid1()
	fileutil.mkdir(src_host, src_tmp)
	fileutil.mkdir(dst_host, dst_tmp)
	#create destination vm 
	create(dst_host, dst_vmid)
	#transfer vm disk image
	fileutil.copy(src_host, _imagePath(src_vmid), "%s/disk.qcow2" % src_tmp)
	fileutil.fileTransfer(src_host, "%s/disk.qcow2" % src_tmp, dst_host, "%s/disk.qcow2" % dst_tmp, direct=True)
	if state == generic.State.STARTED:
		#prepare rdiff before snapshot to save time
		src_host.execute("rdiff signature %(tmp)s/disk.qcow2 %(tmp)s/rdiff.sigs" % {"tmp": src_tmp})
		#create a memory snapshot on old host
		_monitor(src_host, src_vmid, "stop")
		_monitor(src_host, src_vmid, "savevm migrate", timeout=900)
		#stop vm
		stop(src_host, src_vmid)
		#create and transfer a disk image rdiff
		src_host.execute("rdiff -- delta %(tmp)s/rdiff.sigs %(disk)s - | gzip > %(tmp)s/disk.rdiff.gz" % {"tmp": src_tmp, "disk": _imagePath(src_vmid)})
		fileutil.fileTransfer(src_host, "%s/disk.rdiff.gz" % src_tmp, dst_host, "%s/disk.rdiff.gz" % dst_tmp)
		#patch disk image with the rdiff
		dst_host.execute("gunzip < %(tmp)s/disk.rdiff.gz | rdiff -- patch %(tmp)s/disk.qcow2 - %(tmp)s/disk-patched.qcow2" % {"tmp": dst_tmp})
		fileutil.move(dst_host,"%s/disk-patched.qcow2" % dst_tmp, "%s/disk.qcow2" % dst_tmp)			
	#use disk image on new host
	useImage(dst_host, dst_vmid, "%s/disk.qcow2" % dst_tmp)
	for iface in ifaces:
		addInterface(dst_host, dst_vmid, iface)
	if state == generic.State.STARTED:
		start(dst_host, dst_vmid)
		#restore snapshot
		_monitor(dst_host, dst_vmid, "stop")
		_monitor(dst_host, dst_vmid, "loadvm migrate", timeout=900)
		_monitor(dst_host, dst_vmid, "cont")
		_monitor(dst_host, dst_vmid, "delvm migrate", timeout=900)
	#destroy vm on old host
	destroy(src_host, src_vmid)
	#remove tmp directories
	fileutil.delete(src_host, src_tmp, recursive=True)
	fileutil.delete(dst_host, dst_tmp, recursive=True)
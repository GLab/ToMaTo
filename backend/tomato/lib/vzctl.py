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

import uuid

from tomato import generic, config, fault

import process, fileutil, ifaceutil, util, exceptions, decorators

@decorators.retryOnError(errorFilter=lambda x: isinstance(x, exceptions.CommandError) and x.errorCode==9 and "Container already locked" in x.errorMessage)
def _vzctl(host, vmid, cmd, params=[], timeout=None):
	cmd = "vzctl %s %d %s" % (util.escape(cmd), vmid, " ".join(map(util.escape, params)))
	if timeout:
		cmd = ("timeout -9 %d " % timeout) + cmd 
	return host.execute(cmd)

def execute(host, vmid, cmd):
	assert getState(host, vmid) == generic.State.STARTED, "VM must be running to execute commands on it"
	return _vzctl(host, vmid, "exec", [cmd])

def _imagePath(vmid):
	return "/var/lib/vz/private/%d" % vmid

def getState(host, vmid):
	assert vmid
	res = _vzctl(host, vmid, "status")
	if "exist" in res and "running" in res:
		return generic.State.STARTED
	if "exist" in res and "down" in res:
		return generic.State.PREPARED
	if "deleted" in res:
		return generic.State.CREATED
	assert False, "Unable to determine openvz state"

def _vncPidfile(vmid):
	return "%s/vnc-%d.pid" % (config.REMOTE_DIR, vmid)

def vncRunning(host, vmid, port):
	return process.processRunning(host, _vncPidfile(vmid), "vncterm")

def startVnc(host, vmid, port, password):
	assert getState(host, vmid) == generic.State.STARTED, "VM must be running to start vnc"
	if not process.portFree(host, port):
		process.killPortUser(host, port)
	host.execute("vncterm -timeout 0 -rfbport %d -passwd %s -c vzctl enter %d >/dev/null 2>&1 & echo $! > %s" % ( port, util.escape(password), vmid, _vncPidfile(vmid) ))		
	assert not process.portFree(host, port)

def stopVnc(host, vmid, port):
	process.killPidfile(host, _vncPidfile(vmid))
	process.killPortUser(host, port)
	assert process.portFree(host, port)
	
def _templatePath(name):
	return "/var/lib/vz/template/qemu/%s.qcow2" % name

def create(host, vmid, template):
	assert getState(host, vmid) == generic.State.CREATED, "VM already exists"
	res = _vzctl(host, vmid, "create", ["--ostemplate", template])
	assert getState(host, vmid) == generic.State.PREPARED, "Failed to create VM: %s" % res
	_vzctl(host, vmid, "set", ["--devices", "c:10:200:rw", "--capability",  "net_admin:on", "--save"])
	
def start(host, vmid):
	assert getState(host, vmid) == generic.State.PREPARED, "VM already running"
	res = _vzctl(host, vmid, "start", timeout=300)
	util.waitFor (lambda :getState(host, vmid) == generic.State.STARTED)
	assert getState(host, vmid) == generic.State.STARTED, "OpenVZ device failed to start: %s" % res

	assert getState(host, vmid) == generic.State.STARTED, "Failed to start VM: %s" % res
	execute(host, vmid, "while fgrep -q boot /proc/1/cmdline; do sleep 1; done")

def stop(host, vmid):
	assert getState(host, vmid) != generic.State.CREATED, "VM not running"
	res = _vzctl(host, vmid, "stop")
	assert getState(host, vmid) == generic.State.PREPARED, "Failed to stop VM: %s" % res

def destroy(host, vmid):
	assert getState(host, vmid) != generic.State.STARTED, "VM not stopped"
	res = _vzctl(host, vmid, "destroy")
	assert getState(host, vmid) == generic.State.CREATED, "Failed to destroy VM: %s" % res

def setUserPassword(host, vmid, password, username="root"):
	assert getState(host, vmid) != generic.State.CREATED, "VM not prepared"
	_vzctl(host, vmid, "set", ["--userpasswd", "%s:%s"  % (username, password),  "--save"])

def setHostname(host, vmid, hostname):
	assert getState(host, vmid) != generic.State.CREATED, "VM not prepared"
	_vzctl(host, vmid, "set", ["--hostname", "%s" % util.identifier(hostname), "--save"])

def deleteInterface(host, vmid, iface):
	assert getState(host, vmid) != generic.State.CREATED, "VM not prepared"
	_vzctl(host, vmid, "set", ["--netif_del", iface, "--save"])

def checkImage(host, path):
	assert host
	assert fileutil.existsFile(host, path)
	try:
		res = host.execute("tar -tzvf %s ./sbin/init" % util.escape(path))
		fault.check("0/0" in res, "Image contents not owned by root")
	except exceptions.CommandError, err:
		return err.errorMessage

def useImage(host, vmid, image, forceGzip=False):
	assert getState(host, vmid) == generic.State.PREPARED, "VM not prepared"
	assert fileutil.existsFile(host, image), "Image does not exist"
	dst = _imagePath(vmid)
	fileutil.delete(host, dst, recursive=True)
	fileutil.mkdir(host, dst)
	fileutil.unpackdir(host, image, dst, "-z" if forceGzip else "")

def copyImage(host, vmid, file, forceGzip=False):
	assert getState(host, vmid) != generic.State.CREATED, "VM must be prepared"
	fileutil.packdir(host, file, _imagePath(vmid), "--numeric-owner " + ("-z" if forceGzip else ""))
	assert fileutil.existsFile(host, file)

def getDiskUsage(host, vmid):
	state = getState(host, vmid)
	if state == generic.State.STARTED:
		return int(host.execute("grep -h -A 1 -E '^%d:' /proc/vz/vzquota | tail -n 1 | awk '{print $2}'" % vmid))*1024
	elif state == generic.State.PREPARED:
		return int(host.execute("du -sb %s | awk '{print $1}'" % _imagePath(vmid)))
	else:
		return 0
	
def getMemoryUsage(host, vmid):
	if getState(host, vmid) == generic.State.STARTED:
		return int(host.execute("grep -e '^[ ]*%d:' -A 20 /proc/user_beancounters | fgrep privvmpages | awk '{print $2}'" % vmid))*4*1024
	else:
		return 0

def interfaceDevice(vmid, iface):
	return "veth%s.%s" % ( vmid, iface )

def addInterface(host, vmid, iface):
	state = getState(host, vmid)
	assert state != generic.State.CREATED, "VM not prepared"
	_vzctl(host, vmid, "set", ["--netif_add", iface, "--save"])
	_vzctl(host, vmid, "set", ["--ifname", iface, "--host_ifname", interfaceDevice(vmid, iface), "--save"])
	if state == generic.State.STARTED:
		assert ifaceutil.interfaceExists(host, interfaceDevice(vmid, iface))

def migrate(src_host, src_vmid, dst_host, dst_vmid, template, ifaces):
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
	create(dst_host, dst_vmid, template)
	try:
		#transfer vm disk image
		copyImage(src_host, src_vmid, "%s/disk.tar" % src_tmp)
		fileutil.fileTransfer(src_host, "%s/disk.tar" % src_tmp, dst_host, "%s/disk.tar" % dst_tmp, compressed=True)
		if state == generic.State.STARTED:
			#prepare rdiff before snapshot to save time
			src_host.execute("rdiff signature %(tmp)s/disk.tar %(tmp)s/rdiff.sigs" % {"tmp": src_tmp})
			#create a memory snapshot on old host
			res = _vzctl(src_host, src_vmid, "chkpnt", ["--dumpfile",  "%s/openvz.dump" % src_tmp])
			assert fileutil.existsFile(src_host, "%s/openvz.dump" % src_tmp), "Failed to create snapshot: %s" % res
			try:
				fileutil.fileTransfer(src_host, "%s/openvz.dump" % src_tmp, dst_host, "%s/openvz.dump" % dst_tmp, compressed=True)
				#create and transfer a disk image rdiff
				copyImage(src_host, src_vmid, "%s/disk2.tar" % src_tmp)
				src_host.execute("rdiff -- delta %(tmp)s/rdiff.sigs %(disk)s - | gzip > %(tmp)s/disk.rdiff.gz" % {"tmp": src_tmp, "disk": "%s/disk2.tar" % src_tmp})
				fileutil.fileTransfer(src_host, "%s/disk.rdiff.gz" % src_tmp, dst_host, "%s/disk.rdiff.gz" % dst_tmp, direct=True)
				#patch disk image with the rdiff
				dst_host.execute("gunzip < %(tmp)s/disk.rdiff.gz | rdiff -- patch %(tmp)s/disk.tar - %(tmp)s/disk-patched.tar" % {"tmp": dst_tmp})
				fileutil.move(dst_host,"%s/disk-patched.tar" % dst_tmp, "%s/disk.tar" % dst_tmp)
			except:
				_vzctl(src_host, src_vmid, "restore", ["--dumpfile", "%s/openvz.dump" % src_tmp])
				raise
		#use disk image on new host
		useImage(dst_host, dst_vmid, "%s/disk.tar" % dst_tmp)
		for iface in ifaces:
			addInterface(dst_host, dst_vmid, iface)
		if state == generic.State.STARTED:
			try:
				#restore snapshot
				_vzctl(dst_host, dst_vmid, "restore", ["--dumpfile", "%s/openvz.dump" % dst_tmp])
				assert getState(dst_host, dst_vmid) == generic.State.STARTED
			except:
				_vzctl(src_host, src_vmid, "restore", ["--dumpfile", "%s/openvz.dump" % src_tmp])
				raise
	except:
		destroy(dst_host, dst_vmid)
		fileutil.delete(src_host, src_tmp, recursive=True)
		fileutil.delete(dst_host, dst_tmp, recursive=True)
		raise
	#destroy vm on old host
	destroy(src_host, src_vmid)
	#remove tmp directories
	fileutil.delete(src_host, src_tmp, recursive=True)
	fileutil.delete(dst_host, dst_tmp, recursive=True)

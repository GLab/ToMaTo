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

import exceptions, util

def fileTransfer(src_host, src_path, dst_host, dst_path, direct=False, compressed=False):
	if compressed:
		src = src_host.getHostServer().randomFilename()
		dst = dst_host.getHostServer().randomFilename()
		compress(src_host, src_path, src)
	else:
		if direct:
			src = src_path
			dst = dst_path
			mode = src_host.execute("stat -c %%a %s" % util.escape(src)).strip()
		else:
			dst = dst_host.getHostServer().randomFilename()
			src = src_host.getHostServer().randomFilename()
			copy(src_host, src_path, src)
	chmod(src_host, src, 644)
	url = src_host.getHostServer().downloadGrant(src, "file")
	res = fetch(dst_host, url, dst)
	assert existsFile(dst_host, dst), "Failure to transfer file: %s" % res
	if compressed:
		uncompress(dst_host, dst, dst_path)
		delete(dst_host, dst)
		delete(src_host, src)
	else:
		if not direct:
			copy(dst_host, dst, dst_path)
			delete(dst_host, dst)
			delete(src_host, src)
		else:
			chmod(src_host, src_path, mode)
			
def existsSocket(host, file):
	try:
		host.execute("[ -S %s ]" % util.escape(file))
		return True
	except exceptions.CommandError:
		return False

def existsFile(host, file):
	try:
		host.execute("[ -f %s ]" % util.escape(file))
		return True
	except exceptions.CommandError:
		return False
			
def existsDir(host, file):
	try:
		host.execute("[ -d %s ]" % util.escape(file))
		return True
	except exceptions.CommandError, exc:
		return False

def fetch(host, url, dst):
	return host.execute("curl -f -o %s %s; echo $?" % (util.escape(dst), util.escape(url)))

def move(host, src, dst):
	return host.execute("mv %s %s" % (util.escape(src), util.escape(dst)))
	
def copy(host, src, dst):
	return host.execute("cp -a %s %s" % (util.escape(src), util.escape(dst)))

def chown(host, file, owner, recursive=False):
	return host.execute("chown %s %s %s" % ("-r" if recursive else "", util.escape(owner), util.escape(file)))

def chmod(host, file, mode, recursive=False):
	return host.execute("chmod %s %s %s" % ("-r" if recursive else "", util.escape(mode), util.escape(file)))

def mkdir(host, dir):
	return host.execute("mkdir -p %s" % util.escape(dir))

def delete(host, path, recursive=False):
	assert path, "No file to delete"
	return host.execute("rm %s -f %s" % ("-r" if recursive else "", util.escape(path)))

def packdir(host, archive, dir, args=""):
	assert existsDir(host, dir), "Directory does not exist"
	if archive.endswith(".gz") and not "-z" in args:
		args = args + " -z"
	if archive.endswith(".bz2") and not "-j" in args:
		args = args + " -j"
	res = host.execute("tar -cf %s -C %s %s ." % (util.escape(archive), util.escape(dir), args))
	assert existsFile(host, archive), "Failed to pack directory: %s" % res
	return res

def unpackdir(host, archive, dir, args=""):
	assert existsFile(host, archive), "Archive does not exist"
	if archive.endswith(".gz") and not "-z" in args:
		args = args + " -z"
	if archive.endswith(".bz2") and not "-j" in args:
		args = args + " -j"
	return host.execute("tar -xf %s -C %s %s" % (util.escape(archive), util.escape(dir), args))

def compress(host, src, dst):
	assert existsFile(host, src)
	host.execute("gzip < %s > %s" % (util.escape(src), util.escape(dst)))
	assert existsFile(host, dst)
	
def uncompress(host, src, dst):
	assert existsFile(host, src)
	host.execute("gunzip < %s > %s" % (util.escape(src), util.escape(dst)))
	assert existsFile(host, dst)

def fileSize(host, path):
	try:
		return int(host.execute("wc -c %s" % util.escape(path)).split()[0])
	except:
		return None
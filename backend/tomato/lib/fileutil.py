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


def fileTransfer(src_host, src_path, dst_host, dst_path, direct=False, compressed=False):
	import hostserver
	if compressed:
		src = hostserver.randomFilename(src_host)
		dst = hostserver.randomFilename(dst_host)
		compress(src_host, src_path, src)
	else:
		if direct:
			src = src_path
			dst = dst_path
			mode = src_host.execute("stat -c %%a %s" % src).strip()
		else:
			dst = hostserver.randomFilename(dst_host)
			src = hostserver.randomFilename(src_host)
			copy(src_host, src_path, src)
	chmod(src_host, src, 644)
	url = hostserver.downloadGrant(src_host, src, "file")
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
			
def existsFile(host, file):
	return "exists" in host.execute("[ -f \"%s\" ] && echo exists" % file)
			
def existsDir(host, file):
	return "exists" in host.execute("[ -d \"%s\" ] && echo exists" % file)

def fetch(host, url, dst):
	return host.execute("curl -f -o \"%s\" \"%s\"; echo $?" % (dst, url))

def move(host, src, dst):
	return host.execute("mv \"%s\" \"%s\"" % (src, dst))
	
def copy(host, src, dst):
	return host.execute("cp -a \"%s\" \"%s\"" % (src, dst))

def chown(host, file, owner, recursive=False):
	return host.execute("chown %s \"%s\" \"%s\"" % ("-r" if recursive else "", owner, file))

def chmod(host, file, mode, recursive=False):
	return host.execute("chmod %s \"%s\" \"%s\"" % ("-r" if recursive else "", mode, file))

def mkdir(host, dir):
	return host.execute("mkdir -p \"%s\"" % dir)

def delete(host, path, recursive=False):
	assert path, "No file to delete"
	return host.execute("rm %s -f \"%s\"" % ("-r" if recursive else "", path))

def packdir(host, archive, dir, args=""):
	assert existsDir(host, dir), "Directory does not exist"
	if archive.endswith(".gz") and not "-z" in args:
		args = args + " -z"
	if archive.endswith(".bz2") and not "-j" in args:
		args = args + " -j"
	res = host.execute("tar -cf '%s' -C '%s' %s ." % (archive, dir, args))
	assert existsFile(host, archive), "Failed to pack directory: %s" % res
	return res

def unpackdir(host, archive, dir, args=""):
	assert existsFile(host, archive), "Archive does not exist"
	if archive.endswith(".gz") and not "-z" in args:
		args = args + " -z"
	if archive.endswith(".bz2") and not "-j" in args:
		args = args + " -j"
	return host.execute("tar -xf '%s' -C '%s' %s" % (archive, dir, args))

def compress(host, src, dst):
	assert existsFile(host, src)
	host.execute("gzip < '%s' > '%s'" % (src, dst))
	assert existsFile(host, dst)
	
def uncompress(host, src, dst):
	assert existsFile(host, src)
	host.execute("gunzip < '%s' > '%s'" % (src, dst))
	assert existsFile(host, dst)

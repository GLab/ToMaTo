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
import os, shutil

def exists(path):
	return os.path.exists(path)

def entries(path):
	return os.listdir(path)

def copy(src, dst):
	shutil.copyfile(src, dst)
	
def basename(path):
	return os.path.basename(path)

def readlink(path):
	return os.readlink(path)

def createDir(path, parents=True):
	if not parents:
		os.mkdir(path)
	else:
		os.makedirs(path)
		
def remove(path, recursive=False):
	if recursive and os.path.isdir(path):
		shutil.rmtree(path)
	else:
		os.remove(path)
	
def extractArchive(src, dst, opts=[]):
	run(["tar", "-axf", src] + opts + ["-C", dst])

def diskspace(path):
	if not exists(path):
		return 0
	out = run(["du", "-sb", path])
	return int(out.split()[0])

def filesize(path):
	return os.path.getsize(path)
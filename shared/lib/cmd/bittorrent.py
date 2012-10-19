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

from tomato.lib.cmd import run, spawn, CommandError, process
import os, atexit

def startTracker(port, path):
	assert os.path.exists(path)
	usage = run(["bttrack"])
	args = ["bttrack", "--port", str(port), "--dfile", os.path.join(path, "tracker.cache"), "--logfile", os.path.join(path, "tracker.log")]
	#args = ["bttrack", "--port", str(port), "--dfile", os.path.join(path, "tracker.cache"), "--allowed_dir", path, "--logfile", os.path.join(path, "tracker.log")]
	#if "--parse_allowed_interval" in usage: #bittorrent
	#	args += ["--parse_allowed_interval", "1"] #minutes
	#elif "--parse_dir_interval" in usage: #bittornado
	#	args += ["--parse_dir_interval", "60"] #seconds
	pid = spawn(args)
	atexit.register(lambda :process.kill(pid))

def startClient(path, bwlimit=10000):
	print path
	assert os.path.exists(path)
	pid = spawn(["btlaunchmany", ".", "--max_upload_rate", str(bwlimit)], cwd=path, daemon=False)
	atexit.register(lambda :process.kill(pid))

def createTorrent(tracker, dataPath, torrentPath=""):
	assert os.path.exists(dataPath)
	return run(["btmakemetafile", tracker, dataPath, "--target", torrentPath])
	
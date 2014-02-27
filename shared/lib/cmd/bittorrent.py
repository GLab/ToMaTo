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

from . import run, spawn, CommandError, process
from .. import util
from ... import config
import os

_clientPid = None
_clientConfig = {}
_trackerPid = None

def startTracker(port, path):
	global _trackerPid
	if _trackerPid:
		return
	assert os.path.exists(path)
	usage = run(["bttrack"])
	args = ["bttrack", "--port", str(port), "--dfile", os.path.join(path, "tracker.cache"), "--allowed_dir", path]
	if "--parse_allowed_interval" in usage: #bittorrent
		args += ["--parse_allowed_interval", "1"] #minutes
	elif "--parse_dir_interval" in usage: #bittornado
		args += ["--parse_dir_interval", "60"] #seconds
	_trackerPid = spawn(args)

def stopTracker():
	global _trackerPid
	process.kill(_trackerPid)
	_trackerPid = None

def torrentInfo(torrentData):
	from BitTorrent.bencode import bdecode
	info = bdecode(torrentData)["info"]
	return info

def fileSize(torrentData):
	info = torrentInfo(torrentData)
	if info.has_key('length'):
		return info["length"]
	file_length = 0
	for file in info['files']:
		path = ''
		for item in file['path']:
			if (path != ''):
				path = path + "/"
			path = path + item
		file_length += file['length']
	return file_length
	
def startClient(path, bwlimit=10000):
	global _clientPid, _clientConfig
	if _clientPid:
		return
	assert os.path.exists(path)
	_clientConfig = {"path": path, "bwlimit": bwlimit} 
	_clientPid = spawn(["btlaunchmany", ".", "--max_upload_rate", str(bwlimit)], cwd=path, daemon=False)
	try:
		process.ionice(_clientPid, process.IoPolicy.Idle)
	except:
		pass #no essential command

def restartClient():
	global _clientPid, _clientConfig
	if _clientPid:
		stopClient()
		startClient(**_clientConfig)

def stopClient():
	global _clientPid
	process.kill(_clientPid)
	_clientPid = None

def createTorrent(tracker, dataPath, torrentPath=""):
	assert os.path.exists(dataPath)
	return run(["btmakemetafile", tracker, dataPath, "--target", torrentPath])

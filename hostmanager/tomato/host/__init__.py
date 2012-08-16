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

import subprocess, os, hashlib, shutil

DEVNULL = open("/dev/null", "w")

def runUnchecked(cmd, shell=False, ignoreErr=False, input=None):
    stderr = DEVNULL if ignoreErr else subprocess.STDOUT
    stdin = subprocess.PIPE if input else None
    proc=subprocess.Popen(cmd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr, shell=shell, close_fds=True)
    res=proc.communicate(input)
    return (proc.returncode,res[0])

class CommandError(Exception):
    def __init__(self, command, errorCode, errorMessage, mustLog=True):
        self.command = command
        self.errorMessage = errorMessage
        self.errorCode = errorCode
        self.mustLog = mustLog
    def __str__(self):
        return "Error executing command '%s': [%d] %s" % (self.command, self.errorCode, self.errorMessage)

def spawn(cmd):
    #setsid is important, otherwise programs will be killed when the parent process closes
    cmd = ["setsid"] + cmd
    proc=subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT, close_fds=True)
    return proc.pid

def spawnShell(cmd):
    #setsid is important, otherwise programs will be killed when the parent process closes
    cmd = "setsid " + cmd
    proc=subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT, shell=True, close_fds=True)
    return proc.pid

def kill(pid, force=None):
    try:
        os.kill(pid, 9 if force else 15)
    except OSError:
        pass

def run(cmd, **kwargs):
    error, output = runUnchecked(cmd, **kwargs)
    if error:
        raise CommandError(" ".join(cmd), error, output)
    return output

def runShell(cmd, **kwargs):
    return run(cmd, shell=True, **kwargs)
   

def removeControlChars(s):
    #allow TAB=9, LF=10, CR=13
    controlChars = "".join(map(chr, range(0,9)+range(11,13)+range(14,32)))
    return s.translate(None, controlChars)

def getDpkgVersion(package):
    fields = {}
    error, output = runUnchecked(["dpkg-query", "-s", package])
    if error:
        return None 
    for line in output.splitlines():
        if ": " in line:
            name, value = line.split(": ")
            fields[name.lower()] = value
    if not "installed" in fields["status"]:
        return None
    verStr = fields["version"]
    version = []
    numStr = ""
    for ch in verStr:
        if ch in "0123456789":
            numStr += ch
        if ch in ".:-":
            version.append(int(numStr))
            numStr = ""
    version.append(int(numStr))
    return version

def escape(s):
    return repr(unicode(s).encode("utf-8"))

def identifier(s, allowed="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_.", subst="_"):
    ret=""
    for ch in s:
        if ch in allowed:
            ret += ch
        elif subst:
            ret += subst
    return ret

def randomPassword():
    return hashlib.md5(os.urandom(8)).hexdigest()

class Path:
    def __init__(self, path):
        self.path = path
    def exists(self):
        return os.path.exists(self.path)
    def subPath(self, path):
        return Path(os.path.join(self.path, path))
    def entries(self):
        return map(Path, os.listdir(self.path))
    def entryNames(self):
        return os.listdir(self.path)
    def copyTo(self, path):
        if isinstance(path, Path):
            path = path.path
        shutil.copyfile(self.path, path)
    def basename(self):
        return os.path.basename(self.path)
    def readlink(self):
        return Path(os.readlink(self.path))
    def createDir(self, parents=True):
        if not parents:
            os.mkdir(self.path)
        else:
            os.makedirs(self.path)
    def remove(self, recursive=False):
        if recursive:
            shutil.rmtree(self.path)
        else:
            os.remove(self.path)
    
class Archive(Path):
    # not using module tarfile as it is not safe
    def extractTo(self, dst):
        if isinstance(dst, Path):
            dst = dst.path
        run(["tar", "-axf", self.path, "-C", dst])

class Interface:
    def __init__(self, name):
        self.name = name
    def _sysPath(self):
        return Path("/sys/class/net/%s" % self.name)
    def exists(self):
        return self._sysPath().exists()
    def linkConfig(self, options=[]):
        run(["ip", "link", "set", self.name]+options)
    def up(self):
        self.linkConfig(["up"])
    def down(self):
        self.linkConfig(["down"])
    def getBridge(self):
        brlink = self._sysPath().subPath("brport/bridge")
        if not brlink.exists():
            return None
        return Bridge(brlink.readlink().basename())
    
class Bridge(Interface):
    def _brifPath(self):
        return self._sysPath().subPath("brif")
    def exists(self):
        return self._brifPath().exists()
    def create(self):
        run(["brctl", "addbr", self.name])
    def interfaceNames(self):
        assert self.exists()
        return self._brifPath().entryNames()
    def interfaces(self):
        return map(Interface, self.interfaceNames())
    def remove(self):
        assert not self.interfaces()
        assert self.exists()
        self.down()
        run(["brctl", "delbr", self.name])
    def addInterface(self, iface):
        assert self.exists()
        assert isinstance(iface, Interface)
        assert iface.exists()
        run(["brctl", "addif", self.name, iface.name])
    def removeInterface(self, iface):
        assert self.exists()
        assert isinstance(iface, Interface)
        assert iface.exists()
        run(["brctl", "delif", self.name, iface.name])
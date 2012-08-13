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

def runUnchecked(cmd, shell=False):
    proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell, close_fds=True)
    res=proc.communicate()
    return (proc.returncode,res[0])

class CommandError(Exception):
    def __init__(self, command, errorCode, errorMessage, mustLog=True):
        self.command = command
        self.errorMessage = errorMessage
        self.errorCode = errorCode
        self.mustLog = mustLog
    def __str__(self):
        return "Error executing command '%s': [%d] %s" % (self.command, self.errorCode, self.errorMessage)

def spawn(cmd, shell=False):
    proc=subprocess.Popen(cmd, shell=shell, close_fds=True)
    return proc.pid

def kill(pid, force=None):
    os.kill(pid, 9 if force else 15)

def run(cmd):
    error, output = runUnchecked(cmd, False)
    if error:
        raise CommandError(" ".join(cmd), error, output)
    return output

def runShell(cmd):
    error, output = runUnchecked([cmd], True)
    if error:
        raise CommandError(cmd, error, output)
    return output
   

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
        shutil.copyfile(self.path, path)

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
    
class Bridge(Interface):
    def _brifPath(self):
        return self._sysPath().subPath("brif")
    def exists(self):
        return self._brifPath().exists()
    def create(self):
        run(["brctl", "addbr", self.name])
    def interfaces(self):
        assert self.exists()
        return map(Interface, self._brifPath().entryNames())
    def remove(self):
        assert not self.interfaces()
        assert self.exists()
        self.down()
        run(["brctl", "delbr", self.name])
    def addInterface(self, iface):
        assert self.exists()
        assert isinstance(iface, Interface)
        assert iface.exists()
        run(["brctl", "addif", iface])
    def removeInterface(self, iface):
        assert self.exists()
        assert isinstance(iface, Interface)
        assert iface.exists()
        run(["brctl", "delif", iface])
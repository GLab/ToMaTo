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

def runUnchecked(cmd, shell=False, ignoreErr=False, input=None, cwd=None): #@ReservedAssignment
    stderr = DEVNULL if ignoreErr else subprocess.STDOUT
    stdin = subprocess.PIPE if input else None
    proc=subprocess.Popen(cmd, cwd=cwd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr, shell=shell, close_fds=True)
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

def spawn(cmd, stdout=DEVNULL, daemon=True, cwd=None):
    proc=subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT, close_fds=True, preexec_fn=os.setsid if daemon else None)
    return proc.pid

def spawnShell(cmd, stdout=DEVNULL, daemon=True, cwd=None, useExec=True):
    if useExec:
        cmd = "exec " + cmd #important, so proc.pid matches the process and not only the shell
    proc=subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=subprocess.STDOUT, shell=True, close_fds=True, preexec_fn=os.setsid if daemon else None)
    return proc.pid

def run(cmd, **kwargs):
    try:
        error, output = runUnchecked(cmd, **kwargs)
    except Exception, exc:
        error, output = True, repr(exc)
    if error:
        raise CommandError(" ".join(cmd), error, output)
    return output

def runShell(cmd, **kwargs):
    return run(cmd, shell=True, **kwargs)
   

def removeControlChars(s):
    #allow TAB=9, LF=10, CR=13
    controlChars = "".join(map(chr, range(0,9)+range(11,13)+range(14,32)))
    return s.translate(None, controlChars)

def getDpkgVersionStr(package):
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
    return fields["version"]

def splitVersion(verStr):
    version = []
    numStr = ""
    if not verStr:
        return verStr
    for ch in verStr:
        if ch in "0123456789":
            numStr += ch
        if ch in ".:-":
            version.append(int(numStr))
            numStr = ""
    version.append(int(numStr))
    return version
    

def getDpkgVersion(package, verStr=None):
    verStr = getDpkgVersionStr(package)
    return splitVersion(verStr)

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
from . import Error 
from util import run, CommandError, cmd

class DpkgError(Error):
	CATEGORY="cmd_dpkg"
	TYPE_UNKNOWN="unknown"
	TYPE_UNSUPPORTED="unsupported"
	TYPE_UNKNOWN_PACKAGE="unknown_package" # not installed packages are unknown
	TYPE_NOT_INSTALLED="not_installed"
	def __init__(self, type, message, data=None):
		Error.__init__(self, category=DpkgError.CATEGORY, type=type, message=message, data=data)

def _packageInfo(package):
	fields = {}
	try:
	 	output = run(["dpkg-query", "-s", package])
	except CommandError, err:
		if err.code == 1:
			raise DpkgError(DpkgError.TYPE_UNKNOWN_PACKAGE, "Package %r is unknown (not installed)" % package, {"package": package, "error": err})
		else:
			raise DpkgError(DpkgError.TYPE_UNKNOWN, "Failed to execute dpkg-query: %s" % err, {"package": package, "error": err}) 
	for line in output.splitlines():
		if ": " in line:
			name, value = line.split(": ")
			fields[name.lower()] = value
	return fields

def _isInstalled(info):
	return "installed" in info["status"]	

def _check():
	DpkgError.check(cmd.exists("dpkg-query"), DpkgError.TYPE_UNSUPPORTED, "Binary dpkg-query does not exist")
	return True

def _public(method):
	def call(*args, **kwargs):
		_check()
		return method(*args, **kwargs)
	call.__name__ = method.__name__
	call.__doc__ = method.__doc__
	return call

def checkSupport():
	return _check()

@_public
def isInstalled(package):
	try:
		info = _packageInfo(package)
	except DpkgError, err:
		if err.type == DpkgError.TYPE_UNKNOWN_PACKAGE:
			return False
		else:
			raise
	return _isInstalled(info)

@_public
def getVersionStr(package):
	info = _packageInfo(package)
	DpkgError.check(_isInstalled(info), DpkgError.TYPE_NOT_INSTALLED, "Package is not installed: %s" % package, {"package": package})
	return info["version"]

@_public
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
    
def getVersion(package):
    return splitVersion(getVersionStr(package))


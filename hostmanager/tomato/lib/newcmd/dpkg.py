from . import Error, SUPPORT_CHECK_PERIOD
from util import run, CommandError, cmd, cache


class DpkgError(Error):
	CODE_UNKNOWN = "dpkg.unknown"
	CODE_UNSUPPORTED = "dpkg.unsupported"
	CODE_UNKNOWN_PACKAGE = "dpkg.unknown_package"  # not installed packages are unknown
	CODE_NOT_INSTALLED = "dpkg.not_installed"


def _packageInfo(package):
	fields = {}
	try:
		output = run(["dpkg-query", "-s", package])
	except CommandError, err:
		if err.code == 1:
			raise DpkgError(DpkgError.CODE_UNKNOWN_PACKAGE, "Package is unknown (not installed)",
				{"package": package, "error": err})
		else:
			raise DpkgError(DpkgError.CODE_UNKNOWN, "Failed to execute dpkg-query",
				{"package": package, "error": err})
	for line in output.splitlines():
		if ": " in line:
			name, value = line.split(": ")
			fields[name.lower()] = value
	return fields


def _isInstalled(info):
	return "installed" in info["status"]

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	DpkgError.check(cmd.exists("dpkg-query"), DpkgError.CODE_UNSUPPORTED, "Binary dpkg-query does not exist")
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
		if err.type == DpkgError.CODE_UNKNOWN_PACKAGE:
			return False
		else:
			raise
	return _isInstalled(info)


@_public
def getVersionStr(package):
	info = _packageInfo(package)
	DpkgError.check(_isInstalled(info), DpkgError.CODE_NOT_INSTALLED, "Package is not installed", {"package": package})
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


from . import Error, SUPPORT_CHECK_PERIOD
from util import params, cmd, cache
import os

class Aria2Error(Error):
	CODE_UNKNOWN="aria2.unknown"
	CODE_UNSUPPORTED="aria2.unsupported"
	CODE_DEST_PATH_DOES_NOT_EXIST="aria2.dest_path_does_not_exist"


@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def isSupported():
	return cmd.exists("aria2c")

def _check():
	Aria2Error.check(isSupported(), Aria2Error.CODE_UNSUPPORTED, "Binary aria2c does not exist")
	return True

def _public(method):
	def call(*args, **kwargs):
		_check()
		return method(*args, **kwargs)
	call.__name__ = method.__name__
	call.__doc__ = method.__doc__
	return call

######################
### Public methods ###
######################

def checkSupport():
	return _check()

@_public
def download(urls, dest, hash=None):
	urls = params.convert(urls, convert=list)
	dest = params.convert(dest, convert=os.path.realpath)
	hash = params.convert(hash, convert=str, null=True)
	path, fname = os.path.split(dest)
	Aria2Error.check(os.path.exists(path), Aria2Error.CODE_DEST_PATH_DOES_NOT_EXIST, "Destination path does not exit", {"path": path})
	args = ["aria2c", "-d", path, "-o", fname, "-c", "-V", "--auto-file-renaming=false", "--allow-overwrite=true"]
	if hash:
		args.append("--checksum=%s" % hash)
	args += urls
	cmd.run(args)
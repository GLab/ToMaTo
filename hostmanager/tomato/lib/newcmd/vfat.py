import os
from . import Error, SUPPORT_CHECK_PERIOD
from util import params, cmd, cache

class VFatError(Error):
	CODE_UNKNOWN="vfat.unknown"
	CODE_UNSUPPORTED="vfat.unsupported"
	CODE_ALREADY_MOUNTED="vfat.already_mounted"
	CODE_ALREADY_UNMOUNTED="vfat.already_unmounted"
	CODE_FAILED_TO_CREATE="vfat.failed_to_create"
	CODE_FAILED_TO_MOUNT="vfat.failed_to_mount"
	CODE_FAILED_TO_UNMOUNT="vfat.failed_to_unmount"
	CODE_FAILED_TO_READ_MOUNTS="vfat.failed_to_read_mounts"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	VFatError.check(cmd.exists("mkfs.vfat"), VFatError.CODE_UNSUPPORTED, "Binary mkfs.vfat does not exist")
	return True

def _public(method):
	def call(*args, **kwargs):
		_check()
		return method(*args, **kwargs)
	call.__name__ = method.__name__
	call.__doc__ = method.__doc__
	return call

def _isMounted(path):
	try:
		with open('/proc/mounts') as fp:
			mounts = fp.readlines()
		for mount in mounts:
			if path == mount.split()[1]:
				return True
		return False
	except Exception, err:
		raise VFatError(VFatError.CODE_FAILED_TO_READ_MOUNTS, "Failed to read mounts", {"error": err})

######################
### Public methods ###
######################

def checkSupport():
	return _check()

@_public
def isMounted(path):
	path = params.convert(path, convert=os.path.realpath, check=os.path.exists)
	return _isMounted(path)

@_public
def create(path, size):
	path = params.convert(path, convert=os.path.realpath, check=lambda p: not os.path.exists(p))
	size = params.convert(size, convert=int, gte=1)
	try:
		cmd.run(["mkfs.vfat", "-C", path, str(size)])
	except cmd.CommandError, err:
		raise VFatError(VFatError.CODE_FAILED_TO_CREATE, "Failed to create image", {"path": path, "size": size, "error": repr(err)})

@_public
def mount(image, path, sync=False, readOnly=False):
	image = params.convert(image, convert=str, check=os.path.exists)
	path = params.convert(path, convert=os.path.realpath, check=os.path.exists)
	VFatError.check(not _isMounted(path), VFatError.CODE_ALREADY_MOUNTED, "Path is already mounted", {"path": path})
	options = ["loop"]
	if sync:
		options.append("sync")
	if readOnly:
		options.append("ro")
	try:
		cmd.run(["mount", "-o%s" % ",".join(options), image, path])
	except cmd.CommandError, err:
		raise VFatError(VFatError.CODE_FAILED_TO_MOUNT, "Failed to mount image", {"path": path, "image": image, "options": options, "error": repr(err)})

@_public
def unmount(path, ignoreUnmounted=False):
	path = params.convert(path, convert=os.path.realpath, check=os.path.exists)
	if not _isMounted(path):
		if ignoreUnmounted:
			return
		raise VFatError(VFatError.CODE_ALREADY_UNMOUNTED, "Path is already unmounted", {"path": path})
	try:
		cmd.run(["umount", path])
	except cmd.CommandError, err:
		raise VFatError(VFatError.CODE_FAILED_TO_UNMOUNT, "Failed to unmount image", {"path": path, "error": repr(err)})

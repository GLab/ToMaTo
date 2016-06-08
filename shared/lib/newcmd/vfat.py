import os, re
from . import Error, SUPPORT_CHECK_PERIOD
from util import params, cmd, cache

class ImageError(Error):
	CODE_UNKNOWN="image.unknown"
	CODE_UNSUPPORTED="image.unsupported"
	CODE_ALREADY_MOUNTED="image.already_mounted"
	CODE_ALREADY_UNMOUNTED="image.already_unmounted"
	CODE_FAILED_TO_CREATE="image.failed_to_create"
	CODE_FAILED_TO_MOUNT="image.failed_to_mount"
	CODE_FAILED_TO_UNMOUNT="image.failed_to_unmount"
	CODE_FAILED_TO_READ_MOUNTS="image.failed_to_read_mounts"

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	for binary in ['mkfs.vfat', 'sfdisk', 'dd', 'losetup', 'partx']:
		ImageError.check(cmd.exists(binary), ImageError.CODE_UNSUPPORTED, "Binary %s does not exist" % binary)
	return True

def _public(method):
	def call(*args, **kwargs):
		_check()
		return method(*args, **kwargs)
	call.__name__ = method.__name__
	call.__doc__ = method.__doc__
	return call

def _mountedDevice(path):
	try:
		path = os.path.abspath(path)
		with open('/proc/mounts') as fp:
			mounts = fp.readlines()
		for mount in mounts:
			if path == mount.split()[1]:
				return mount.split()[0]
		return None
	except Exception, err:
		raise ImageError(ImageError.CODE_FAILED_TO_READ_MOUNTS, "Failed to read mounts", {"error": err})

def _isMounted(path):
	return bool(_mountedDevice(path))

def _getPartitions(path):
	output = cmd.run(["sfdisk", "-d", path])
	pat = re.compile('.*\s+start=\s*(\d+)\s*,\s*size=\s*(\d+)\s*,.*')
	partitions = []
	for p in output.splitlines():
		m = pat.match(p)
		if m:
			partitions.append(map(int, m.groups()))
	return partitions


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
def create(path, size, nested=False):
	path = params.convert(path, convert=os.path.realpath, check=lambda p: not os.path.exists(p))
	size = params.convert(size, convert=int, gte=8192)
	nested = params.convert(nested, convert=bool)
	try:
		cmd.run(["dd", "if=/dev/zero", "of=%s" % path, "bs=1k", "count=%d" % size])
		device = path
		if nested:
			cmd.run(["sfdisk", path], input=",\n")
			partitions = _getPartitions(path)
			start, size = partitions[0]
			start, size = start * 512, size * 512
			ImageError.check(start > 0 and size > 0, ImageError.CODE_FAILED_TO_CREATE, "Failed to create partition table", {"path": path, "table": partitions})
			device = cmd.run(["losetup", "-f", "--show", "--offset", str(start), "--sizelimit", str(size), path]).splitlines()[0]
			ImageError.check(os.path.exists(device), ImageError.CODE_FAILED_TO_CREATE, "Failed to bind to loop device", {"path": path, "size": size, "loop_device": device})
		cmd.run(["mkfs.vfat", device])
		cmd.run(["sync"])
		if nested:
			cmd.run(["losetup", "-d", device])
	except cmd.CommandError, err:
		raise ImageError(ImageError.CODE_FAILED_TO_CREATE, "Failed to create image", {"path": path, "size": size, "error": repr(err)})

@_public
def mount(image, path, sync=False, readOnly=False, partition=0):
	image = params.convert(image, convert=str, check=os.path.exists)
	path = params.convert(path, convert=os.path.realpath, check=os.path.exists)
	partition = params.convert(partition, convert=int, gte=0, lte=4)
	ImageError.check(not _isMounted(path), ImageError.CODE_ALREADY_MOUNTED, "Path is already mounted", {"path": path})
	options = ["loop"] if not partition else []
	if sync:
		options.append("sync")
	if readOnly:
		options.append("ro")
	try:
		if partition:
			partitions = _getPartitions(image)
			start, size = partitions[partition-1]
			start, size = start * 512, size * 512
			ImageError.check(start > 0 and size > 0, ImageError.CODE_FAILED_TO_CREATE, "Wrong partition table", {"image": image, "table": partitions})
			options += ["offset=%d" % start, "sizelimit=%d" % size]
		cmd.run(["mount", "-o%s" % ",".join(options), image, path])
	except cmd.CommandError, err:
		raise ImageError(ImageError.CODE_FAILED_TO_MOUNT, "Failed to mount image", {"path": path, "image": image, "options": options, "error": repr(err)})

@_public
def unmount(path, ignoreUnmounted=False):
	path = params.convert(path, convert=os.path.realpath, check=os.path.exists)
	if not _isMounted(path):
		if ignoreUnmounted:
			return
		raise ImageError(ImageError.CODE_ALREADY_UNMOUNTED, "Path is already unmounted", {"path": path})
	try:
		cmd.run(["umount", path])
	except cmd.CommandError, err:
		raise ImageError(ImageError.CODE_FAILED_TO_UNMOUNT, "Failed to unmount image", {"path": path, "error": repr(err)})

from . import Error, SUPPORT_CHECK_PERIOD
from util import CommandError, params, cmd, cache
import os, json

class QemuImgError(Error):
	CODE_UNKNOWN="qemu_img.unknown"
	CODE_UNSUPPORTED="qemu_img.unsupported"
	CODE_INVALID_IMAGE="qemu_img.invalid_image"
	CODE_FAILED_TO_CREATE="qemu_img.failed_to_create"
	CODE_FAILED_TO_CONVERT="qemu_img.failed_to_convert"

def _imageInfo(path, format=None):
	format = params.convert(format, convert=str, null=True)
	path = params.convert(path, check=os.path.exists)
	try:
		if format:
			res = cmd.run(["qemu-img", "info", "-f", format, "--output=json", path])
		else:
			res = cmd.run(["qemu-img", "info", "--output=json", path])
		return json.loads(res)
	except CommandError, err:
		data = {"path": path}
		data.update(err.data)
		raise QemuImgError(QemuImgError.CODE_INVALID_IMAGE, "Invalid image", data)
	except Exception, err:
		raise QemuImgError(QemuImgError.UNKNOWN, "Error checking image", {"path": path, "error": repr(err)})

_checkImage = _imageInfo

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	QemuImgError.check(cmd.exists("qemu-img"), QemuImgError.CODE_UNSUPPORTED, "Binary qemu-img does not exist")
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
def info(path, format=None):
	return _imageInfo(path, format)

check=info

@_public
def create(path, format="qcow2", size=None, backingImage=None):
	format = params.convert(format, convert=str)
	path = params.convert(path, check=lambda p: not os.path.exists(p))
	size = params.convert(size, convert=str, null=True)
	backingImage = params.convert(backingImage, check=os.path.exists, null=True)
	c = ["qemu-img", "create", "-f", format]
	if backingImage:
		c += ["-o", "backing_file=%s" % backingImage]
	c.append(path)
	if size and not backingImage:
		c.append(size)
	try:
		cmd.run(c)
	except CommandError, err:
		data = {"path": path, "format": format, "size": size, "backing_image": backingImage}
		data.update(err.data)
		raise QemuImgError(QemuImgError.CODE_FAILED_TO_CREATE, "Failed to create image", data)

@_public
def convert(src, dst, srcFormat="qcow2", dstFormat="qcow2", compress=True):
	src = params.convert(src, check=_checkImage)
	dst = params.convert(dst, check=lambda p: not os.path.exists(p))
	srcFormat = params.convert(srcFormat, convert=str)
	dstFormat = params.convert(dstFormat, convert=str)
	try:
		cmd.run(["qemu-img", "convert", "-c" if compress else "", "-f", srcFormat, "-O", dstFormat, src, dst])
	except CommandError, err:
		data = {"src": src, "dst": dst, "src_format": srcFormat, "dst_format": dstFormat}
		data.update(err.data)
		raise QemuImgError(QemuImgError.CODE_FAILED_TO_CONVERT, "Failed to convert image", data)

export=convert
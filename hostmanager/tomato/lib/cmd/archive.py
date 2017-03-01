"""
automatic archive type detection and extraction/packing

for more details on packing and extracting, see the pack() and extract() functions

to get a list of all supported types, see the keys of the dict constants TYPES_EXTRACT, and TYPES_PACK
"""

import os
from . import run
from ..error import UserError, InternalError

class ArchiveTypes:
	TAR = "tar"
	TARGZ = "tar"
	ZIP = "zip"
	RAR = "rar"
	SEVENZIP = "7z"

def which(program):
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			path = path.strip('"')
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file

	return None

class TarArchive:
	MIMETYPES = ("application/x-tar", "application/gzip")
	TYPES = (ArchiveTypes.TAR,)
	SUPPORTED_EXTRACT = (which("tar") is not None)
	SUPPORTED_PACK = (which("tar") is not None)

	@staticmethod
	def extract(src, dst, preserve_permissions):
		run(["tar", "-axf", src] + ([] if preserve_permissions else ["--no-same-owner"]) + ["-C", dst])

	@staticmethod
	def pack(src, dst, preserve_permissions, t):
		run(["tar", "--numeric-owner", "-acf", dst, "-C", src, "."])


class ZipFile:
	MIMETYPES = ("application/zip",)
	TYPES = (ArchiveTypes.ZIP,)
	SUPPORTED_EXTRACT = (which("unzip") is not None)
	SUPPORTED_PACK = (which("zip") is not None)

	@staticmethod
	def extract(src, dst, preserve_permissions):
		run(["unzip"] + (["-XK"] if preserve_permissions else []) + [src, "-d", dst])

	@staticmethod
	def pack(src, dst, preserve_permissions, t):
		run(("zip", dst, src))

class RarFile:  # fixme: implement
	MIMETYPES = ()
	TYPES = (ArchiveTypes.RAR,)
	SUPPORTED_EXTRACT = False
	SUPPORTED_PACK = False

	@staticmethod
	def extract(src, dst, preserve_permissions):
		pass

	@staticmethod
	def pack(src, dst, preserve_permissions, t):
		pass

class SevenZipFile:  # fixme: implement
	MIMETYPES = ()
	TYPES = (ArchiveTypes.SEVENZIP,)
	SUPPORTED_EXTRACT = False
	SUPPORTED_PACK = False

	@staticmethod
	def extract(src, dst, preserve_permissions):
		pass

	@staticmethod
	def pack(src, dst, preserve_permissions, t):
		pass





TYPES_EXTRACT = {}
TYPES_PACK = {}
for type_ in (TarArchive, ZipFile, RarFile, SevenZipFile):

	if type_.SUPPORTED_EXTRACT:
		for mt in type_.MIMETYPES:
			if mt in TYPES_EXTRACT:
				TYPES_EXTRACT[mt].append(type_)
			else:
				TYPES_EXTRACT[mt] = [type_]

	if type_.SUPPORTED_PACK:
		for t in type_.TYPES:
			if t in TYPES_PACK:
				TYPES_PACK[t].append(type_)
			else:
				TYPES_PACK[t] = [type_]





def mimetype(filename):
	return run(("file", "-b", "--mime-type", filename))




def extract(src, dst, preserve_permissions=False):
	"""
	detect archive type and extract
	:param str src: archive
	:param str dst: target directory
	:param bool preserve_permissions: preserve UID/GID information or not
	:return:
	"""
	mt = mimetype(src)
	UserError.check(mt in TYPES_EXTRACT, code=UserError.UNSUPPORTED_TYPE, message="archive format not supported",
	                data={"mimetype": mt})
	type_ = list(t for t in TYPES_EXTRACT[mt] if t.SUPPORT_EXTRACT)[0]
	return type_.extract(src, dst, preserve_permissions)

def pack(src, dst, preserve_permissions, t=ArchiveTypes.TARGZ):
	"""
	create an archive
	:param str src: directory or file to pack
	:param str dst: archive filename
	:param str t: target format - one of the ArchiveType constants; defaults to tar
	:return:
	"""
	UserError.check(t in TYPES_PACK, code=UserError.UNSUPPORTED_TYPE, message="archive format not supported",
	                data={"t": t})
	type_ = list(t for t in TYPES_PACK[mt] if t.SUPPORT_EXTRACT)[0]
	return type_.pack(src, dst, preserve_permissions, t)

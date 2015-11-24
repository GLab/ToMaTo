# specify version in /etc/tomato/version, or in OS environment variable $TOMATO_VERSION
import os

def getVersionStr(module):

	if os.path.exists("/etc/tomato/version"):
		try:
			with open("/etc/tomato/version") as f:
				version = f.readline()
				if version:
					return version
		except:
			pass

	version = os.getenv("TOMATO_VERSION", None)
	if version:
		return version

	return "devel"
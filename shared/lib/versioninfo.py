# specify version in /etc/tomato/version
import os

def getVersionStr(module):

	if os.path.exists("/etc/tomato/version"):
		try:
			with open("/etc/tomato/version") as f:
				version = f.readline()
				return version
		except:
			pass

	return "devel"
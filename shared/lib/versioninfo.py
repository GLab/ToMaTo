# ways to get the version (ordered by preference, i.e., if the first one works, ignore the others

# run git describe in the current working directory
# read a git describe dump from /etc/tomato/git-describe
# use dpkg-query to get the version of tomato packages installed on the system
# read a dpkg-query dump from /etc/tomato/dpkg-query


# dpkg functions
import os

def getDpkgVersionStr(package):
	from .cmd import runUnchecked
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



# git functions

def getGitVersionStr():
	info = getGitVersionInfo()
	if info:
		return "%s-%s" % info[0:2]
	return None

def getGitVersionInfo():
	from .cmd import runUnchecked
	output = None
	try:
		error, output = runUnchecked(["git", "describe", "--tags", "--dirty"])  # when changing params, also update in docker/run/cmds.sh
		assert not error
		assert output
	except:
		try:
			if os.path.exists("/etc/tomato/git-describe"):  # when changing filename, also update in docker/run/cmds.sh
				with open("/etc/tomato/git-describe") as f:
					output = f.read()
		except:
			return None
	res = []
	for line in output.splitlines():
		for part in line.split("-"):
			res.append(part)
	if res:
		return tuple(res)
	return None





# function to get the correct version

def getVersionStr(module):

	# try git
	version = getGitVersionStr()
	if version:
		return version

	# try dpkg
	if module == "web":
		version = getDpkgVersionStr("tomato-web")
	elif module == "backend":
		version = getDpkgVersionStr("tomato-backend")
	elif module == "hostmanager":
		version = getDpkgVersionStr("tomato-hostmanager")
	if version:
		return version

	# nothing worked. now just return devel.
	return "devel"
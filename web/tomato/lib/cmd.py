__author__ = 't-gerhard'

DEVNULL = open("/dev/null", "w")

def runUnchecked(cmd, shell=False, ignoreErr=False, input=None, cwd=None):  # @ReservedAssignment
	import subprocess
	stderr = DEVNULL if ignoreErr else subprocess.STDOUT
	stdin = subprocess.PIPE if input else None
	proc = subprocess.Popen(cmd, cwd=cwd, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr, shell=shell,
		close_fds=True)
	res = proc.communicate(input)
	return (proc.returncode, res[0])
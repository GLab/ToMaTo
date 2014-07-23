import os, signal
import wait

def kill(pid, force=False, group=False):
	sgnl = signal.SIGKILL if force else signal.SIGTERM
	if group:
		gid = os.getpgid(pid)
		os.killpg(gid, sgnl)
	else:
		os.kill(pid, sgnl) 
	
def isAlive(pid):
	return os.path.exists("/proc/%d" % pid)

def autoKill(pid, group=False, timeout=60):
	kill(pid, group=group, force=False)
	try:
		wait.waitFor(lambda :not isAlive(pid), timeout=timeout)
	except wait.WaitError:
		kill(pid, group=group, force=True)
import os, signal, collections
import wait

from . import cmd

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
	if not isAlive(pid):
		return
	kill(pid, group=group, force=False)
	try:
		wait.waitFor(lambda :not isAlive(pid), timeout=timeout)
	except wait.WaitError:
		kill(pid, group=group, force=True)

_jiffiesPerSecond = None
def jiffiesPerSecond():
	global _jiffiesPerSecond
	if _jiffiesPerSecond:
		return _jiffiesPerSecond
	cpus = 0
	with open("/proc/stat") as fp:
		jiffies = sum(map(int, fp.readline().split()[1:]))
		while fp.readline().startswith("cpu"):
			cpus += 1
	with open("/proc/uptime") as fp:
		seconds = float(fp.readline().split()[0])
	_jiffiesPerSecond = jiffies / seconds / cpus
	return jiffies / seconds / cpus

Statistics = collections.namedtuple("Statistics", ["cputime_total", "memory_used"])

def getStatistics(pid):
	with open("/proc/%d/stat" % pid) as fp:
		stats = fp.readline().split()
	cputime = sum(map(int, stats[13:17]))/jiffiesPerSecond()
	memory = int(stats[23]) * 4096
	return Statistics(cputime_total=cputime, memory_used=memory)

class IoPolicy:
	Idle = 3
	BestEffort = 2
	Realtime = 1

def ionice(pid, policy, priority=4):
	cmd.run(["ionice", "-c", str(policy), "-n", str(priority), "-p", str(pid)])

def isSameGroup(pid1, pid2):
	return os.getpgid(pid1) == os.getpgid(pid2)
import sys, os

# TODO: allow to set fds for stdin, stdout, stderr

class Daemon:
	def __init__(self):
		self.pid = None
		self._w_pipe = None
		self._r_pipe = None

	def start(self):
		if self.pid != None:
			raise Exception("Can only start process once")

		child_r, father_w = os.pipe()
		father_r, child_w = os.pipe()
		pid_r, pid_w = os.pipe()

		# To achieve a working daemon mode, we need to follow the magic incantation: fork - setsid - fork.

		# This is the first fork.
		pid = os.fork()
		if pid:
			# The original process will go this way and receive the pid of its child.
			# Wait for the child to fork its own child before we return.
			# This is important as the first child will still be terminated with the parent and we need to give it a chance to fork.
			# The original process will stay here until the first child returns from this function
			pid = os.read(pid_r, 16)
			self.pid = int(pid)
			self._w_pipe, self._r_pipe = father_w, father_r
			for fd in [child_r, child_w, pid_r, pid_w]:
				os.close(fd)
			return

		# If we are here, we are the first child.
		# Setsid will create a new process session but the process will still be a child of its parent.
		os.setsid()

		# Now we fork again to be a grand-child of the calling process with different session.
		# That is distant enough to not get killed together with the grand-parent.
		pid = os.fork()
		if pid:
			# The father (child of the caller) goes this way.
			# We set the pid attribute so we can use it when we return
			os.write(pid_w, str(pid))
			for fd in [child_w, child_r, father_w, father_r, pid_w, pid_r]:
				os.close(fd)
			# Exit this process so we dont execute the caller code
			os._exit(0)

		# We now close all the inherited file descripters and open our own.
		# The easiest way to get a list of all used file descriptors is using /proc/self/fd (this only works on Linux).
		for fd in os.listdir("/proc/self/fd"):
			try:
				fd = int(fd)
				# Close the file descriptor, this will not harm the grand-fathers fds as we only close the copies.
				if not fd in [child_w, child_r, sys.stderr.fileno()]:
					os.close(fd)
			except OSError:
				# If we get this error, the fd was not open in the first place, everything is ok.
				pass

		# Opening /dev/null as standard input. This will block on read as there is no input.
		os.open("/dev/null", os.O_RDWR)
		# Copying /dev/null over to standard output and error output. All output will be ignored.
		os.open("/dev/null", os.O_RDWR)
		# Finally closing stderr
		os.close(sys.stderr.fileno())
		# Cloning stdout to stderr
		os.dup2(1, 2)

		self._r_pipe, self._w_pipe = child_r, child_w

		# If we are here, we are a grand-child of the caller process.
		# So, finally we run the actual code.
		self.run()

		os.close(self._w_pipe)
		os.close(self._r_pipe)
		# Exit this process so we dont execute the caller code
		os._exit(0)

	def run(self):
		pass

	def send(self, data):
		os.write(self._w_pipe, data)

	def recv(self, size):
		return os.read(self._r_pipe, size)

	def signal(self, signal):
		os.kill(self.pid, signal)

	def terminate(self):
		self.signal(15)

	def wait(self):
		return os.waitpid(self.pid, 0)


def start(func, args=None, kwargs=None):
	if not kwargs: kwargs = {}
	if not args: args = []

	class Dummy(Daemon):
		def run(self):
			func(*args, **kwargs)

	dummy = Dummy()
	dummy.start()
	return dummy
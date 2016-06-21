import threading

class LockMatrix:
	def __init__(self, lockType=threading.RLock):
		self.lock = threading.RLock()
		self.locks = {}
		self.lockType = lockType
	def __getitem__(self, ident):
		with self.lock:
			if not ident in self.locks:
				self.locks[ident] = LockMatrix.Lock(self, ident, self.lockType())
			return self.locks[ident]
	def __delitem__(self, ident):
		with self.lock:
			with self[ident]:
				del self.locks[ident]
	class Lock:
		def __init__(self, matrix, ident, lock):
			self.matrix = matrix
			self.ident = ident
			self.lock = lock
		def __enter__(self):
			self.lock.acquire()
		def __exit__(self, *args):
			self.lock.release()
		def __del__(self):
			with self.lock:
				del self.matrix[self.ident]
	

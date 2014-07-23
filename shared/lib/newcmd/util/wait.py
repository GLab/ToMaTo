from .. import Error

import time

class WaitError(Error):
	CATEGORY="wait"
	TYPE_COND_FAILED="cond_failed"
	TYPE_FAILCOND_FAILED="failcond_failed"
	TYPE_TIMEOUT="timeout"
	TYPE_FAILED="failed"
	def __init__(self, type, message, data=None):
		Error.__init__(self, category=WaitError.CATEGORY, type=type, message=message, data=data)

def waitFor(cond, failCond=None, timeout=60.0):
	start = time.time()
	while True:
		s = time.time()
		try:
			if cond():
				return True
		except Exception, exc:
			raise WaitError(WaitError.TYPE_COND_FAILED, "Failed to execute condition", {"timeout": timeout, "cond": cond, "failCond": failCond, "error": exc})
		try:
			if failCond and failCond():
				raise WaitError(WaitError.TYPE_FAILED, "Fail condition met", {"timeout": timeout, "cond": cond, "failCond": failCond})
		except WaitError:
			raise
		except Exception, exc:
			raise WaitError(WaitError.TYPE_FAILCOND_FAILED, "Failed to execute fail condition", {"timeout": timeout, "cond": cond, "failCond": failCond, "error": exc})
		if time.time() > start + timeout:
			raise WaitError(WaitError.TYPE_TIMEOUT, "Wait timed out", {"timeout": timeout, "cond": cond, "failCond": failCond})
		dur = time.time() - s
		time.sleep(2*dur)
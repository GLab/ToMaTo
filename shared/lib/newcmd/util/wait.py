from .. import Error

import time

class WaitError(Error):
	CODE_COND_FAILED="wait.cond_failed"
	CODE_FAILCOND_FAILED="wait.failcond_failed"
	CODE_TIMEOUT="wait.timeout"
	CODE_FAILED="wait.failed"

def waitFor(cond, failCond=None, timeout=60.0):
	start = time.time()
	while True:
		s = time.time()
		try:
			if cond():
				return True
		except Exception, exc:
			raise WaitError(WaitError.CODE_COND_FAILED, "Failed to execute condition", {"timeout": timeout, "cond": cond, "failCond": failCond, "error": exc})
		try:
			if failCond and failCond():
				raise WaitError(WaitError.CODE_FAILED, "Fail condition met", {"timeout": timeout, "cond": cond, "failCond": failCond})
		except WaitError:
			raise
		except Exception, exc:
			raise WaitError(WaitError.CODE_FAILCOND_FAILED, "Failed to execute fail condition", {"timeout": timeout, "cond": cond, "failCond": failCond, "error": exc})
		if time.time() > start + timeout:
			raise WaitError(WaitError.CODE_TIMEOUT, "Wait timed out", {"timeout": timeout, "cond": cond, "failCond": failCond})
		dur = time.time() - s
		time.sleep(2*dur)
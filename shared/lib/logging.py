from datetime import datetime
import sys, os, gzip, bz2, time, json, traceback

class JSONLogger:
  def __init__(self, path, maxSize=1e7, maxAge=24*60*60, compress="gzip"):
    self.path = path
    self.maxSize = maxSize
    self.maxAge = maxAge
    self.compress = compress
    self.open()
  def open(self):
    now = datetime.strftime(datetime.now(), "%Y-%m-%d__%H-%M-%S")
    if self.compress == "gzip":
      self._fp = gzip.open(os.path.join(self.path, "%s.json.gz" % now), "w")
    elif self.compress == "bzip2":
      self._fp = bz2.BZ2File(os.path.join(self.path, "%s.json.bz2" % now), "w")
    else:
      self._fp = open(os.path.join(self.path, "%s.json" % now), "w")
    self._written = 0
    self._opened = time.time()
  def __enter__(self):
    return self
  def __exit__(self, *args):
    self.close()
  def close(self):
    self._fp.close()
    self._fp = None
  def _write(self, data):
    data = json.dumps(data)
    self._fp.write(data)
    self._fp.write("\n")
    self._written += len(data) + 1
    if self._written >= self.maxSize or self._opened + self.maxAge < time.time():
      self.close()
      self.open()
  def _caller(self):
    caller = None
    for t in traceback.extract_stack():
        if t[0] == __file__:
            break
        caller = list(t[0:3])
    if caller:
        caller[0] = "..."+caller[0][-22:]
    return caller
  def log(self, category=None, timestamp=None, caller=None, **kwargs):
    if not timestamp:
      timestamp = time.time()
    timestr = datetime.strftime(datetime.fromtimestamp(timestamp), "%Y-%m-%dT%H:%M:%S.%f%z")
    data = {"category": category, "timestamp": timestr}
    if not caller is False:
        data["caller"] = self._caller()
    data.update(kwargs)
    self._write(data)
  def logMessage(self, message, category=None, **kwargs):
    self.log(message=message, category=category, **kwargs)
  def logException(self, **kwargs):
    trace = traceback.extract_tb(sys.exc_traceback) if sys.exc_traceback else None
    self.log(category="exception", trace=trace, caller=False, exception=(sys.exc_type.__name__, str(sys.exc_value)), **kwargs)
    
_default = None
    
def openDefault(path, **kwargs):
    global _default
    _default = JSONLogger(path, **kwargs)
    
def closeDefault():
    global _default
    _default.close()
    _default = None

def logException(**kwargs):
    _default.logException(**kwargs)
    
def logMessage(message, **kwargs):
    _default.logMessage(message, **kwargs)
    
def log(**kwargs):
    _default.log(**kwargs)
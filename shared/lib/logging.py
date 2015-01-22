from datetime import datetime
import sys, time, traceback, hashlib
from . import anyjson as json

class JSONLogger:
  def __init__(self, path):
    self.path = path
    self.open()
  def open(self):
    self._fp = open(self.path, "a")
  def __enter__(self):
    return self
  def __exit__(self, *args):
    self.close()
  def close(self):
    self._fp.close()
    self._fp = None
  def _write(self, data):
    data = json.dumps(data)
    self._fp.write(data+"\n")
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
    data.update(maskPasswords(kwargs))
    self._write(data)
  def logMessage(self, message, category=None, **kwargs):
    self.log(message=message, category=category, **kwargs)
  def logException(self, **kwargs):
    (type, value, trace) = sys.exc_info()
    trace = traceback.extract_tb(trace) if trace else None
    self.log(category="exception", trace=trace, caller=False, exception=(type.__name__, str(value)), **kwargs)
    
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
    
def maskPasswords(data):
    tmp = {}
    for key, value in data.iteritems():
        if isinstance(value, dict):
            value = maskPasswords(value)
        else:
            for pattern in ["password", "passwd", "pwd"]:
                if pattern in key or pattern in repr(value):
                    value = "(contains passwords)MD5=%s" % hashlib.md5(repr(value)).hexdigest()
                    break
        tmp[key] = value
    return tmp 

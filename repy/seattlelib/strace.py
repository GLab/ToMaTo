"""
Author: Armon Dadgar
Description:
  This namespace can be used as an intermediary logging namespace to
  log calls to the Repy API functions.
"""

# These API functions do _not_ return an object, and can be handled uniformly.
NON_OBJ_API_CALLS = ["gethostbyname","getmyip","sendmessage","listfiles","removefile",
                     "exitall","getruntime","randombytes","createthread","sleep","getthreadname",
                     "getresources","getlasterror"]

# Global print lock
PRINT_LOCK = createlock()

# If this is True, then output will be serialized,
# this avoids jumbling but is a performance hit
ENABLE_LOCKING = True

# Limit the maximum print length of arguments and results
MAX_PRINT_VALS = 200  # Print the first 200 characters worth

# Handle when locking is disabled
if not ENABLE_LOCKING:
  def _noop(*args,**kwargs):
    return True
  
  PRINT_LOCK.acquire = _noop
  PRINT_LOCK.release = _noop


# Replace getruntime
_orig_getruntime = getruntime
def getruntime():
  return round(_orig_getruntime(), 5)


# Do a traced function call
def traced_call(self,name,func,args,kwargs,no_return=False,print_args=True,print_result=True):
  # Store the time, function call and arguments
  call_string = str(getruntime()) + " " + name

  # Print the optional stuff
  if not self is None:
    call_string += " " + str(self)
  if print_args and not args == ():
    str_args = str(args)
    if len(str_args) > MAX_PRINT_VALS:
      str_args = str_args[:MAX_PRINT_VALS] + "...)"
    call_string += " " + str_args
  if print_args and not kwargs == {}:
    call_string += " " + str(kwargs)[:MAX_PRINT_VALS]

  # Print if there is no return
  if no_return:
    PRINT_LOCK.acquire(True)
    print call_string
    PRINT_LOCK.release()

  # Get the result
  try:
    result = func(*args,**kwargs)

  # On an exception, print the call at least
  except Exception, e:
    PRINT_LOCK.acquire(True)
    print call_string,"->",str(type(e))+" "+str(e)
    PRINT_LOCK.release()
    raise

  # Return if there is no result
  if no_return:
    return

  # Lock to print
  if print_result:
    str_result = str(result)
    if len(str_result) > MAX_PRINT_VALS:
      str_result = str_result[:MAX_PRINT_VALS] + "..."
    call_string += " = " + str_result

  PRINT_LOCK.acquire(True)
  print call_string
  PRINT_LOCK.release()

  return result


# This class is used for API calls that don't return objects
class NonObjAPICall():
  # Initialize with the name of the call
  def __init__(self, name):
    self.name = name
    self.func = _context[name]

  # This method will be called by sub-namespaces
  def call(self,*args,**kwargs):
    # Trace the call
    return traced_call(None,self.name,self.func,args,kwargs)


# This class is used for socket objects
class SocketObj():
  # Store the socket object
  def __init__(self,sock):
    self.sock = sock

  # Emulate the other functions
  def close(self,*args,**kwargs):
    return traced_call(self.sock,"socket.close",self.sock.close,args,kwargs)

  def recv(self,*args,**kwargs):
    return traced_call(self.sock,"socket.recv",self.sock.recv,args,kwargs)

  def send(self,*args,**kwargs):
    return traced_call(self.sock,"socket.send",self.sock.send,args,kwargs)


# This class is used for lock objects
class LockObj():
  # Store the lock object
  def __init__(self,lock):
    self.lock = lock

  # Emulate the functions
  def acquire(self, *args,**kwargs):
    return traced_call(self.lock,"lock.acquire",self.lock.acquire,args,kwargs)

  def release(self, *args, **kwargs):
    return traced_call(self.lock,"lock.release",self.lock.release,args,kwargs,True)


# This class is used for file objects
class FileObj():
  # Store the file object
  def __init__(self,fileo):
    self.fileo = fileo

  # Emulate the functions
  def close(self,*args,**kwargs):
    return traced_call(self.fileo,"file.close",self.fileo.close,args,kwargs,True)

  def readat(self,*args,**kwargs):
    return traced_call(self.fileo,"file.readat",self.fileo.readat,args,kwargs)

  def writeat(self,*args,**kwargs):
    return traced_call(self.fileo,"file.writeat",self.fileo.writeat,args,kwargs,True)


class VNObj():
  # Store the virt object
  def __init__(self,virt):
    self.virt = virt

  # Emulate the functions
  def evaluate(self,*args,**kwargs):
    return traced_call(self.virt,"VirtualNamespace.evaluate",self.virt.evaluate,args,kwargs,print_args=False,print_result=False)


# This class is used for TCPServerObjects
class TCPServerObj():
  # Store the object
  def __init__(self,sock):
    self.sock = sock

  # Emulate the functions
  def getconnection(self, *args,**kwargs):
    ip,port,conn = traced_call(self.sock,"TCPServerSocket.getconnection",self.sock.getconnection,args,kwargs)
    return (ip,port, SocketObj(conn))

  def close(self, *args, **kwargs):
    return traced_call(self.sock,"TCPServerSocket.close",self.sock.close,args,kwargs,True)


# This class is used for UDPServerObjects
class UDPServerObj():
  # Store the object
  def __init__(self,sock):
    self.sock = sock

  # Emulate the functions
  def getmessage(self, *args,**kwargs):
    return traced_call(self.sock,"UDPServerSocket.getmessage",self.sock.getmessage,args,kwargs)

  def close(self, *args, **kwargs):
    return traced_call(self.sock,"UDPServerSocket.close",self.sock.close,args,kwargs,True)


# Wrap the call to openconnection
def wrapped_openconnection(*args, **kwargs):
  # Trace the call
  sock = traced_call(None,"openconnection",openconnection,args,kwargs)

  # Wrap the socket object
  return SocketObj(sock)

# Wrap the call to listenformessage
def wrapped_listenformessage(*args, **kwargs):
  # Trace the call
  sock = traced_call(None, "listenformessage", listenformessage, args, kwargs)

  # Return the socket object
  return UDPServerObj(sock)

# Wrap the call to listenforconnection
def wrapped_listenforconnection(*args, **kwargs):
  # Trace the call
  sock = traced_call(None, "listenforconnection", listenforconnection, args, kwargs)

  # Return the socket object
  return TCPServerObj(sock)


# Wrap the call to createlock
def wrapped_createlock(*args,**kwargs):
  # Trace the call to get the lock
  lock = traced_call(None,"createlock",createlock,args,kwargs)

  # Return the wrapped lock
  return LockObj(lock)

# Wrap the call to openfile
def wrapped_openfile(*args,**kwargs):
  # Trace the call to get the file object
  fileo = traced_call(None,"openfile",openfile,args,kwargs)

  # Return the wrapped object
  return FileObj(fileo)


# Wrap the call to createvirtualnamespace
def wrapped_virtual_namespace(*args,**kwargs):
  # Trace the call to get the object
  return VNObj(traced_call(None,"VirtualNamespace(...)",createvirtualnamespace,args,kwargs,print_args=False))


# Wrap all the API calls so they can be traced
def wrap_all():
  # Handle the normal calls
  for call in NON_OBJ_API_CALLS:
    CHILD_CONTEXT[call] = NonObjAPICall(call).call

  # Wrap openconnection
  CHILD_CONTEXT["openconnection"] = wrapped_openconnection

  # Wrap listenformessage
  CHILD_CONTEXT["listenformessage"] = wrapped_listenformessage

  # Wrap listenforconnection
  CHILD_CONTEXT["listenforconnection"] = wrapped_listenforconnection

  # Wrap createlock
  CHILD_CONTEXT["createlock"] = wrapped_createlock

  # Wrap openfile
  CHILD_CONTEXT["openfile"] = wrapped_openfile

  # Wrap createvirtualnamespace
  CHILD_CONTEXT["createvirtualnamespace"] = wrapped_virtual_namespace


# Wrap all the functions
wrap_all()

# Print the header
print "Call-time function [instance] [args] [ = result ]"

# Dispatch the next module
dy_dispatch_module()



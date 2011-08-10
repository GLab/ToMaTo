# harshexit module -- Should be renamed, but I'm not sure what to.
# Provides these functions:
#   portablekill: kill a function by pid
#   harshexit: die, and do some things depending on the error code
#   init_ostype: sets the module globals ostype and osrealtype

# used to get information about the system we're running on
import platform
import os
import sys

# needed for signal numbers
import signal

# needed for changing polling constants on the Nokia N800
import repy_constants

# Needed for kill_process; This will fail on non-windows systems
try:
  import windows_api
except:
  windows_api = None

# need for status retrieval
import statusstorage

# This prevents writes to the nanny's status information after we want to stop
statuslock = statusstorage.statuslock



ostype = None
osrealtype = None


# this indicates if we are exiting.   Wrapping in a list to prevent needing a
# global   (the purpose of this is described below)
statusexiting = [False]



class UnsupportedSystemException(Exception):
  pass



def portablekill(pid):
  global ostype
  global osrealtype

  if ostype == None:
    init_ostype()

  if ostype == 'Linux' or ostype == 'Darwin':
    try:
      os.kill(pid, signal.SIGTERM)
    except:
      pass

    try:
      os.kill(pid, signal.SIGKILL)
    except:
      pass

  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # Use new api
    windows_api.kill_process(pid)
    
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"



# exit all threads
def harshexit(val):
  global ostype
  global osrealtype

  if ostype == None:
    init_ostype()

  # The problem is that there can be multiple calls to harshexit before we
  # stop.   For example, a signal (like we may send to kill) may trigger a 
  # call.   As a result, we block all other status writers the first time this
  # is called, but don't later on...
  if not statusexiting[0]:

    # do this once (now)
    statusexiting[0] = True

    # prevent concurrent writes to status info (acquire the lock to stop others,
    # but do not block...
    statuslock.acquire()
  
    # we are stopped by the stop file watcher, not terminated through another 
    # mechanism
    if val == 4:
      # we were stopped by another thread.   Let's exit
      pass
    
    # Special Termination signal to notify the NM of excessive threads
    elif val == 56:
      statusstorage.write_status("ThreadErr")
      
    elif val == 44:
      statusstorage.write_status("Stopped")

    else:
      # generic error, normal exit, or exitall in the user code...
      statusstorage.write_status("Terminated")

    # We intentionally do not release the lock.   We don't want anyone else 
    # writing over our status information (we're killing them).
    

  if ostype == 'Linux':
    # The Nokia N800 refuses to exit on os._exit() by a thread.   I'm going to
    # signal our pid with SIGTERM (or SIGKILL if needed)
    portablekill(os.getpid())
#    os._exit(val)
  elif ostype == 'Darwin':
    os._exit(val)
  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # stderr is not automatically flushed in Windows...
    sys.stderr.flush()
    os._exit(val)
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"



# Figure out the OS type
def init_ostype():
  global ostype
  global osrealtype

  # Detect whether or not it is Windows CE/Mobile
  if os.name == 'ce':
    ostype = 'WindowsCE'
    return

  # figure out what sort of witch we are...
  osrealtype = platform.system()

  # The Nokia N800 (and N900) uses the ARM architecture, 
  # and we change the constants on it to make disk checks happen less often 
  if platform.machine().startswith('armv'):
    if osrealtype == 'Linux' or osrealtype == 'Darwin' or osrealtype == 'FreeBSD':
      repy_constants.CPU_POLLING_FREQ_LINUX = repy_constants.CPU_POLLING_FREQ_WINCE;
      repy_constants.RESOURCE_POLLING_FREQ_LINUX = repy_constants.RESOURCE_POLLING_FREQ_WINCE;

  if osrealtype == 'Linux' or osrealtype == 'Windows' or osrealtype == 'Darwin':
    ostype = osrealtype
    return

  # workaround for a Vista bug...
  if osrealtype == 'Microsoft':
    ostype = 'Windows'
    return

  if osrealtype == 'FreeBSD':
    ostype = 'Linux'
    return

  if osrealtype.startswith('CYGWIN'):
    # I do this because ps doesn't do memory info...   They'll need to add
    # pywin to their copy of cygwin...   I wonder if I should detect its 
    # abscence and tell them (but continue)?
    ostype = 'Windows'
    return

  ostype = 'Unknown'

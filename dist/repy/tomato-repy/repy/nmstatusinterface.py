# Armon Dadgar
# May 10th 2009
#
# This file houses the code used for interactions between repy and the node manager.
# Namely, it checks for a stopfile to inform us to terminate, and it periodically
# writes a status file informing the NM of our status.
#

# This is used to write out our status
import statusstorage

# This prevents updates to our current status when we are about to exit
statuslock = statusstorage.statuslock

# This is to sleep
import time

# This is for the thread
import threading

# This is for path checking and stuff
import os

# For ostype, harshexit
import harshexit

# For setting thread priority (import fails on non-windows)
try:
  import windows_api
except:
  windows_api = None

# This is to get around the safe module
safe_open = open

# Store our important variables
stopfilename = None
statusfilename_prefix = None
frequency = 1     # Check rate in seconds

# This lock is to allow the thread to run
# If the thread fails to acquire it (e.g. somebody else has it) it will stop
run_thread_lock = threading.Lock()


def init(stopfile=None, statusfile=None, freq=1):
  """
  <Purpose>
    Prepares the module to run.

  <Arguments>
    stopfile: 
      The name of the stopfile to check for. Set to None to disable checking for a stopfile.

    statusfile: 
      The filename prefix for writing out our status. Set to None to disable a status file

    freq:
      The frequency of checks for the stopfile and status updates. 1 second is default.
  """
  global stopfilename, statusfilename_prefix, frequency

  # Check for the stopfile
  if stopfile != None and os.path.exists(stopfile):
    raise Exception, "Stop file already exists! File:"+stopfile

  # Assign the values
  stopfilename = stopfile
  statusfilename_prefix = statusfile
  frequency = freq

  # Initialize statusstorage
  statusstorage.init(statusfilename_prefix)


def launch(pid):
  """
  <Purpose>
    Starts a thread to handle status updates and stopfile checking.

  <Arguments>
    pid:
      The repy process id on unix, or None on Windows.

  <Side Effects>
    Starts a new thread.
  """

  # Check if we need to do anything
  global stopfilename, statusfilename_prefix
  if stopfilename == None and statusfilename_prefix == None:
    return

  # Launch the thread    
  threadobj = nm_interface_thread(pid)
  threadobj.start()


def stop():
  """
  <Purpose>
    Stops the worker thread.
    WARNING: Do not call this twice. It will block indefinately.
  """
  # Acquiring the thread lock will cause the thread to stop
  global run_thread_lock
  run_thread_lock.acquire()


# This is an internal function called when the stopfile is found
# It handles some of the nonportable details for nm_interface_thread
def _stopfile_exit(exitcode, pid):
  # On Windows, we are in the Repy process, so we can just use harshexit
  if harshexit.ostype in ["Windows", "WindowsCE"]:
    # Harshexit will store the appriopriate status for us
    harshexit.harshexit(exitcode)

  else:    # On NIX we are on the external process
    try:
      if exitcode == 44:
        # Write out status information, repy was Stopped
        statusstorage.write_status("Stopped")  
      else:
        # Status terminated
        statusstorage.write_status("Terminated")
    except:
      pass

    # Disable the other status thread, in case the resource thread detects we've killed repy
    statusstorage.init(None)

    # Kill repy
    harshexit.portablekill(pid)

    # Fix Derek proposed, this should solve the problem of 
    # the monitor exiting before the repy process.
    time.sleep(1)

    # Exit
    harshexit.harshexit(78)

# This is the actual worker thread
class nm_interface_thread(threading.Thread):
  def __init__(self, pid):
    self.repy_process_id = pid
    threading.Thread.__init__(self)


  def run(self):
    global stopfilename, frequency, run_thread_lock
    
    # On Windows elevate our priority above the user code.
    if harshexit.ostype in ["Windows", "WindowsCE"]:
      # Elevate our priority, above normal is higher than the usercode
      windows_api.set_current_thread_priority(windows_api.THREAD_PRIORITY_ABOVE_NORMAL)
    
    while True:
      # Attempt to get the lock
      have_lock = run_thread_lock.acquire(False)
      
      # If we have the lock, release and continue. Else break and exit the thread
      if have_lock: run_thread_lock.release()
      else: break

      # Get the status lock
      statuslock.acquire()

      # Write out our status
      statusstorage.write_status("Started")

      # Release the status lock
      statuslock.release()

      # Look for the stopfile
      if stopfilename != None and os.path.exists(stopfilename):
        try:
          # Get a file object for the file
          fileobject = safe_open(stopfilename)

          # Read in the contents, close the object
          contents = fileobject.read()
          fileobject.close()
            
          # Check the length, if there is nothing then just close as stopped
          if len(contents) > 0:
            # Split, at most we have 2 parts, the exit code and message
            (exitcode, mesg) = contents.split(";",1)
            exitcode = int(exitcode)
            
            # Check if exitcode is 56, which stands for ThreadErr is specified
            # ThreadErr cannot be specified externally, since it has side-affects
            # such as changing global thread restrictions
            if exitcode == 56:
              raise Exception, "ThreadErr exit code specified. Exit code not allowed."
            
            # Print the message, then call harshexit with the exitcode
            if mesg != "": 
              print mesg
            _stopfile_exit(exitcode, self.repy_process_id)
            
          else:
            raise Exception, "Stopfile has no content."
            
        except:
          # On any issue, just do "Stopped" (44)
          _stopfile_exit(44, self.repy_process_id)

      # Sleep until the next loop around.
      time.sleep(frequency)




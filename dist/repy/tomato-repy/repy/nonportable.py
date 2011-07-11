""" 
Author: Justin Cappos

Start Date: July 1st, 2008

Description:
Handles exiting and killing all threads, tracking CPU / Mem usage, etc.


"""


import threading
import os
import time

# needed for sys.stderr and windows Popen hackery
import sys

# needed for signal numbers
import signal

# needed for harshexit
import harshexit

# print useful info when exiting...
import tracebackrepy  

# used to query status, etc.
# This may fail on Windows CE
try:
  import subprocess
  mobile_no_subprocess = False
except ImportError:
  # Set flag to avoid using subprocess
  mobile_no_subprocess = True 


# used for socket.error
import socket

# need for status retrieval
import statusstorage

# Get constants
import repy_constants

# Get access to the status interface so we can start it
import nmstatusinterface

# This allows us to meter resource use
import nanny

# This is used for IPC
import marshal

# This will fail on non-windows systems
try:
  import windows_api as windows_api
except:
  windows_api = None

# Armon: This is a place holder for the module that will be imported later
os_api = None

# Armon: See additional imports at the bottom of the file

class UnsupportedSystemException(Exception):
  pass



###################     Publicly visible functions   #######################

# check the disk space used by a dir.
def compute_disk_use(dirname):
  # Convert path to absolute
  dirname = os.path.abspath(dirname)
  
  diskused = 0
  
  for filename in os.listdir(dirname):
    try:
      diskused = diskused + os.path.getsize(os.path.join(dirname, filename))
    except IOError:   # They likely deleted the file in the meantime...
      pass
    except OSError:   # They likely deleted the file in the meantime...
      pass

    # charge an extra 4K for each file to prevent lots of little files from 
    # using up the disk.   I'm doing this outside of the except clause in
    # the failure to get the size wasn't related to deletion
    diskused = diskused + 4096
        
  return diskused


# prepare a socket so it behaves how we want
def preparesocket(socketobject):
  
  if ostype == 'Windows':
    # we need to set a timeout because on rare occasions Windows will block 
    # on recvmess with a bad socket.  This prevents it from locking the system.
    # We use select, so the timeout should never be actually used.

    # The actual value doesn't seem to matter, so I'll use 100 years
    socketobject.settimeout(60*60*24*365*100)

  elif ostype == 'Linux' or ostype == 'Darwin':
    # Linux seems not to care if we set the timeout, Mac goes nuts and refuses
    # to let you send from a socket you're receiving on (why?)
    pass

  elif ostype == "WindowsCE":
    # No known issues, so just go
    pass
	
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"
  

# Armon: Also launches the nmstatusinterface thread.
# This will result in an internal thread on Windows
# and a thread on the external process for *NIX
def monitor_cpu_disk_and_mem():
  if ostype == 'Linux' or ostype == 'Darwin':  
    # Startup a CPU monitoring thread/process
    do_forked_resource_monitor()
    
  elif ostype == 'Windows' or ostype == 'WindowsCE':
    # Now we set up a cpu nanny...
    # Use an external CPU monitor for WinCE
    if ostype == 'WindowsCE':
      nannypath = "\"" + repy_constants.PATH_SEATTLE_INSTALL + 'win_cpu_nanny.py' + "\""
      cmdline = str(os.getpid())+" "+str(nanny.get_resource_limit("cpu"))+" "+str(repy_constants.CPU_POLLING_FREQ_WINCE)
      windows_api.launch_python_script(nannypath, cmdline)
    else:
      WinCPUNannyThread().start()
    
    # Launch mem./disk resource nanny
    WindowsNannyThread().start()
    
    # Start the nmstatusinterface. Windows means repy isn't run in an external
    # process, so pass None instead of a process id.
    nmstatusinterface.launch(None)
  else:
    raise UnsupportedSystemException, "Unsupported system type: '"+osrealtype+"' (alias: "+ostype+")"




# Elapsed time
elapsedtime = 0

# Store the uptime of the system when we first get loaded
starttime = 0
last_uptime = 0

# Timestamp from our starting point
last_timestamp = time.time()

# This is our uptime granularity
granularity = 1

# This ensures only one thread calling getruntime at any given time
runtimelock = threading.Lock()

def getruntime():
  """
   <Purpose>
      Return the amount of time the program has been running.   This is in
      wall clock time.   This function is not guaranteed to always return
      increasing values due to NTP, etc.

   <Arguments>
      None

   <Exceptions>
      None.

   <Side Effects>
      None

   <Remarks>
      By default this will have the same granularity as the system clock. However, if time 
      goes backward due to NTP or other issues, getruntime falls back to system uptime.
      This has much lower granularity, and varies by each system.

   <Returns>
      The elapsed time as float
  """
  global starttime, last_uptime, last_timestamp, elapsedtime, granularity, runtimelock
  
  # Get the lock
  runtimelock.acquire()
  
  # Check if Linux or BSD/Mac
  if ostype in ["Linux", "Darwin"]:
    uptime = os_api.get_system_uptime()

    # Check if time is going backward
    if uptime < last_uptime:
      # If the difference is less than 1 second, that is okay, since
      # The boot time is only precise to 1 second
      if (last_uptime - uptime) > 1:
        raise EnvironmentError, "Uptime is going backwards!"
      else:
        # Use the last uptime
        uptime = last_uptime
        
        # No change in uptime
        diff_uptime = 0
    else:  
      # Current uptime, minus the last uptime
      diff_uptime = uptime - last_uptime
      
      # Update last uptime
      last_uptime = uptime

  # Check for windows  
  elif ostype in ["Windows", "WindowsCE"]:   
    # Release the lock
    runtimelock.release()
    
    # Time.clock returns elapsedtime since the first call to it, so this works for us
    return time.clock()
     
  # Who knows...  
  else:
    raise EnvironmentError, "Unsupported Platform!"
  
  # Current uptime minus start time
  runtime = uptime - starttime
  
  # Get runtime from time.time
  current_time = time.time()
  
  # Current time, minus the last time
  diff_time = current_time - last_timestamp
  
  # Update the last_timestamp
  last_timestamp = current_time
  
  # Is time going backward?
  if diff_time < 0.0:
    # Add in the change in uptime
    elapsedtime += diff_uptime
  
  # Lets check if time.time is too skewed
  else:
    skew = abs(elapsedtime + diff_time - runtime)
    
    # If the skew is too great, use uptime instead of time.time()
    if skew < granularity:
      elapsedtime += diff_time
    else:
      elapsedtime += diff_uptime
  
  # Release the lock
  runtimelock.release()
          
  # Return the new elapsedtime
  return elapsedtime
 

# This lock is used to serialize calls to get_resouces
get_resources_lock = threading.Lock()

# Cache the disk used from the external process
cached_disk_used = 0L

# This array holds the times that repy was stopped.
# It is an array of tuples, of the form (time, amount)
# where time is when repy was stopped (from getruntime()) and amount
# is the stop time in seconds. The last process_stopped_max_entries are retained
process_stopped_timeline = []
process_stopped_max_entries = 100

# Method to expose resource limits and usage
def get_resources():
  """
  <Purpose>
    Returns the resouce utilization limits as well
    as the current resource utilization.

  <Arguments>
    None.

  <Returns>
    A tuple of dictionaries and an array (limits, usage, stoptimes).

    Limits is the dictionary which maps the resouce name
    to its maximum limit.

    Usage is the dictionary which maps the resource name
    to its current usage.

    Stoptimes is an array of tuples with the times which the Repy proces
    was stopped and for how long, due to CPU over-use.
    Each entry in the array is a tuple (TOS, Sleep Time) where TOS is the
    time of stop (respective to getruntime()) and Sleep Time is how long the
    repy process was suspended.

    The stop times array holds a fixed number of the last stop times.
    Currently, it holds the last 100 stop times.
  """
  # Acquire the lock...
  get_resources_lock.acquire()

  # ...but always release it
  try:
    # Construct the dictionaries as copies from nanny
    (limits,usage) = nanny.get_resource_information()


    # Calculate all the usage's
    pid = os.getpid()

    # Get CPU and memory, this is thread specific
    if ostype in ["Linux", "Darwin"]:
    
      # Get CPU first, then memory
      usage["cpu"] = os_api.get_process_cpu_time(pid)

      # This uses the cached PID data from the CPU check
      usage["memory"] = os_api.get_process_rss()

      # Get the thread specific CPU usage
      usage["threadcpu"] = os_api.get_current_thread_cpu_time() 


    # Windows Specific versions
    elif ostype in ["Windows","WindowsCE"]:
    
      # Get the CPU time
      usage["cpu"] = windows_api.get_process_cpu_time(pid)

      # Get the memory, use the resident set size
      usage["memory"] = windows_api.process_memory_info(pid)['WorkingSetSize'] 

      # Get thread-level CPU 
      usage["threadcpu"] = windows_api.get_current_thread_cpu_time()

    # Unknown OS
    else:
      raise EnvironmentError("Unsupported Platform!")

    # Use the cached disk used amount
    usage["diskused"] = cached_disk_used

  finally:
    # Release the lock
    get_resources_lock.release()

  # Copy the stop times
  stoptimes = process_stopped_timeline[:]

  # Return the dictionaries and the stoptimes
  return (limits,usage,stoptimes)


###################     Windows specific functions   #######################

class WindowsNannyThread(threading.Thread):

  def __init__(self):
    threading.Thread.__init__(self,name="NannyThread")

  def run(self):
    # Calculate how often disk should be checked
    if ostype == "WindowsCE":
      disk_interval = int(repy_constants.RESOURCE_POLLING_FREQ_WINCE / repy_constants.CPU_POLLING_FREQ_WINCE)
    else:
      disk_interval = int(repy_constants.RESOURCE_POLLING_FREQ_WIN / repy_constants.CPU_POLLING_FREQ_WIN)
    current_interval = 0 # What cycle are we on  
    
    # Elevate our priority, above normal is higher than the usercode, and is enough for disk/mem
    windows_api.set_current_thread_priority(windows_api.THREAD_PRIORITY_ABOVE_NORMAL)
    
    # need my pid to get a process handle...
    mypid = os.getpid()

    # run forever (only exit if an error occurs)
    while True:
      try:
        # Check memory use, get the WorkingSetSize or RSS
        memused = windows_api.process_memory_info(mypid)['WorkingSetSize']
        
        if memused > nanny.get_resource_limit("memory"):
          # We will be killed by the other thread...
          raise Exception, "Memory use '"+str(memused)+"' over limit '"+str(nanny.get_resource_limit("memory"))+"'"
        
        # Increment the interval we are on
        current_interval += 1

        # Check if we should check the disk
        if (current_interval % disk_interval) == 0:
          # Check diskused
          diskused = compute_disk_use(repy_constants.REPY_CURRENT_DIR)
          if diskused > nanny.get_resource_limit("diskused"):
            raise Exception, "Disk use '"+str(diskused)+"' over limit '"+str(nanny.get_resource_limit("diskused"))+"'"
        
        if ostype == 'WindowsCE':
          time.sleep(repy_constants.CPU_POLLING_FREQ_WINCE)
        else:
          time.sleep(repy_constants.CPU_POLLING_FREQ_WIN)
        
      except windows_api.DeadProcess:
        #  Process may be dead, or die while checking memory use
        #  In any case, there is no reason to continue running, just exit
        harshexit.harshexit(99)

      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "Nanny died!   Trying to kill everything else"
        harshexit.harshexit(20)


# Windows specific CPU Nanny Stuff
winlastcpuinfo = [0,0]

# Enfoces CPU limit on Windows and Windows CE
def win_check_cpu_use(cpulim, pid):
  global winlastcpuinfo
  
  # get use information and time...
  now = getruntime()

  # Get the total cpu time
  usertime = windows_api.get_process_cpu_time(pid)

  useinfo = [usertime, now]

  # get the previous time and cpu so we can compute the percentage
  oldusertime = winlastcpuinfo[0]
  oldnow = winlastcpuinfo[1]

  if winlastcpuinfo == [0,0]:
    winlastcpuinfo = useinfo
    # give them a free pass if it's their first time...
    return 0

  # save this data for next time...
  winlastcpuinfo = useinfo

  # Get the elapsed time...
  elapsedtime = now - oldnow

  # This is a problem
  if elapsedtime == 0:
    return -1 # Error condition
    
  # percent used is the amount of change divided by the time...
  percentused = (usertime - oldusertime) / elapsedtime

  # Calculate amount of time to sleep for
  stoptime = nanny.calculate_cpu_sleep_interval(cpulim, percentused,elapsedtime)

  if stoptime > 0.0:
    # Try to timeout the process
    if windows_api.timeout_process(pid, stoptime):
      # Log the stoptime
      process_stopped_timeline.append((now, stoptime))

      # Drop the first element if the length is greater than the maximum entries
      if len(process_stopped_timeline) > process_stopped_max_entries:
        process_stopped_timeline.pop(0)

      # Return how long we slept so parent knows whether it should sleep
      return stoptime
  
    else:
      # Process must have been making system call, try again next time
      return -1
  
  # If the stop time is 0, then avoid calling timeout_process
  else:
    return 0.0
    
            
# Dedicated Thread for monitoring CPU, this is run as a part of repy
class WinCPUNannyThread(threading.Thread):
  # Thread variables
  pid = 0 # Process pid
  
  def __init__(self):
    self.pid = os.getpid()
    threading.Thread.__init__(self,name="CPUNannyThread")    
      
  def run(self):
    # Elevate our priority, set us to the highest so that we can more effectively throttle
    success = windows_api.set_current_thread_priority(windows_api.THREAD_PRIORITY_HIGHEST)
    
    # If we failed to get HIGHEST priority, try above normal, else we're still at default
    if not success:
      windows_api.set_current_thread_priority(windows_api.THREAD_PRIORITY_ABOVE_NORMAL)
    
    # Run while the process is running
    while True:
      try:
        # Get the frequency
        frequency = repy_constants.CPU_POLLING_FREQ_WIN
        
        # Base amount of sleeping on return value of 
    	  # win_check_cpu_use to prevent under/over sleeping
        slept = win_check_cpu_use(nanny.get_resource_limit("cpu"), self.pid)
        
        if slept == -1:
          # Something went wrong, try again
          pass
        elif (slept < frequency):
          time.sleep(frequency-slept)

      except windows_api.DeadProcess:
        #  Process may be dead
        harshexit.harshexit(97)
        
      except:
        tracebackrepy.handle_exception()
        print >> sys.stderr, "CPU Nanny died!   Trying to kill everything else"
        harshexit.harshexit(25)
              
              





##############     *nix specific functions (may include Mac)  ###############

# This method handles messages on the "diskused" channel from
# the external process. When the external process measures disk used,
# it is piped in and cached for calls to getresources.
def IPC_handle_diskused(bytes):
  cached_disk_used = bytes


# This method handles meessages on the "repystopped" channel from
# the external process. When the external process stops repy, it sends
# a tuple with (TOS, amount) where TOS is time of stop (getruntime()) and
# amount is the amount of time execution was suspended.
def IPC_handle_stoptime(info):
  # Push this onto the timeline
  process_stopped_timeline.append(info)

  # Drop the first element if the length is greater than the max
  if len(process_stopped_timeline) > process_stopped_max_entries:
    process_stopped_timeline.pop(0)


# Use a special class of exception for when
# resource limits are exceeded
class ResourceException(Exception):
  pass


# Armon: Method to write a message to the pipe, used for IPC.
# This allows the pipe to be multiplexed by sending simple dictionaries
def write_message_to_pipe(writehandle, channel, data):
  """
  <Purpose>
    Writes a message to the pipe

  <Arguments>
    writehandle:
        A handle to a pipe which can be written to.

    channel:
        The channel used to describe the data. Used for multiplexing.

    data:
        The data to send.

  <Exceptions>
    As with os.write()
    EnvironmentError will be thrown if os.write() sends 0 bytes, indicating the
    pipe is broken.
  """
  # Construct the dictionary
  mesg_dict = {"ch":channel,"d":data}

  # Convert to a string
  mesg_dict_str = marshal.dumps(mesg_dict)

  # Make a full string
  mesg = str(len(mesg_dict_str)) + ":" + mesg_dict_str

  # Send this
  index = 0
  while index < len(mesg):
    bytes = os.write(writehandle, mesg[index:])
    if bytes == 0:
      raise EnvironmentError, "Write send 0 bytes! Pipe broken!"
    index += bytes


# Armon: Method to read a message from the pipe, used for IPC.
# This allows the pipe to be multiplexed by sending simple dictionaries
def read_message_from_pipe(readhandle):
  """
  <Purpose>
    Reads a message from a pipe.

  <Arguments>
    readhandle:
        A handle to a pipe which can be read from

  <Exceptions>
    As with os.read().
    EnvironmentError will be thrown if os.read() returns a 0-length string, indicating
    the pipe is broken.

  <Returns>
    A tuple (Channel, Data) where Channel is used to multiplex the pipe.
  """
  # Read until we get to a colon
  data = ""
  index = 0

  # Loop until we get a message
  while True:

    # Read in data if the buffer is empty
    if index >= len(data):
      # Read 8 bytes at a time
      mesg = os.read(readhandle,8)
      if len(mesg) == 0:
        raise EnvironmentError, "Read returned emtpy string! Pipe broken!"
      data += mesg

    # Increment the index while there is data and we have not found a colon
    while index < len(data) and data[index] != ":":
      index += 1

    # Check if we've found a colon
    if len(data) > index and data[index] == ":":
      # Get the message length
      mesg_length = int(data[:index])

      # Determine how much more data we need
      more_data = mesg_length - len(data) + index + 1

      # Read in the rest of the message
      while more_data > 0:
        mesg = os.read(readhandle, more_data)
        if len(mesg) == 0:
          raise EnvironmentError, "Read returned emtpy string! Pipe broken!"
        data += mesg
        more_data -= len(mesg)

      # Done, convert the message to a dict
      whole_mesg = data[index+1:]
      mesg_dict = marshal.loads(whole_mesg)

      # Return a tuple (Channel, Data)
      return (mesg_dict["ch"],mesg_dict["d"])



# This dictionary defines the functions that handle messages
# on each channel. E.g. when a message arrives on the "repystopped" channel,
# the IPC_handle_stoptime function should be invoked to handle it.
IPC_HANDLER_FUNCTIONS = {"repystopped":IPC_handle_stoptime,
                         "diskused":IPC_handle_diskused }


# This thread checks that the parent process is alive and invokes
# delegate methods when messages arrive on the pipe.
class parent_process_checker(threading.Thread):
  def __init__(self, readhandle):
    """
    <Purpose>
      Terminates harshly if our parent dies before we do.

    <Arguments>
      readhandle: A file descriptor to the handle of a pipe to our parent.
    """
    # Name our self
    threading.Thread.__init__(self, name="ParentProcessChecker")

    # Store the handle
    self.readhandle = readhandle

  def run(self):
    # Run forever
    while True:
      # Read a message
      try:
        mesg = read_message_from_pipe(self.readhandle)
      except Exception, e:
        break

      # Check for a handler function
      if mesg[0] in IPC_HANDLER_FUNCTIONS:
        # Invoke the handler function with the data
        handler = IPC_HANDLER_FUNCTIONS[mesg[0]]
        handler(mesg[1])

      # Print a message if there is a message on an unknown channel
      else:
        print "[WARN] Message on unknown channel from parent process:", mesg[0]


    ### We only leave the loop on a fatal error, so we need to exit now

    # Write out status information, our parent would do this, but its dead.
    statusstorage.write_status("Terminated")  
    print >> sys.stderr, "Monitor process died! Terminating!"
    harshexit.harshexit(70)



# For *NIX systems, there is an external process, and the 
# pid for the actual repy process is stored here
repy_process_id = None

# Forks Repy. The child will continue execution, and the parent
# will become a resource monitor
def do_forked_resource_monitor():
  global repy_process_id

  # Get a pipe
  (readhandle, writehandle) = os.pipe()

  # I'll fork a copy of myself
  childpid = os.fork()

  if childpid == 0:
    # We are the child, close the write end of the pipe
    os.close(writehandle)

    # Start a thread to check on the survival of the parent
    parent_process_checker(readhandle).start()

    return
  else:
    # We are the parent, close the read end
    os.close(readhandle)

  # Store the childpid
  repy_process_id = childpid

  # Start the nmstatusinterface
  nmstatusinterface.launch(repy_process_id)
  
  # Small internal error handler function
  def _internal_error(message):
    try:
      print >> sys.stderr, message
      sys.stderr.flush()
    except:
      pass
      
    # Stop the nmstatusinterface, we don't want any more status updates
    nmstatusinterface.stop()  

    # Kill repy
    harshexit.portablekill(childpid)

    try:
      # Write out status information, repy was Stopped
      statusstorage.write_status("Terminated")  
    except:
      pass
  
  try:
    # Some OS's require that you wait on the pid at least once
    # before they do any accounting
    (pid, status) = os.waitpid(childpid,os.WNOHANG)
    
    # Launch the resource monitor, if it fails determine why and restart if necessary
    resource_monitor(childpid, writehandle)
    
  except ResourceException, exp:
    # Repy exceeded its resource limit, kill it
    _internal_error(str(exp)+" Impolitely killing child!")
    harshexit.harshexit(98)
    
  except Exception, exp:
    # There is some general error...
    try:
      (pid, status) = os.waitpid(childpid,os.WNOHANG)
    except:
      # This means that the process is dead
      pass
    
    # Check if this is repy exiting
    if os.WIFEXITED(status) or os.WIFSIGNALED(status):
      sys.exit(0)
    
    else:
      _internal_error(str(exp)+" Monitor death! Impolitely killing child!")
      raise
  
def resource_monitor(childpid, pipe_handle):
  """
  <Purpose>
    Function runs in a loop forever, checking resource usage and throttling CPU.
    Checks CPU, memory, and disk.
    
  <Arguments>
    childpid:
      The child pid, e.g. the pid of repy

    pipe_handle:
      A handle to the pipe to the repy process. Allows sending resource use information.
  """
  # Get our pid
  ourpid = os.getpid()
  
  # Calculate how often disk should be checked
  disk_interval = int(repy_constants.RESOURCE_POLLING_FREQ_LINUX / repy_constants.CPU_POLLING_FREQ_LINUX)
  current_interval = -1 # What cycle are we on  
  
  # Store time of the last interval
  last_time = getruntime()
  last_CPU_time = 0
  resume_time = 0 
  
  # Run forever...
  while True:
    ########### Check CPU ###########
    # Get elasped time
    currenttime = getruntime()
    elapsedtime1 = currenttime - last_time     # Calculate against last run
    elapsedtime2 = currenttime - resume_time   # Calculate since we last resumed repy
    elapsedtime = min(elapsedtime1, elapsedtime2) # Take the minimum interval
    last_time = currenttime  # Save the current time
    
    # Safety check, prevent ZeroDivisionError
    if elapsedtime == 0.0:
      continue
    
    # Get the total cpu at this point
    totalCPU =  os_api.get_process_cpu_time(ourpid)   # Our own usage
    totalCPU += os_api.get_process_cpu_time(childpid) # Repy's usage
    
    # Calculate percentage of CPU used
    percentused = (totalCPU - last_CPU_time) / elapsedtime
    
    # Do not throttle for the first interval, wrap around
    # Store the totalCPU for the next cycle
    if last_CPU_time == 0:
      last_CPU_time = totalCPU    
      continue
    else:
      last_CPU_time = totalCPU
      
    # Calculate stop time
    stoptime = nanny.calculate_cpu_sleep_interval(nanny.get_resource_limit("cpu"), percentused, elapsedtime)
    
    # If we are supposed to stop repy, then suspend, sleep and resume
    if stoptime > 0.0:
      # They must be punished by stopping
      os.kill(childpid, signal.SIGSTOP)

      # Sleep until time to resume
      time.sleep(stoptime)

      # And now they can start back up!
      os.kill(childpid, signal.SIGCONT)
      
      # Save the resume time
      resume_time = getruntime()

      # Send this information as a tuple containing the time repy was stopped and
      # for how long it was stopped
      write_message_to_pipe(pipe_handle, "repystopped", (currenttime, stoptime))
      
    
    ########### End Check CPU ###########
    # 
    ########### Check Memory ###########
    
    # Get how much memory repy is using
    memused = os_api.get_process_rss()
    
    # Check if it is using too much memory
    if memused > nanny.get_resource_limit("memory"):
      raise ResourceException, "Memory use '"+str(memused)+"' over limit '"+str(nanny.get_resource_limit("memory"))+"'."
    
    ########### End Check Memory ###########
    # 
    ########### Check Disk Usage ###########
    # Increment our current cycle
    current_interval += 1;
    
    # Check if it is time to check the disk usage
    if (current_interval % disk_interval) == 0:
      # Reset the interval
      current_interval = 0
       
      # Calculate disk used
      diskused = compute_disk_use(repy_constants.REPY_CURRENT_DIR)

      # Raise exception if we are over limit
      if diskused > nanny.get_resource_limit("diskused"):
        raise ResourceException, "Disk use '"+str(diskused)+"' over limit '"+str(nanny.get_resource_limit("diskused"))+"'."

      # Send the disk usage information, raw bytes used
      write_message_to_pipe(pipe_handle, "diskused", diskused)
    
    ########### End Check Disk ###########
    
    # Sleep before the next iteration
    time.sleep(repy_constants.CPU_POLLING_FREQ_LINUX)


###########     functions that help me figure out the os type    ###########

# Calculates the system granularity
def calculate_granularity():
  global granularity

  if ostype in ["Windows", "WindowsCE"]:
    # The Granularity of getTickCount is 1 millisecond
    granularity = pow(10,-3)
    
  elif ostype == "Linux":
    # We don't know if the granularity is correct yet
    correct_granularity = False
    
    # How many times have we tested
    tests = 0
    
    # Loop while the granularity is incorrect, up to 10 times
    while not correct_granularity and tests <= 10:
      current_granularity = os_api.get_uptime_granularity()
      uptime_pre = os_api.get_system_uptime()
      time.sleep(current_granularity / 10)
      uptime_post = os_api.get_system_uptime()
    
      diff = uptime_post - uptime_pre
    
      correct_granularity = int(diff / current_granularity) == (diff / current_granularity)
      tests += 1
    
    granularity = current_granularity
    
  elif ostype == "Darwin":
    granularity = os_api.get_uptime_granularity()
    


# Call init_ostype!!!
harshexit.init_ostype()

ostype = harshexit.ostype
osrealtype = harshexit.osrealtype

# Import the proper system wide API
if osrealtype == "Linux":
  import linux_api as os_api
elif osrealtype == "Darwin":
  import darwin_api as os_api
elif osrealtype == "FreeBSD":
  import freebsd_api as os_api
elif ostype == "Windows" or ostype == "WindowsCE":
  # There is no real reason to do this, since windows is imported separately
  import windows_api as os_api
else:
  # This is a non-supported OS
  raise UnsupportedSystemException, "The current Operating System is not supported! Fatal Error."
  
# Set granularity
calculate_granularity()  

# For Windows, we need to initialize time.clock()
if ostype in ["Windows", "WindowsCE"]:
  time.clock()

# Initialize getruntime for other platforms 
else:
  # Set the starttime to the initial uptime
  starttime = getruntime()
  last_uptime = starttime

  # Reset elapsed time 
  elapsedtime = 0



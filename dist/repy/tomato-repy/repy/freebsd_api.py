"""
Author: Armon Dadgar
Start Date: April 7th, 2009

Description:
  This file provides a python interface to low-level system call on the Linux platform.
  It is designed to abstract away the C-level detail and provide a high-level method of doing
  common management tasks.

"""

import ctypes       # Allows us to make C calls
import ctypes.util  # Helps to find the C library

import os           # Provides some convenience functions
import time         # Provides time.time

import freebsd_kinfo  # Imports the kinfo structure, along with others

import nix_common_api as nix_api # Import the Common API

import textops      # Import the seattlelib textops library

import portable_popen  # Import for Popen

# Manually import the common functions we want
exists_outgoing_network_socket = nix_api.exists_outgoing_network_socket
exists_listening_network_socket = nix_api.exists_listening_network_socket
get_available_interfaces = nix_api.get_available_interfaces
get_ctypes_errno = nix_api.get_ctypes_errno
get_ctypes_error_str = nix_api.get_ctypes_error_str

# Get the standard library
libc = nix_api.libc

# Globals
# Cache the last process info struct so as to avoid redundant memory allocation
# and to fetch additional info without constantly updating
last_proc_info_struct = None
last_proc_info_size   = 0    # Stores the size of the struct

# Functions
_sysctl = libc.sysctl # Makes system calls
_clock_gettime = libc.clock_gettime # Get the CPU time

# Constants
CTL_KERN = 1
KERN_PROC = 14
KERN_PROC_PID = 1
FourIntegers = ctypes.c_int * 4 # A C array with 4 ints, used for syscalls
PAGE_SIZE = libc.getpagesize() # Call into libc to get our page size
KERN_BOOTTIME = 21
TwoIntegers = ctypes.c_int * 2 # C array with 2 ints
CLOCK_THREAD_CPUTIME_ID	= 14 # Get the CPU time for the current thread

# Structures
kinfo_proc = freebsd_kinfo.kinfo_proc # Import from the external file

class timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long),
                ("tv_usec", ctypes.c_long)]


def _get_proc_info_by_pid(pid):
  """
  <Purpose>
    Immediately updates the internal kinfo_proc structure.
  
  <Arguments>
    pid: The Process Identifier for which data should be retrieved
  
  <Exceptions>
    Raises an Exception if there is an error.
  
  <Returns>
    Nothing
  """
  global last_proc_info_struct
  global last_proc_info_size
  
  # Create the argument array
  mib = FourIntegers(CTL_KERN, KERN_PROC, KERN_PROC_PID, pid)
  
  # Check if we need to allocate a structure
  if last_proc_info_struct == None:
    # Allocate a kinfo structure
    last_proc_info_struct = kinfo_proc(0)
    last_proc_info_size  = ctypes.c_int(0)
    
    # Make a system call without a pointer to the kinfo structure, this sets
    # ths proper size of the structure for future system calls
    status = _sysctl(mib, 4, None, ctypes.byref(last_proc_info_size), None, 0)
    
    # Check the status
    if status != 0:
      raise Exception,"Fatal error with sysctl. Errno:"+str(get_ctypes_errno())+", Error: "+get_ctypes_error_str()
  
  
  # Make the call to update
  status = _sysctl(mib, 4, ctypes.byref(last_proc_info_struct), ctypes.byref(last_proc_info_size), None, 0)
  
  # Check the status
  if status != 0:
    raise Exception,"Fatal error with sysctl. Errno:"+str(get_ctypes_errno())+", Error: "+get_ctypes_error_str()
    

def get_process_cpu_time(pid):
  """
  <Purpose>
    Returns the total CPU time used by a process.

  <Arguments>
    pid: The process identifier for the process to query.

  <Exceptions>
    See _get_proc_info_by_pid.

  <Returns>
    The total cpu time.
  """
  global last_proc_info_struct
  
  # Update the info
  _get_proc_info_by_pid(pid)
  
  # Get the rusage field in the structure
  ru = last_proc_info_struct.ki_rusage
  
  # Calculate user time and system, for the process and its children,
  # divide by 1 million since the usec field is in microseconds
  utime = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec/1000000.0
  stime = ru.ru_stime.tv_sec + ru.ru_stime.tv_usec/1000000.0

  # Switch ru to the child structure
  ru = last_proc_info_struct.ki_rusage_ch

  utime_ch = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec/1000000.0
  stime_ch = ru.ru_stime.tv_sec + ru.ru_stime.tv_usec/1000000.0
  
  # Calculate the total time
  total_time = utime + stime + utime_ch + stime_ch
  
  return total_time



def get_process_rss(force_update=False, pid=None):
  """
  <Purpose>
    Returns the Resident Set Size of a process. By default, this will
    return the information cached by the last call to _get_proc_info_by_pid.
    This call is used in get_process_cpu_time.

  <Arguments>
    force_update:
      Allows the caller to force a data update, instead of using the cached data.

    pid:
      If force_update is True, this parameter must be specified to force the update.

  <Exceptions>
    See _get_proc_info_by_pid.

  <Returns>
    The RSS of the process in bytes.
  """
  global last_proc_info_struct
  
  # Check if an update is being forced
  if force_update and pid != None:
    # Update the info
    _get_proc_info_by_pid(pid)
  
  # Get RSS
  rss_pages = last_proc_info_struct.ki_rssize
  rss_bytes = rss_pages * PAGE_SIZE
  
  return rss_bytes



# Get the CPU time of the current thread
def get_current_thread_cpu_time():
  """
  <Purpose>
    Gets the total CPU time for the currently executing thread.

  <Exceptions>
    An AssertionError will be raised if the underlying system call fails.

  <Returns>
    A floating amount of time in seconds.
  """
  # Allocate a structure
  time_struct = timeval()

  # Make the system call
  result = _clock_gettime(CLOCK_THREAD_CPUTIME_ID, ctypes.byref(time_struct))

  # Sum up the CPU usage
  cpu_time = time_struct.tv_sec + time_struct.tv_usec / 1000000000.0

  # Safety check, result should be 0
  # Do the safety check after we free the memory to avoid leaks
  assert(result == 0)

  # Return the structure
  return cpu_time



# Return the timeval struct with our boottime
def _get_boottime_struct():
  # Get an array with 2 elements, set the syscall parameters
  mib = TwoIntegers(CTL_KERN, KERN_BOOTTIME)

  # Get timeval structure, set the size
  boottime = timeval()                
  size = ctypes.c_size_t(ctypes.sizeof(boottime))

  # Make the syscall
  libc.sysctl(mib, 2, ctypes.pointer(boottime), ctypes.pointer(size), None, 0)
  
  return boottime

def get_system_uptime():
  """
  <Purpose>
    Returns the system uptime.

  <Returns>
    The system uptime.  
  """
  # Get the boot time struct
  boottime = _get_boottime_struct()

  # Calculate uptime from current time
  uptime = time.time() - boottime.tv_sec+boottime.tv_usec*1.0e-6

  return uptime

def get_uptime_granularity():
  """
  <Purpose>
    Determines the granularity of the get_system_uptime call.

  <Returns>
    A numerical representation of the minimum granularity.
    E.g. 2 digits of granularity would return 0.01
  """
  # Get the boot time struct
  boottime = _get_boottime_struct()
  
  # Check if the number of nano seconds is 0
  if boottime.tv_usec == 0:
    granularity = 0
  
  else:
    # Convert nanoseconds to string
    nanosecondstr = str(boottime.tv_usec)
    
    # Justify with 0's to 9 digits
    nanosecondstr = nanosecondstr.rjust(9,"0")
    
    # Strip the 0's on the other side
    nanosecondstr = nanosecondstr.rstrip("0")
    
    # Get granularity from the length of the string
    granularity = len(nanosecondstr)

  # Convert granularity to a number
  return pow(10, 0-granularity)



def get_system_thread_count():
  """
  <Purpose>
    Returns the number of active threads running on the system.

  <Returns>
    The thread count.
  """

  # Use PS since it is can get the info for us
  process = portable_popen.Popen(["ps", "axH"])
  
  ps_output, _ = process.communicate()

  # Subtract 1 from the number of lines because the first line is a a table
  # header: "  PID TTY      STAT   TIME COMMAND"
  threads = len(textops.textops_rawtexttolines(ps_output)) - 1

  return threads



def get_interface_ip_addresses(interfaceName):
  """
  <Purpose>
    Returns the IP address associated with the interface.
  
  <Arguments>
    interfaceName: The string name of the interface, e.g. eth0
  
  <Returns>
    A list of IP addresses associated with the interface.
  """

  # Launch up a shell, get the feed back
  # We use ifconfig with the interface name.
  ifconfig_process = portable_popen.Popen(["/sbin/ifconfig", interfaceName.strip()])

  ifconfig_output, _ = ifconfig_process.communicate()
  ifconfig_lines = textops.textops_rawtexttolines(ifconfig_output)
  
  # Look for ipv4 addresses
  target_lines = textops.textops_grep("inet", ifconfig_lines)
  # and not ipv6
  target_lines = textops.textops_grep("inet6", target_lines, exclude=True)

  # Only take the ip(s)
  target_lines = textops.textops_cut(target_lines, delimiter=" ", fields=[1])

  # Create an array for the ip's
  ipaddressList = []
  
  for line in target_lines:
     # Strip the newline and any spacing
     line = line.strip("\n\t ")
     ipaddressList.append(line)

  # Done, return the interfaces
  return ipaddressList

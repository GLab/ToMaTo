"""
Author: Armon Dadgar
Start Date: April 7th, 2009

Description:
  This file provides a python interface to low-level system call on the Linux platform.
  It is designed to abstract away the C-level detail and provide a high-level method of doing
  common management tasks.

"""

import os           # Provides some convenience functions

import nix_common_api as nix_api # Import the Common API

import textops      # Import seattlelib's text processing lib
import portable_popen  # For Popen

import platform

# Determine if we are 32 bit or 64 bit
running_32bit = True
architecture = platform.architecture()
if "64" in architecture[0]:
  running_32bit = False

# Manually import the common functions we want
exists_outgoing_network_socket = nix_api.exists_outgoing_network_socket
exists_listening_network_socket = nix_api.exists_listening_network_socket
get_available_interfaces = nix_api.get_available_interfaces

# Libc
libc = nix_api.libc

# Functions
myopen = open # This is an annoying restriction of repy
syscall = libc.syscall # syscall function

# Globals
last_stat_data = None   # Store the last array of data from _get_proc_info_by_pid

# Constants
JIFFIES_PER_SECOND = 100.0
PAGE_SIZE = os.sysconf('SC_PAGESIZE')

# Get the thread id of the currently executing thread
if running_32bit:
  GETTID = 224 
else:
  GETTID = 186

# Maps each field in /proc/{pid}/stat to an index when split by spaces
FIELDS = {
"pid":0,
"state":1,
"ppid":2,
"pgrp":3,
"session":4,
"tty_nr":5,
"tpgid":6,
"flags":7,
"minflt":8,
"cminflt":9,
"majflt":10,
"cmajflt":11,
"utime":12,
"stime":13,
"cutime":14,
"cstime":15,
"priority":16,
"nice":17,
"num_threads":18,
"itrealvalue":19,
"starttime":20,
"vsize":21,
"rss":22,
"rlim":23,
"startcode":24,
"endcode":25,
"startstack":26,
"kstkesp":27,
"kstkeoip":28,
"signal":29,
"blocked":30,
"sigignore":31,
"sigcatch":32,
"wchan":33,
"nswap":34,
"cnswap":35,
"exit_signal":36,
"processor":37,
"rt_priority":38,
"policy":39,
"delayacct_blkio_ticks":40
}

# Process a /proc/PID/stat or /proc/PID/task/TID/stat file and returns it as an array
def _process_stat_file(file):
  # Get the file in proc
  fileo = myopen(file,"r")

  # Read in all the data
  data = fileo.read()

  # Close the file object
  fileo.close()

  # Strip the newline
  data = data.strip("\n")

  # Remove the substring that says "(python)", since it changes the field alignment
  start_index = data.find("(")
  if start_index != -1:
    end_index = data.find(")", start_index)
    data = data[:start_index-1] + data[end_index+1:]

  # Break the data into an array by spaces
  return data.split(" ")


def _get_proc_info_by_pid(pid):
  """
  <Purpose>
    Reads in the data from a process stat file, and stores it
  
  <Arguments>
    pid: The process identifier for which data should be fetched.  
  """
  global last_stat_data

  # Get the file in proc
  file = "/proc/"+str(pid)+"/stat"

  # Process the status file
  last_stat_data = _process_stat_file(file)
  
  # Check the state, raise an exception if the process is a zombie
  if "Z" in last_stat_data[FIELDS["state"]]:
    raise Exception, "Queried Process is a zombie (dead)!"
  
  
def get_process_cpu_time(pid):
  """
  <Purpose>
    Returns the total CPU time used by a process.
    
  <Arguments>
    pid: The process identifier for the process to query.
  
  <Returns>
    The total cpu time.
  """
  global last_stat_data
  
  # Update our data
  _get_proc_info_by_pid(pid)
  
  # Get the raw usertime and system time
  total_time_raw = int(last_stat_data[FIELDS["utime"]])+int(last_stat_data[FIELDS["stime"]])
  
  # Adjust by the number of jiffies per second
  total_time = total_time_raw / JIFFIES_PER_SECOND
  
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

  <Returns>
    The RSS of the process in bytes.
  """
  global last_stat_data

  # Check if an update is being forced
  if force_update and pid != None:
    # Update the info
    _get_proc_info_by_pid(pid)

  # Fetch the RSS, convert to an integer
  rss_pages = int(last_stat_data[FIELDS["rss"]])
  rss_bytes = rss_pages * PAGE_SIZE

  # Return the info
  return rss_bytes


# Get the id of the currently executing thread
def _get_current_thread_id():
  # Syscall for GETTID
  return syscall(GETTID)


# Get the CPU time of the current thread
def get_current_thread_cpu_time():
  """
  <Purpose>
    Gets the total CPU time for the currently executing thread.

  <Exceptions>
    An exception will be raised if something goes wrong.

  <Returns>
    A floating amount of time in seconds.
  """
  # Get the thread id
  thread_id = _get_current_thread_id()

  # Get our pid
  pid = os.getpid()

  # Get the file with our status
  file = "/proc/"+str(pid)+"/task/"+str(thread_id)+"/stat"

  # Process the status file
  thread_stat_data = _process_stat_file(file)

  # Get the raw usertime and system time
  total_time_raw = int(thread_stat_data[FIELDS["utime"]])+int(thread_stat_data[FIELDS["stime"]])
  
  # Adjust by the number of jiffies per second
  total_time = total_time_raw / JIFFIES_PER_SECOND

  # Return the total time
  return total_time


def get_system_uptime():
  """
  <Purpose>
    Returns the system uptime.

  <Exception>
    Raises Exception if /proc/uptime is unavailable
    
  <Returns>
    The system uptime.  
  """
  if os.path.exists("/proc/uptime"):
    # Open the file
    fh = myopen('/proc/uptime', 'r')
    
    # Read in the whole file
    data = fh.read() 
    
    # Split the file by commas, grap the first number and convert to a float
    uptime = float(data.split(" ")[0])
    
    # Close the file
    fh.close()
    
    return uptime
  else:
    raise Exception, "Could not find /proc/uptime!"
  
def get_uptime_granularity():
  """
  <Purpose>
    Determines the granularity of the get_system_uptime call.
  
  <Exception>
    Raises Exception if /proc/uptime is unavailable
        
  <Returns>
    A numerical representation of the minimum granularity.
    E.g. 2 digits of granularity would return 0.01
  """
  if os.path.exists("/proc/uptime"):
    # Open the file
    fh = myopen('/proc/uptime', 'r')
  
    # Read in the whole file
    data = fh.read()
  
    # Split the file by commas, grap the first number
    uptime = data.split(" ")[0]
    uptime_digits = len(uptime.split(".")[1])
  
    # Close the file
    fh.close()
  
    granularity = uptime_digits
    
    # Convert granularity to a number
    return pow(10, 0-granularity)
  else:
    raise Exception, "Could not find /proc/uptime!"  


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
  target_lines = textops.textops_cut(target_lines, delimiter=":", fields=[1])
  target_lines = textops.textops_cut(target_lines, delimiter=" ", fields=[0])

  # Create an array for the ip's
  ipaddressList = []
  
  for line in target_lines:
     # Strip the newline and any spacing
     line = line.strip("\n\t ")
     ipaddressList.append(line)

  # Done, return the interfaces
  return ipaddressList

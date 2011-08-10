"""

Author: Armon Dadgar
Start Date: April 16th, 2009
Description:
  Houses code which is common between the Linux, Darwin, and FreeBSD API's to avoid redundancy.

"""

import ctypes       # Allows us to make C calls
import ctypes.util  # Helps to find the C library

# Import for Popen
import portable_popen

# Seattlelib text-processing library (not a Python stdlib):
import textops

# Get the standard library
libc = ctypes.CDLL(ctypes.util.find_library("c"))

# Functions
_strerror = libc.strerror
_strerror.restype = ctypes.c_char_p

# This functions helps to conveniently retrieve the errno
# of the last call. This is a bit tedious to do, since 
# Python doesn't understand that this is a globally defined int
def get_ctypes_errno():
  errno_pointer = ctypes.cast(libc.errno, ctypes.POINTER(ctypes.c_int))
  err_val = errno_pointer.contents
  return err_val.value

# Returns the string version of the errno  
def get_ctypes_error_str():
  errornum = get_ctypes_errno()
  return _strerror(errornum)


def exists_outgoing_network_socket(localip, localport, remoteip, remoteport):
  """
  <Purpose>
    Determines if there exists a network socket with the specified unique tuple.
    Assumes TCP.

  <Arguments>
    localip: The IP address of the local socket
    localport: The port of the local socket
    remoteip:  The IP of the remote host
    remoteport: The port of the remote host
    
  <Returns>
    A Tuple, indicating the existence and state of the socket. E.g. (Exists (True/False), State (String or None))

  """
  # This only works if all are not of the None type
  if not (localip and localport and remoteip and remoteport):
    return (False, None)

  # Grab netstat output.
  netstat_process = portable_popen.Popen(["netstat", "-an"])
  netstat_stdout, _ = netstat_process.communicate()
  netstat_lines = textops.textops_rawtexttolines(netstat_stdout)

  # Search for things matching the local and remote ip+port we are trying to get
  # information about.
  target_lines = textops.textops_grep(localip + ':' + str(localport), netstat_lines) + \
      textops.textops_grep(localip + '.' + str(localport), netstat_lines)

  target_lines = textops.textops_grep(remoteip + ':' + str(remoteport), target_lines) + \
      textops.textops_grep(remoteip + '.' + str(remoteport), target_lines)

  # Only tcp connections.
  target_lines = textops.textops_grep('tcp', target_lines)
  
  # Check if there is any entries
  if len(target_lines) > 0:
    line = target_lines[0]
    # Replace tabs with spaces, explode on spaces
    parts = line.replace("\t","").strip("\n").split()
    # Get the state
    socket_state = parts[-1]
      
    return (True, socket_state)

  else:
    return (False, None)




def exists_listening_network_socket(ip, port, tcp):
  """
  <Purpose>
    Determines if there exists a network socket with the specified ip and port which is the LISTEN state.
  
  <Arguments>
    ip: The IP address of the listening socket
    port: The port of the listening socket
    tcp: Is the socket of TCP type, else UDP
    
  <Returns>
    True or False.
  """
  # This only works if both are not of the None type
  if not (ip and port):
    return False
  
  # UDP connections are stateless, so for TCP check for the LISTEN state
  # and for UDP, just check that there exists a UDP port
  if tcp:
    grep_terms = ["tcp", "LISTEN"]
  else:
    grep_terms = ["udp"]

  # Launch up a shell, get the feedback
  netstat_process = portable_popen.Popen(["netstat", "-an"])
  netstat_stdout, _ = netstat_process.communicate()
  netstat_lines = textops.textops_rawtexttolines(netstat_stdout)

  # Search for things matching the ip+port we are trying to get
  # information about.
  target_lines = textops.textops_grep(ip + ':' + str(port), netstat_lines) + \
      textops.textops_grep(ip + '.' + str(port), netstat_lines)

  for term in grep_terms:
    target_lines = textops.textops_grep(term, target_lines)

  number_of_sockets = len(target_lines)
  
  return (number_of_sockets > 0)


def get_available_interfaces():
  """
  <Purpose>
    Returns a list of available network interfaces.
  
  <Returns>
    An array of string interfaces
  """
  # Common headers
  # This list contains common header elements so that they can be stripped
  common_headers_list = ["Name", "Kernel", "Iface"]
  
  # Netstat will return all interfaces, but also has some duplication.
  # Cut will get the first field from each line, which is the interface name.
  # Sort prepares the input for uniq, which only works on sorted lists.
  # Uniq, is somewhat obvious, it will only return the unique interfaces to remove duplicates.
  # Launch up a shell, get the feedback
  netstat_process = portable_popen.Popen(["netstat", "-i"])
  netstat_stdout, _ = netstat_process.communicate()
  netstat_lines = textops.textops_rawtexttolines(netstat_stdout)

  target_lines = textops.textops_cut(netstat_lines, delimiter=" ", fields=[0])

  unique_lines = set(target_lines)

  # Create an array for the interfaces
  interfaces_list = []
  
  for line in unique_lines:
    # Strip the newline
    line = line.strip("\n")
    # Check if this is a header
    if line in common_headers_list:
      continue
    interfaces_list.append(line)
  
  # Done, return the interfaces
  return interfaces_list

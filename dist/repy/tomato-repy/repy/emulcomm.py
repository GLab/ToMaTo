"""
   Author: Justin Cappos, Armon Dadgar

   Start Date: 27 June 2008

   Description:

   This is a collection of communications routines that provide a programmer 
   with a reasonable environment.   This is used by repy.py to provide a 
   highly restricted (but usable) environment.
"""

import socket

# Armon: Used to check if a socket is ready
import select

# socket uses getattr and setattr.   We need to make these available to it...
socket.getattr = getattr
socket.setattr = setattr


# needed to set threads for recvmess and waitforconn
import threading
# threading in python2.7 uses hasattr. It needs to be made available.
threading.hasattr = hasattr


# So I can exit all threads when an error occurs or do select
import harshexit

# Needed for finding out info about sockets, available interfaces, etc
import nonportable

# So I can print a clean traceback when an error happens
import tracebackrepy

# accounting
# id(sock) will be used to register and unregister sockets with nanny 
import nanny

# give me uniqueIDs for the comminfo table
import idhelper

# for sleep
import time 

# Armon: Used for decoding the error messages
import errno

# Armon: Used for getting the constant IP values for resolving our external IP
import repy_constants 

# Get the exceptions
from exception_hierarchy import *

###### Module Data

# This is a library of all currently bound sockets. Since multiple 
# UDP bindings on a single port is hairy, we store bound sockets 
# here, and use them for both sending and receiving if they are 
# available. This feels slightly byzantine, but it allows us to 
# avoid modifying the repy API.
#
# Format of entries is as follows:
# Key - 3-tuple of ("UDP", IP, Port)
# Val - Bound socket object
_BOUND_SOCKETS = {} # Ticket = 1015 (Resolved)

# If we have a preference for an IP/Interface this flag is set to True
user_ip_interface_preferences = False

# Do we allow non-specified IPs
allow_nonspecified_ips = True

# Armon: Specified the list of allowed IP and Interfaces in order of their preference
# The basic structure is list of tuples (IP, Value), IP is True if its an IP, False if its an interface
user_specified_ip_interface_list = []

# This list caches the allowed IP's
# It is updated at the launch of repy, or by calls to getmyip and update_ip_cache
# NOTE: The loopback address 127.0.0.1 is always permitted. update_ip_cache will always add this
# if it is not specified explicitly by the user
allowediplist = []
cachelock = threading.Lock()  # This allows only a single simultaneous cache update


##### Internal Functions

# Determines if a specified IP address is allowed in the context of user settings
def _ip_is_allowed(ip):
  """
  <Purpose>
    Determines if a given IP is allowed, by checking against the cached allowed IP's.
  
  <Arguments>
    ip: The IP address to search for.
  
  <Returns>
    True, if allowed. False, otherwise.
  """
  global allowediplist
  global user_ip_interface_preferences
  global allow_nonspecified_ips
  
  # If there is no preference, anything goes
  # same with allow_nonspecified_ips
  if not user_ip_interface_preferences or allow_nonspecified_ips:
    return True
  
  # Check the list of allowed IP's
  return (ip in allowediplist)


# Only appends the elem to lst if the elem is unique
def _unique_append(lst, elem):
  if elem not in lst:
    lst.append(elem)
      
# This function updates the allowed IP cache
# It iterates through all possible IP's and stores ones which are bindable as part of the allowediplist
def update_ip_cache():
  global allowediplist
  global user_ip_interface_preferences
  global user_specified_ip_interface_list
  global allow_nonspecified_ips
  
  # If there is no preference, this is a no-op
  if not user_ip_interface_preferences:
    return
    
  # Acquire the lock to update the cache
  cachelock.acquire()
  
  # If there is any exception release the cachelock
  try:  
    # Stores the IP's
    allowed_list = []
  
    # Iterate through the allowed list, handle each element
    for (is_ip_addr, value) in user_specified_ip_interface_list:
      # Handle normal IP's
      if is_ip_addr:
        _unique_append(allowed_list, value)
    
      # Handle interfaces
      else:
        try:
          # Get the IP's associated with the NIC
          interface_ips = nonportable.os_api.get_interface_ip_addresses(value)
          for interface_ip in interface_ips:
            _unique_append(allowed_list, interface_ip)
        except:
          # Catch exceptions if the NIC does not exist
          pass
  
    # This will store all the IP's that we are able to bind to
    bindable_list = []
        
    # Try binding to every ip
    for ip in allowed_list:
      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      try:
        sock.bind((ip,0))
      except:
        pass # Not a good ip, skip it
      else:
        bindable_list.append(ip) # This is a good ip, store it
      finally:
        sock.close()

    # Add loopback
    _unique_append(bindable_list, "127.0.0.1")
  
    # Update the global cache
    allowediplist = bindable_list
  
  finally:      
    # Release the lock
    cachelock.release()
 

############## General Purpose socket functions ##############

def _is_already_connected_exception(exceptionobj):
  """
  <Purpose>
    Determines if a given error number indicates that the socket
    is already connected.

  <Arguments>
    An exception object from a network call.

  <Returns>
    True if already connected, false otherwise
  """
  # Get the type
  exception_type = type(exceptionobj)

  # Only continue if the type is socket.error
  if exception_type is not socket.error:
    return False

  # Get the error number
  errnum = exceptionobj[0]

  # Store a list of error messages meaning we are connected
  connected_errors = ["EISCONN", "WSAEISCONN"]

  # Convert the errno to and error string name
  try:
    errname = errno.errorcode[errnum]
  except Exception,e:
    # The error is unknown for some reason...
    errname = None
  
  # Return if the error name is in our white list
  return (errname in connected_errors)


def _is_addr_in_use_exception(exceptionobj):
  """
  <Purpose>
    Determines if a given error number indicates that the provided
    localip / localport are already bound and that the unique
    tuple is already in use.

  <Arguments>
    An exception object from a network call.

  <Returns>
    True if already in use, false otherwise
  """
  # Get the type
  exception_type = type(exceptionobj)

  # Only continue if the type is socket.error
  if exception_type is not socket.error:
    return False

  # Get the error number
  errnum = exceptionobj[0]

  # Store a list of error messages meaning we are in use
  in_use_errors = ["EADDRINUSE", "WSAEADDRINUSE"]

  # Convert the errno to and error string name
  try:
    errname = errno.errorcode[errnum]
  except Exception,e:
    # The error is unknown for some reason...
    errname = None
  
  # Return if the error name is in our white list
  return (errname in in_use_errors)


def _is_addr_unavailable_exception(exceptionobj):
  """
  <Purpose>
    Determines if a given error number indicates that the provided
    localip is not available during a bind() call.
    This indicates an AddressBindingError should be raised.

  <Arguments>
    An exception object from a network call.

  <Returns>
    True if already in use, false otherwise
  """
  # Get the type
  exception_type = type(exceptionobj)

  # Only continue if the type is socket.error
  if exception_type is not socket.error:
    return False

  # Get the error number
  errnum = exceptionobj[0]

  # Store a list of error messages meaning the address is not available
  not_avail_errors = ["EADDRNOTAVAIL", "WSAEADDRNOTAVAIL"]

  # Convert the errno to and error string name
  try:
    errname = errno.errorcode[errnum]
  except Exception,e:
    # The error is unknown for some reason...
    errname = None
  
  # Return if the error name is in our white list
  return (errname in not_avail_errors)


def _is_conn_refused_exception(exceptionobj):
  """
  <Purpose>
    Determines if a given error number indicates that the remote
    host has actively refused the connection. E.g.
    ECONNREFUSED

  <Arguments>
    An exception object from a network call.

  <Returns>
    True if the error indicates the connection was refused, false otherwise
  """
  # Get the type
  exception_type = type(exceptionobj)

  # Only continue if the type is socket.error
  if exception_type is not socket.error:
    return False

  # Get the error number
  errnum = exceptionobj[0]

  # Store a list of error messages meaning the host refused
  refused_errors = ["ECONNREFUSED", "WSAECONNREFUSED"]

  # Convert the errno to and error string name
  try:
    errname = errno.errorcode[errnum]
  except Exception,e:
    # The error is unknown for some reason...
    errname = None
  
  # Return if the error name is in our white list
  return (errname in refused_errors)


def _is_network_down_exception(exceptionobj):
  """
  <Purpose>
    Determines if a given error number indicates that the
    network is down.

  <Arguments>
    An exception object from a network call.

  <Returns>
    True if the network is down, false otherwise
  """
  # Get the type
  exception_type = type(exceptionobj)

  # Only continue if the type is socket.error
  if exception_type is not socket.error:
    return False

  # Get the error number
  errnum = exceptionobj[0]

  # Store a list of error messages meaning we are disconnected
  net_down_errors = ["ENETDOWN","ENETUNREACH","WSAENETDOWN", "WSAENETUNREACH"]

  # Convert the errno to and error string name
  try:
    errname = errno.errorcode[errnum]
  except Exception,e:
    # The error is unknown for some reason...
    errname = None
  
  # Return if the error name is in our white list
  return (errname in net_down_errors)


def _is_recoverable_network_exception(exceptionobj):
  """
  <Purpose>
    Determines if a given error number is recoverable or fatal.

  <Arguments>
    An exception object from a network call.

  <Returns>
    True if potentially recoverable, False if fatal.
  """
  # Get the type
  exception_type = type(exceptionobj)

  # socket.timeout is recoverable always
  if exception_type == socket.timeout:
    return True

  # Only continue if the type is socket.error or select.error
  elif exception_type != socket.error and exception_type != select.error:
    return False
  
  # Get the error number
  errnum = exceptionobj[0]

  # Store a list of recoverable error numbers
  recoverable_errors = ["EINTR","EAGAIN","EBUSY","EWOULDBLOCK","ETIMEDOUT","ERESTART",
                        "WSAEINTR","WSAEWOULDBLOCK","WSAETIMEDOUT","EALREADY","WSAEALREADY",
                       "EINPROGRESS","WSAEINPROGRESS"]

  # Convert the errno to and error string name
  try:
    errname = errno.errorcode[errnum]
  except Exception,e:
    # The error is unknown for some reason...
    errname = None
  
  # Return if the error name is in our white list
  return (errname in recoverable_errors)


# Determines based on exception if the connection has been terminated
def _is_terminated_connection_exception(exceptionobj):
  """
  <Purpose>
    Determines if the exception is indicated the connection is terminated.

  <Arguments>
    An exception object from a network call.

  <Returns>
    True if the connection is terminated, False otherwise.
    False means we could not determine with certainty if the socket is closed.
  """
  # Get the type
  exception_type = type(exceptionobj)

  # We only want to continue if it is socket.error or select.error
  if exception_type != socket.error and exception_type != select.error:
    return False

  # Get the error number
  errnum = exceptionobj[0]

  # Store a list of errors which indicate connection closed
  connection_closed_errors = ["EPIPE","EBADF","EBADR","ENOLINK","EBADFD","ENETRESET",
                              "ECONNRESET","WSAEBADF","WSAENOTSOCK","WSAECONNRESET",]

  # Convert the errnum to an error string
  try:
    errname = errno.errorcode[errnum]
  except:
    # The error number is not defined...
    errname = None

  # Return whether the errname is in our pre-defined list
  return (errname in connection_closed_errors)



# Armon: This is used for semantics, to determine if we have a valid IP.
def _is_valid_ip_address(ipaddr):
  """
  <Purpose>
    Determines if ipaddr is a valid IP address.
    0.X and 224-255.X addresses are not allowed.
    Additionally, 192.168.0.0 is not allowed.

  <Arguments>
    ipaddr: String to check for validity. (It will check that this is a string).

  <Returns>
    True if a valid IP, False otherwise.
  """
  # Argument must be of the string type
  if not type(ipaddr) == str:
    return False

  if ipaddr == '192.168.0.0':
    return False

  # A valid IP should have 4 segments, explode on the period
  octets = ipaddr.split(".")

  # Check that we have 4 parts
  if len(octets) != 4:
    return False

  # Check that each segment is a number between 0 and 255 inclusively.
  for octet in octets:
    # Attempt to convert to an integer
    try:
      ipnumber = int(octet)
    except ValueError:
      # There was an error converting to an integer, not an IP
      return False

    # IP addresses octets must be between 0 and 255
    if not (ipnumber >= 0 and ipnumber <= 255):
      return False

  # should not have a ValueError (I already checked)
  firstipnumber = int(octets[0])

  # IP addresses with the first octet 0 refer to all local IPs.   These are
  # not allowed
  if firstipnumber == 0:
    return False

  # IP addresses with the first octet >=224 are either Multicast or reserved.
  # These are not allowed
  if firstipnumber >= 224:
    return False

  # At this point, assume the IP is valid
  return True


# Armon: This is used for semantics, to determine if the given port is valid
def _is_valid_network_port(port):
  """
  <Purpose>
    Determines if a given network port is valid. 

  <Arguments>
    port: A numeric type (this will be checked) port number.

  <Returns>
    True if valid, False otherwise.
  """
  # Check the type is int or long
  if not (type(port) == long or type(port) == int):
    return False

  if port >= 1 and port <= 65535:
    return True
  else:
    return False


# Used to decide if an IP is the loopback IP or not.   This is needed for 
# accounting
def _is_loopback_ipaddr(host):
  if not host.startswith('127.'):
    return False
  if len(host.split('.')) != 4:
    return False

  octets = host.split('.')
  if len(octets) != 4:
    return False
  for octet in octets:
    try:
      if int(octet) > 255 or int(octet) < 0:
        return False
    except ValueError:
      return False
 
  return True


# Checks if binding to the local port is allowed
# type should be "TCP" or "UDP".
def _is_allowed_localport(type, localport):
  # Switch to the proper resource
  if type == "TCP":
    resource = "connport"
  elif type == "UDP":
    resource = "messport"
  else:
    raise InternalRepyError("Bad type specified for _is_allowed_localport()")

  # Check what is allowed by nanny
  return nanny.is_item_allowed(resource, float(localport))




######################### Simple Public Functions ##########################



# Public interface
def gethostbyname(name):
  """
   <Purpose>
      Provides information about a hostname. Calls socket.gethostbyname().
      Translate a host name to IPv4 address format. The IPv4 address is
      returned as a string, such as '100.50.200.5'. If the host name is an
      IPv4 address itself it is returned unchanged.

   <Arguments>
     name:
         The host name to translate.

   <Exceptions>
     RepyArgumentError (descends from NetworkError) if the name is not a string
     NetworkAddressError (descends from NetworkError) if the address cannot
     be resolved.

   <Side Effects>
     None.

   <Resource Consumption>
     This operation consumes network bandwidth of 4K netrecv, 1K netsend.
     (It's hard to tell how much was actually sent / received at this level.)

   <Returns>
     The IPv4 address as a string.
  """

  if type(name) is not str:
    raise RepyArgumentError("gethostbyname() takes a string as argument.")

  # charge 4K for a look up...   I don't know the right number, but we should
  # charge something.   We'll always charge to the netsend interface...
  nanny.tattle_quantity('netsend', 1024) 
  nanny.tattle_quantity('netrecv', 4096)

  try:
    return socket.gethostbyname(name)
  except socket.gaierror:
    raise NetworkAddressError("The hostname '"+name+"' could not be resolved.")



# Public interface
def getmyip():
  """
   <Purpose>
      Provides the IP of this computer on its public facing interface.  
      Does some clever trickery. 

   <Arguments>
      None

   <Exceptions>
      InternetConnectivityError is the host is not connected to the internet.

   <Side Effects>
      None.

   <Resource Consumption>
      This operations consumes 256 netsend and 128 netrecv.

   <Returns>
      The localhost's IP address
  """
  # Charge for the resources
  nanny.tattle_quantity("netsend", 256)
  nanny.tattle_quantity("netrecv", 128)

  # I got some of this from: http://groups.google.com/group/comp.lang.python/browse_thread/thread/d931cdc326d7032b?hl=en
  
  # Update the cache and return the first allowed IP
  # Only if a preference is set
  if user_ip_interface_preferences:
    update_ip_cache()
    # Return the first allowed ip, there is always at least 1 element (loopback)
    return allowediplist[0]

  # Initialize these to None, so we can detect a failure
  myip = None
  
  # It's possible on some platforms (Windows Mobile) that the IP will be
  # 0.0.0.0 even when I have a public IP and the external IP is up. However, if
  # I get a real connection with SOCK_STREAM, then I should get the real
  # answer.
        
  # Try each stable IP  
  for ip_addr in repy_constants.STABLE_PUBLIC_IPS:  
    try:
      # Try to resolve using the current connection type and 
      # stable IP, using port 80 since some platforms panic
      # when given 0 (FreeBSD)
      myip = _get_localIP_to_remoteIP(socket.SOCK_DGRAM, ip_addr, 80)
    except (socket.error, socket.timeout):
      # We can ignore any networking related errors, since we want to try 
      # the other connection types and IP addresses. If we fail,
      # we will eventually raise an exception anyways.
      pass
    else:
      # Return immediately if the IP address is good
      if _is_valid_ip_address(myip): 
        return myip


  # Since we haven't returned yet, we must have failed.
  # Raise an exception, we must not be connected to the internet
  raise InternetConnectivityError("Cannot detect a connection to the Internet.")



def _get_localIP_to_remoteIP(connection_type, external_ip, external_port=80):
  """
  <Purpose>
    Resolve the local ip used when connecting outbound to an external ip.
  
  <Arguments>
    connection_type:
      The type of connection to attempt. See socket.socket().
    
    external_ip:
      The external IP to attempt to connect to.
      
    external_port:
      The port on the remote host to attempt to connect to.
  
  <Exceptions>
    As with socket.socket(), socketobj.connect(), etc.
  
  <Returns>
    The locally assigned IP for the connection.
  """
  # Open a socket
  sockobj = socket.socket(socket.AF_INET, connection_type)

  # Make sure that the socket obj doesn't hang forever in 
  # case connect() is blocking. Fix to #1003
  sockobj.settimeout(1.0)

  try:
    sockobj.connect((external_ip, external_port))

    # Get the local connection information for this socket
    (myip, localport) = sockobj.getsockname()
      
  # Always close the socket
  finally:
    sockobj.close()
  
  return myip




###################### Shared message / connection items ###################




# Armon: How frequently should we check for the availability of the socket?
RETRY_INTERVAL = 0.2 # In seconds


def _cleanup_socket(self):
  """
  <Purpose>
    Internal cleanup method for open sockets. The socket
    lock for the socket should be acquired prior to
    calling.

  <Arguments>
    None
  <Side Effects>
    The insocket/outsocket handle will be released.

  <Exceptions>
    InternalRepyError is raised if the socket lock is not held
    prior to calling the function.

  <Returns>
    None
  """
  sock = self.socketobj
  socket_lock = self.sock_lock
  # Make sure the lock is already acquired
  # BUG: We don't know which thread exactly acquired the lock.
  if socket_lock.acquire(False):
    socket_lock.release()
    raise InternalRepyError("Socket lock should be acquired before calling _cleanup_socket!")

  if (sock == None):  
    # Already cleaned up
    return
  # Shutdown the socket for writing prior to close
  # to unblock any threads that are writing
  try:
    sock.shutdown(socket.SHUT_WR)
  except:
    pass

  # Close the socket
  try:
    sock.close()
  except:
    pass
  # socket id is used to unregister socket with nanny
  sockid = id(sock)
  # Re-store resources
  nanny.tattle_remove_item('insockets', sockid)
  nanny.tattle_remove_item('outsockets', sockid)


####################### Message sending #############################



# Public interface!!!
def sendmessage(destip, destport, message, localip, localport):
  """
   <Purpose>
      Send a message to a host / port

   <Arguments>
      destip:
         The host to send a message to
      destport:
         The port to send the message to
      message:
         The message to send
      localhost:
         The local IP to send the message from 
      localport:
         The local port to send the message from

   <Exceptions>
      AddressBindingError (descends NetworkError) when the local IP isn't
        a local IP.

      ResourceForbiddenError (descends ResourceException?) when the local
        port isn't allowed

      RepyArgumentError when the local IP and port aren't valid types
        or values

      AlreadyListeningError if there is an existing listening UDP socket
      on the same local IP and port.

      DuplicateTupleError if there is another sendmessage on the same
      local IP and port to the same remote host.

   <Side Effects>
      None.

   <Resource Consumption>
      This operation consumes 64 bytes + number of bytes of the message that
      were transmitted. This requires that the localport is allowed.

   <Returns>
      The number of bytes sent on success
  """
  # Check the input arguments (type)
  if type(destip) is not str:
    raise RepyArgumentError("Provided destip must be a string!")
  if type(localip) is not str:
    raise RepyArgumentError("Provided localip must be a string!")

  if type(destport) is not int:
    raise RepyArgumentError("Provided destport must be an int!")
  if type(localport) is not int:
    raise RepyArgumentError("Provided localport must be an int!")

  if type(message) is not str:
    raise RepyArgumentError("Provided message must be a string!")


  # Check the input arguments (sanity)
  if not _is_valid_ip_address(destip):
    raise RepyArgumentError("Provided destip is not valid! IP: '"+destip+"'")
  if not _is_valid_ip_address(localip):
    raise RepyArgumentError("Provided localip is not valid! IP: '"+localip+"'")

  if not _is_valid_network_port(destport):
    raise RepyArgumentError("Provided destport is not valid! Port: "+str(destport))
  if not _is_valid_network_port(localport):
    raise RepyArgumentError("Provided localport is not valid! Port: "+str(localport))


  # Check that if localip == destip, then localport != destport
  if localip == destip and localport == destport:
    raise RepyArgumentError("Local socket name cannot match destination socket name! Local/Dest IP and Port match.")

  # Check the input arguments (permission)
  update_ip_cache()
  if not _ip_is_allowed(localip):
    raise ResourceForbiddenError("Provided localip is not allowed! IP: "+localip)

  if not _is_allowed_localport("UDP", localport):
    raise ResourceForbiddenError("Provided localport is not allowed! Port: "+str(localport))

  # Wait for netsend
  if _is_loopback_ipaddr(destip):
    nanny.tattle_quantity('loopsend', 0)
  else:
    nanny.tattle_quantity('netsend', 0)

  try:
    sock = None

    if ("UDP", localip, localport) in _BOUND_SOCKETS:
      sock = _BOUND_SOCKETS[("UDP", localip, localport)]       
    else:
      # Get the socket
      sock = _get_udp_socket(localip, localport)      
      # Register this socket with nanny
      nanny.tattle_add_item("outsockets", id(sock))
    # Send the message
    bytessent = sock.sendto(message, (destip, destport))

    # Account for the resources
    if _is_loopback_ipaddr(destip):
      nanny.tattle_quantity('loopsend', bytessent + 64)
    else:
      nanny.tattle_quantity('netsend', bytessent + 64)

    return bytessent

  except Exception, e:
        
    try:
      # If we're borrowing the socket, closing is not appropriate.
      if not ("UDP", localip, localport) in _BOUND_SOCKETS:
        sock.close()
    except:
      pass

    # Check if address is already in use
    if _is_addr_in_use_exception(e):
      raise DuplicateTupleError("Provided Local IP and Local Port is already in use!")
 
    if _is_addr_unavailable_exception(e):
      raise AddressBindingError("Cannot bind to the specified local ip, invalid!")

    # Unknown error...
    else:
      raise




# Public interface!!!
def listenformessage(localip, localport):
  """
    <Purpose>
        Sets up a UDPServerSocket to receive incoming UDP messages.

    <Arguments>
        localip:
            The local IP to register the handler on.
        localport:
            The port to listen on.

    <Exceptions>
        DuplicateTupleError (descends NetworkError) if the port cannot be
        listened on because some other process on the system is listening on
        it.

        AlreadyListeningError if there is already a UDPServerSocket with the same
        IP and port.

        RepyArgumentError if the port number or ip is wrong type or obviously
        invalid.

        AddressBindingError (descends NetworkError) if the IP address isn't a
        local IP.

        ResourceForbiddenError if the port is not allowed.

    <Side Effects>
        Prevents other UDPServerSockets from using this port / IP

    <Resource Consumption>
        This operation consumes an insocket and requires that the provided messport is allowed.

    <Returns>
        The UDPServerSocket.
  """
  # Check the input arguments (type)
  if type(localip) is not str:
    raise RepyArgumentError("Provided localip must be a string!")

  if type(localport) is not int:
    raise RepyArgumentError("Provided localport must be a int!")


  # Check the input arguments (sanity)
  if not _is_valid_ip_address(localip):
    raise RepyArgumentError("Provided localip is not valid! IP: '"+localip+"'")

  if not _is_valid_network_port(localport):
    raise RepyArgumentError("Provided localport is not valid! Port: "+str(localport))


  # Check the input arguments (permission)
  update_ip_cache()
  if not _ip_is_allowed(localip):
    raise ResourceForbiddenError("Provided localip is not allowed! IP: '"+localip+"'")

  if not _is_allowed_localport("UDP", localport):
    raise ResourceForbiddenError("Provided localport is not allowed! Port: "+str(localport))
  # This identity tuple will be used to check for an existing connection with same identity
  identity = ("UDP", localip, localport, None, None)

  try:
    # Check if localip is on loopback
    on_loopback = _is_loopback_ipaddr(localip) 

    # Get the socket
    sock = _get_udp_socket(localip,localport)
    
    # Register this socket as an insocket
    nanny.tattle_add_item('insockets',id(sock))

    # Add the socket to _BOUND_SOCKETS so that we can 
    # preserve send functionality on this port.
    _BOUND_SOCKETS[("UDP", localip, localport)] = sock

  except Exception, e:    

    # Check if this an already in use error
    if _is_addr_in_use_exception(e):  
    # Call _conn_cleanup_check to determine if this is because
    # the socket is being cleaned up or if it is actively being used or
    # if there is an existing listening socket 
    # This will always raise DuplicateTupleError or
    # CleanupInProgressError or AlreadyListeningError  
      _conn_cleanup_check(identity)

    # Check if this is a binding error
    if _is_addr_unavailable_exception(e):
      raise AddressBindingError("Cannot bind to the specified local ip, invalid!")

    # Unknown error...
    else:
      raise
 
  # Create a UDPServerSocket
  server_sock = UDPServerSocket(sock, on_loopback)

  # Return the UDPServerSocket
  return server_sock
  


####################### Connection oriented #############################
def _conn_alreadyexists_check(identity):
  """
  <Purpose>
    This private function checks if a socket that
    got EADDRINUSE is because the socket is active,
    or not

  <Arguments>
    identity: A tuple to check for cleanup

  <Exceptions>
    Raises DuplicateTupleError if the socket is actively being used.

    Raises AddressBindingError if the binding is not allowed 

  <Returns>
    None
  """
  # Decompose the tuple
  family, localip, localport, desthost, destport = identity
  
  # Check the sockets status
  (exists, status) = nonportable.os_api.exists_outgoing_network_socket(localip,localport,desthost,destport)

  # Check if the socket is actively being used
  # If the socket is these states:
  #  ESTABLISHED : Connection is active
  #  CLOSE_WAIT : Connection is closed, but waiting on local program to close
  #  SYN_SENT (SENT) : Connection is just being established
  if exists and ("ESTABLISH" in status or "CLOSE_WAIT" in status or "SENT" in status):
    raise DuplicateTupleError("There is a duplicate connection which conflicts with the request!")

  # Otherwise, the socket is being cleaned up
  raise AddressBindingError("Cannot bind to the specified local ip, invalid!")


def _conn_cleanup_check(identity):
  """
  <Purpose>
    This private function checks if a socket that
    got EADDRINUSE is because the socket is active,
    or because the socket is listening or 
    because the socket is being cleaned up.

  <Arguments>
    identity: A tuple to check for cleanup

  <Exceptions>
    Raises DuplicateTupleError if the socket is actively being used.

    Raises AlreadyListeningError if the socket is listening.   

    Raises CleanupInProgressError if the socket is being cleaned up
    or if the socket does not appear to exist. This is because there
    may be a race between getting EADDRINUSE and the call to this
    function.

  <Returns>
    None
  """
  # Decompose the tuple
  family, localip, localport, desthost, destport = identity
  
  # Check the sockets status
  (exists, status) = nonportable.os_api.exists_outgoing_network_socket(localip,localport,desthost,destport)

  # Check if the socket is actively being used
  # If the socket is these states:
  #  ESTABLISHED : Connection is active
  #  CLOSE_WAIT : Connection is closed, but waiting on local program to close
  #  SYN_SENT (SENT) : Connection is just being established
  if exists and ("ESTABLISH" in status or "CLOSE_WAIT" in status or "SENT" in status):
    raise DuplicateTupleError("There is a duplicate connection which conflicts with the request!")
  else:
    # Checking if a listening TCP or UDP socket exists with given local address
    # The third argument is True if socket type is TCP,False if socket type is UDP 
    if (nonportable.os_api.exists_listening_network_socket(localip, localport, (family == "TCP"))):
      raise AlreadyListeningError("There is a listening socket on the provided localip and localport!")
      # Otherwise, the socket is being cleaned up
    else:
      raise CleanupInProgressError("The socket is being cleaned up by the operating system!")


def _timed_conn_initialize(localip,localport,destip,destport, timeout):
  """
  <Purpose> 
    Tries to initialize an outgoing socket to match
    the given address parameters.

  <Arguments>
    localip,localport: The local address of the socket
    destip,destport: The destination address to which socket has to be connected  
    timeout: Maximum time to try

  <Exceptions>
    Raises TimeoutError if we timed out trying to connect.
    Raises ConnectionRefusedError if the connection was refused.
    Raises InternetConnectivityError if the network is down.

    Raises any errors encountered calling _get_tcp_socket,
    or any non-recoverable network exception.

  <Returns>
    A Python socket object connected to the dest,
    from the specified local tuple.
  """

  # Store our start time
  starttime = nonportable.getruntime()

  # Get a TCP socket bound to the local ip / port
  sock = _get_tcp_socket(localip, localport)
  sock.settimeout(timeout)

  try:
    # Try to connect until we timeout
    connected = False
    while nonportable.getruntime() - starttime < timeout:
      try:
        sock.connect((destip, destport))
        connected = True
        break
      except Exception, e:
        # Check if we are already connected
        if _is_already_connected_exception(e):
          connected = True     
          raise DuplicateTupleError("There is a duplicate connection which conflicts with the request!")
          break

        # Check if the network is down
        if _is_network_down_exception(e):
          raise InternetConnectivityError("The network is down or cannot be reached from the local IP!")

        # Check if the connection was refused
        if _is_conn_refused_exception(e):
          raise ConnectionRefusedError("The connection was refused!") 

        # Check if this is recoverable (try again, timeout, etc)
        elif not _is_recoverable_network_exception(e):
          raise

        # Sleep and retry, avoid busy waiting
        time.sleep(RETRY_INTERVAL)

    # Check if we timed out
    if not connected:
      raise TimeoutError("Timed-out connecting to the remote host!")

    # Return the socket
    return sock

  except:
    # Close the socket, and raise
    sock.close()
    raise


# Public interface!!!
def openconnection(destip, destport,localip, localport, timeout):
  """
    <Purpose>
      Opens a connection, returning a socket-like object


    <Arguments>
      destip: The destination ip to open communications with

      destport: The destination port to use for communication

      localip: The local ip to use for the communication

      localport: The local port to use for communication

      timeout: The maximum amount of time to wait to connect.   This may
               be a floating point number or an integer


    <Exceptions>

      RepyArgumentError if the arguments are invalid.   This includes both
      the types and values of arguments. If the localip matches the destip,
      and the localport matches the destport this will also be raised.

      AddressBindingError (descends NetworkError) if the localip isn't 
      associated with the local system or is not allowed.

      ResourceForbiddenError (descends ResourceError) if the localport isn't 
      allowed.

      DuplicateTupleError (descends NetworkError) if the (localip, localport, 
      destip, destport) tuple is already used.   This will also occur if the 
      operating system prevents the local IP / port from being used.

      AlreadyListeningError if the (localip, localport) tuple is already used
      for a listening TCP socket.

      CleanupInProgress if the (localip, localport, destip, destport) tuple is
      still being cleaned up by the OS.

      ConnectionRefusedError (descends NetworkError) if the connection cannot 
      be established because the destination port isn't being listened on.

      TimeoutError (common to all API functions that timeout) if the 
      connection times out

      InternetConnectivityError if the network is down, or if the host
      cannot be reached from the local IP that has been bound to.


    <Side Effects>
      TODO

    <Resource Consumption>
      This operation consumes 64*2 bytes of netsend (SYN, ACK) and 64 bytes 
      of netrecv (SYN/ACK). This requires that the localport is allowed. Upon 
      success, this call consumes an outsocket.

    <Returns>
      A socket-like object that can be used for communication. Use send, 
      recv, and close just like you would an actual socket object in python.
  """
  # Check the input arguments (type)
  if type(destip) is not str:
    raise RepyArgumentError("Provided destip must be a string!")
  if type(localip) is not str:
    raise RepyArgumentError("Provided localip must be a string!")

  if type(destport) is not int:
    raise RepyArgumentError("Provided destport must be an int!")
  if type(localport) is not int:
    raise RepyArgumentError("Provided localport must be an int!")

  if type(timeout) not in [float, int]:
    raise RepyArgumentError("Provided timeout must be an int or float!")


  # Check the input arguments (sanity)
  if not _is_valid_ip_address(destip):
    raise RepyArgumentError("Provided destip is not valid! IP: '"+destip+"'")
  if not _is_valid_ip_address(localip):
    raise RepyArgumentError("Provided localip is not valid! IP: '"+localip+"'")

  if not _is_valid_network_port(destport):
    raise RepyArgumentError("Provided destport is not valid! Port: "+str(destport))
  if not _is_valid_network_port(localport):
    raise RepyArgumentError("Provided localport is not valid! Port: "+str(localport))

  if timeout <= 0:
    raise RepyArgumentError("Provided timeout is not valid, must be positive! Timeout: "+str(timeout))

  # Check that if localip == destip, then localport != destport
  if localip == destip and localport == destport:
    raise RepyArgumentError("Local socket name cannot match destination socket name! Local/Dest IP and Port match.")

  # Check the input arguments (permission)
  update_ip_cache()
  if not _ip_is_allowed(localip):
    raise ResourceForbiddenError("Provided localip is not allowed! IP: "+localip)

  if not _is_allowed_localport("TCP", localport):
    raise ResourceForbiddenError("Provided localport is not allowed! Port: "+str(localport))



  # use this tuple during connection clean up check
  identity = ("TCP", localip, localport, destip, destport)
  
  # Wait for netsend / netrecv
  if _is_loopback_ipaddr(destip):
    nanny.tattle_quantity('loopsend', 0)
    nanny.tattle_quantity('looprecv', 0)
  else:
    nanny.tattle_quantity('netsend', 0)
    nanny.tattle_quantity('netrecv', 0)

  try:
    # To Know if remote IP is on loopback or not
    on_loopback = _is_loopback_ipaddr(destip)

    # Get the socket
    sock = _timed_conn_initialize(localip,localport,destip,destport, timeout)
    
    # Register this socket as an outsocket
    nanny.tattle_add_item('outsockets',id(sock))
  except Exception, e:

    # Check if this an already in use error
    if _is_addr_in_use_exception(e):
      # Call _conn_cleanup_check to determine if this is because
      # the socket is being cleaned up or if it is actively being used
      # This will always raise DuplicateTupleError or
      # CleanupInProgressError or AlreadyListeningError
      _conn_cleanup_check(identity)
 
    # Check if this is a binding error
    if _is_addr_unavailable_exception(e):
      # Call _conn_alreadyexists_check to determine if this is because
      # the connection is active or not
      _conn_alreadyexists_check(identity)
      

    # Unknown error...
    else:
      raise

  emul_sock = EmulatedSocket(sock, on_loopback)

  # Tattle the resources used
  if _is_loopback_ipaddr(destip):
    nanny.tattle_quantity('loopsend', 128)
    nanny.tattle_quantity('looprecv', 64)
  else:
    nanny.tattle_quantity('netsend', 128)
    nanny.tattle_quantity('netrecv', 64)

  # Return the EmulatedSocket
  return emul_sock


def listenforconnection(localip, localport):
  """
  <Purpose>
    Sets up a TCPServerSocket to recieve incoming TCP connections. 

  <Arguments>
    localip:
        The local IP to listen on
    localport:
        The local port to listen on

  <Exceptions>
    Raises AlreadyListeningError if another TCPServerSocket or process has bound
    to the provided localip and localport.

    Raises DuplicateTupleError if another process has bound to the
    provided localip and localport.

    Raises RepyArgumentError if the localip or localport are invalid
    Raises ResourceForbiddenError if the ip or port is not allowed.
    Raises AddressBindingError if the IP address isn't a local ip.

  <Side Effects>
    The IP / Port combination cannot be used until the TCPServerSocket
    is closed.

  <Resource Consumption>
    Uses an insocket for the TCPServerSocket.

  <Returns>
    A TCPServerSocket object.
  """
  # Check the input arguments (type)
  if type(localip) is not str:
    raise RepyArgumentError("Provided localip must be a string!")

  if type(localport) is not int:
    raise RepyArgumentError("Provided localport must be a int!")


  # Check the input arguments (sanity)
  if not _is_valid_ip_address(localip):
    raise RepyArgumentError("Provided localip is not valid! IP: '"+localip+"'")

  if not _is_valid_network_port(localport):
    raise RepyArgumentError("Provided localport is not valid! Port: "+str(localport))


  # Check the input arguments (permission)
  update_ip_cache()
  if not _ip_is_allowed(localip):
    raise ResourceForbiddenError("Provided localip is not allowed! IP: '"+localip+"'")

  if not _is_allowed_localport("TCP", localport):
    raise ResourceForbiddenError("Provided localport is not allowed! Port: "+str(localport))

  # This is used to check if there is an existing connection with the same identity
  identity = ("TCP", localip, localport, None, None) 

  try:
    # Check if localip is on loopback
    on_loopback = _is_loopback_ipaddr(localip)
    # Get the socket
    sock = _get_tcp_socket(localip,localport)     
    nanny.tattle_add_item('insockets',id(sock))
    # Get the maximum number of outsockets
    max_outsockets = nanny.get_resource_limit("outsockets")        
    # If we have restrictions, then we want to set the outsocket
    # limit
    if max_outsockets:
      # Set the backlog to be the maximum number of outsockets
      sock.listen(max_outsockets)
    else:
      sock.listen(5)

  except Exception, e:
    
    # Check if this an already in use error
    if _is_addr_in_use_exception(e): 
      # Call _conn_cleanup_check to determine if this is because
      # the socket is being cleaned up or if it is actively being used
      # This will always raise DuplicateTupleError or
      # CleanupInProgressError or AlreadyListeningError   
      _conn_cleanup_check(identity)
 
    # Check if this is a binding error
    if _is_addr_unavailable_exception(e):
      # Call _conn_alreadyexists_check to determine if this is because
      # the connection is active or not      
      _conn_alreadyexists_check(identity)
    # Unknown error...
    else:
        raise

  server_sock = TCPServerSocket(sock, on_loopback)

  # Return the TCPServerSocket
  return server_sock


# Private method to create a TCP socket and bind
# to a localip and localport.
# 
def _get_tcp_socket(localip, localport):
  # Create the TCP socket
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
  # Reuse the socket if it's "pseudo-availible"
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  if localip and localport:
    try:
      s.bind((localip,localport))
    except: # Raise the exception un-tainted
      # don't leak sockets
      s.close()
      raise
  return s


# Private method to create a UDP socket and bind
# to a localip and localport.
# 
def _get_udp_socket(localip, localport):
  # Create the UDP socket
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  if localip and localport:
    try:
      s.bind((localip, localport))
    except:
      # don't leak sockets
      s.close()
      raise
  return s


# Checks if the given real socket would block
def _check_socket_state(realsock, waitfor="rw", timeout=0.0):
  """
  <Purpose>
    Checks if the given socket would block on a send() or recv().
    In the case of a listening socket, read_will_block equates to
    accept_will_block.

  <Arguments>
    realsock:
              A real socket.socket() object to check for.

    waitfor:
              An optional specifier of what to wait for. "r" for read only, "w" for write only,
              and "rw" for read or write. E.g. if timeout is 10, and wait is "r", this will block
              for up to 10 seconds until read_will_block is false. If you specify "r", then
              write_will_block is always true, and if you specify "w" then read_will_block is
              always true.

    timeout:
              An optional timeout to wait for the socket to be read or write ready.

  <Returns>
    A tuple, (read_will_block, write_will_block).

  <Exceptions>
    As with select.select(). Probably best to wrap this with _is_recoverable_network_exception
    and _is_terminated_connection_exception. Throws an exception if waitfor is not in ["r","w","rw"]
  """
  # Check that waitfor is valid
  if waitfor not in ["rw","r","w"]:
    raise Exception, "Illegal waitfor argument!"

  # Array to hold the socket
  sock_array = [realsock]

  # Generate the read/write arrays
  read_array = []
  if "r" in waitfor:
    read_array = sock_array

  write_array = []
  if "w" in waitfor:
    write_array = sock_array

  # Call select()
  (readable, writeable, exception) = select.select(read_array,write_array,sock_array,timeout)

  # If the socket is in the exception list, then assume its both read and writable
  if (realsock in exception):
    return (False, False)

  # Return normally then
  return (realsock not in readable, realsock not in writeable)


##### Class Definitions

# Public.   We pass these to the users for communication purposes
class EmulatedSocket:
  """
  This object is a wrapper around a tcp
  TCP socket. It allows for sending and
  recieving data, and closing the socket.

  It operates in a strictly non-blocking mode,
  and uses Exceptions to indicate when an
  operation would result in blocking behavior.
  """
  # Fields:
  # socket: This is a TCP Socket  
  #
  # send_buffer_size: The size of the send buffer. We send less than
  #                  this to avoid a bug.
  #
  # on_loopback: true if the remote ip is a loopback address.
  #              this is used for resource accounting.
  # sock_lock: Threading Lock on socket object used for 
  #            synchronization.
  __slots__ = ["socketobj", "send_buffer_size", "on_loopback", "sock_lock"]

  
  def __init__(self, sock, on_loopback):
    """
    <Purpose>
      Initializes a EmulatedSocket object.

    <Arguments>
      sock: A TCP Socket

      on_loopback: True/False based on whether remote IP is
                   on loopback oe not
      
    <Exceptions>
      InteralRepyError is raised if there is no table entry for
      the socket.

    <Returns>
      A EmulatedSocket object.
    """
    # Store the parameters tuple
    self.socketobj = sock
    self.on_loopback = on_loopback
    self.sock_lock = threading.Lock()
    
    # Store the socket send buffer size and set to non-blocking
    self.send_buffer_size = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    # locking should be unnecessary because there isn't another external
    # reference here yet
    sock.setblocking(0)

    
  def _close(self):
    """
    <Purpose>
      Private close method. Called when socket lock is held.
      Does not perform any accounting / locking. Those should
      be done by the public methods.

    <Arguments>
      None

    <Side Effects>
      Closes the socket

    <Returns>
      None
    """
    # Clean up the socket
    _cleanup_socket(self)

    # Replace the socket
    self.socketobj = None


  def close(self):
    """
      <Purpose>
        Closes a socket.   Pending remote recv() calls will return with the 
        remaining information.   Local recv / send calls will fail after this.

      <Arguments>
        None

      <Exceptions>
        None

      <Side Effects>
        Pending local recv calls will either return or have an exception.

      <Resource Consumption>
        If the connection is closed, no resources are consumed. This operation
        uses 64 bytes of netrecv, and 128 bytes of netsend.
        This call also stops consuming an outsocket.

      <Returns>
        True if this is the first close call to this socket, False otherwise.
    """
    # Get the socket lock
    socket_lock = self.sock_lock
   
    if (self.socketobj == None):
      return False
    # Wait for resources
    if self.on_loopback:
      nanny.tattle_quantity('looprecv', 0)
      nanny.tattle_quantity('loopsend', 0)
    else:
      nanny.tattle_quantity('netrecv', 0)
      nanny.tattle_quantity('netsend', 0)

    # Acquire the lock
    socket_lock.acquire()
    try:
      # Internal close
      self._close()

      # Tattle the resources
      if self.on_loopback:
        nanny.tattle_quantity('looprecv',64)
        nanny.tattle_quantity('loopsend',128)
      else:
        nanny.tattle_quantity('netrecv',64)
        nanny.tattle_quantity('netsend',128)

      # Done
      return True

    finally:
      socket_lock.release()



  def recv(self,bytes):
    """
      <Purpose>
        Receives data from a socket.   It may receive fewer bytes than 
        requested.   

      <Arguments>
        bytes: 
           The maximum number of bytes to read.   

      <Exceptions>
        SocketClosedLocal is raised if the socket was closed locally.
        SocketClosedRemote is raised if the socket was closed remotely.
        SocketWouldBlockError is raised if the socket operation would block.

      <Side Effects>
        None.

      <Resource Consumptions>
        This operations consumes 64 + amount of data  in bytes
        worth of netrecv, and 64 bytes of netsend.
  
      <Returns>
        The data received from the socket (as a string).   If '' is returned,
        the other side has closed the socket and no more data will arrive.
    """
    # Get the socket lock
    socket_lock = self.sock_lock
    # Wait if already oversubscribed
    if self.on_loopback:
      nanny.tattle_quantity('looprecv',0)
      nanny.tattle_quantity('loopsend',0)
    else:
      nanny.tattle_quantity('netrecv',0)
      nanny.tattle_quantity('netsend',0)


    # Acquire the socket lock
    socket_lock.acquire()
    try:
      # Get the socket
      sock = self.socketobj
      if sock is None:
        raise KeyError # Socket is closed locally

      # Try to recieve the data
      data_recieved = sock.recv(bytes)

      # Calculate the length of the data
      data_length = len(data_recieved)
      
      # Raise an exception if there was no data
      if data_length == 0:
        raise SocketClosedRemote("The socket has been closed remotely!")

      if self.on_loopback:
        nanny.tattle_quantity('looprecv',data_length+64)
        nanny.tattle_quantity('loopsend',64)
      else:
        nanny.tattle_quantity('netrecv',data_length+64)
        nanny.tattle_quantity('netsend',64)

      return data_recieved

    except KeyError:
      raise SocketClosedLocal("The socket is closed!")
  
    except RepyException:
      raise # Pass up from inner block

    except Exception, e:
      # Check if this a recoverable error
      if _is_recoverable_network_exception(e):
        # Operation would block
        raise SocketWouldBlockError("There is no data! recv() would block.")

      elif _is_terminated_connection_exception(e):
        # Remote close
        self._close()
        raise SocketClosedRemote("The socket has been closed remotely!")

      else:
        # Unknown error
        self._close()
        raise SocketClosedLocal("The socket has encountered an unexpected error! Error:"+str(e))

    finally:
      socket_lock.release()



  def send(self,message):
    """
      <Purpose>
        Sends data on a socket.   It may send fewer bytes than requested.   

      <Arguments>
        message:
          The string to send.

      <Exceptions>
        SocketClosedLocal is raised if the socket is closed locally.
        SocketClosedRemote is raised if the socket is closed remotely.
        SocketWouldBlockError is raised if the operation would block.

      <Side Effects>
        None.

      <Resource Consumption>
        This operations consumes 64 + size of sent data of netsend and
        64 bytes of netrecv.

      <Returns>
        The number of bytes sent.   Be sure not to assume this is always the 
        complete amount!
    """
    # Get the socket lock
    socket_lock = self.sock_lock
    # Wait if already oversubscribed
    if self.on_loopback:
      nanny.tattle_quantity('loopsend',0)
      nanny.tattle_quantity('looprecv',0)
    else:
      nanny.tattle_quantity('netsend',0)
      nanny.tattle_quantity('netrecv',0)

    # Trim the message size to be less than the send buffer size.
    # This is a fix for http://support.microsoft.com/kb/823764
    message = message[:self.send_buffer_size-1]

    # Acquire the socket lock
    socket_lock.acquire()
    try:
      # Get the socket
      sock = self.socketobj
      if sock is None:
        raise KeyError # Socket is closed locally
 
      # Detect Socket Closed Remote
      # Fixes ticket#974
      (readable, writable, exception) = select.select([sock],[],[],0)
      # check if socket is readable.   This is true if the remote end closed.
      if readable:

         # if socket is readable but there was no data this means the remote end
         # has closed the socket.   We peek so that we don't consume a character.
         data_peeked = sock.recv(1,socket.MSG_PEEK)
         if len(data_peeked) == 0:
            # remote socket is closed
            raise SocketClosedRemote("The socket has been closed by the remote end!")

      # Try to send the data
      bytes_sent = sock.send(message)
      
      if self.on_loopback:
        nanny.tattle_quantity('looprecv', 64)
        nanny.tattle_quantity('loopsend', 64 + bytes_sent)
      else:
        nanny.tattle_quantity('netrecv', 64)
        nanny.tattle_quantity('netsend', 64 + bytes_sent)

      # Return the number of bytes sent
      return bytes_sent


    except KeyError:
      raise SocketClosedLocal("The socket is closed!")
    except RepyException:
      raise # pass up from inner block
    except Exception, e:
      # Check if this a recoverable error
      if _is_recoverable_network_exception(e):
        # Operation would block
        raise SocketWouldBlockError("send() would block.")

      elif _is_terminated_connection_exception(e):
        # Remote close
        self._close()
        raise SocketClosedRemote("The socket has been closed remotely!")

      else:
        # Unknown error
        self._close()
        raise SocketClosedLocal("The socket has encountered an unexpected error! Error:"+str(e))

    finally:
      socket_lock.release()


  def __del__(self):
    # Get the socket lock
    try:
      socket_lock = self.sock_lock
    except KeyError:
      # Closed, done
      return

    # Acquire the lock and close
    socket_lock.acquire()
    try:
      self._close()
    finally:
      socket_lock.release()


# End of EmulatedSocket class


# Public: Class the behaves represents a listening UDP socket.
class UDPServerSocket:
  """
  This object is a wrapper around a listening
  UDP socket. It allows for accepting incoming
  messages, and closing the socket.

  It operates in a strictly non-blocking mode,
  and uses Exceptions to indicate when an
  operation would result in blocking behavior.
  """
  # Fields:
  # sock: This is a listening UDP socket  
  # on_loopback: True if the local IP is a loopback address.
  #              This is used for resource accounting.
  # sock_lock: Threading Lock on socket object used for 
  #            synchronization.
  __slots__ = ["socketobj", "on_loopback", "sock_lock"]

  # UDP listening socket interface
  def __init__(self, sock, on_loopback):
    """
    <Purpose>
      Initializes the UDPServerSocket. The socket
      should already be established by listenformessage
      prior to calling the initializer.

    <Arguments>
      
      socketobj : The listening socket
      on_loopback : True/False based on whether the local IP 
                    is a loopback address or not 
    <Exceptions>
      None

    <Returns>
      A UDPServerSocket
    """
    # Store the parameters
    self.socketobj = sock
    self.on_loopback = on_loopback
    self.sock_lock = threading.Lock()
    
    # Set the socket to non-blocking
    # locking should be unnecessary because there isn't another external
    # reference here yet
    sock.setblocking(0)

  def getmessage(self):
    """
    <Purpose>
        Obtains an incoming message that was sent to an IP and port.

    <Arguments>
        None.

    <Exceptions>
        SocketClosedLocal if UDPServerSocket.close() was called.
        Raises SocketWouldBlockError if the operation would block.

    <Side Effects>
        None

    <Resource Consumption>
        This operation consumes 64 + size of message bytes of netrecv

    <Returns>
        A tuple consisting of the remote IP, remote port, and message.

    """
    # Get the socket lock
    
    socket_lock = self.sock_lock
    # Wait for netrecv resources
    if self.on_loopback:
      nanny.tattle_quantity('looprecv',0)
    else:
      nanny.tattle_quantity('netrecv',0)

    # Acquire the lock
    socket_lock.acquire()
    try:
      # Get the socket itself. This must be done after
      # we acquire the lock because it is possible that the
      # socket was closed/re-opened or that it was set to None,
      # etc.
      socket = self.socketobj
      if socket is None:
        raise KeyError # Indicates socket is closed

      # Try to get a message of any size.   (64K is the max that fits in the 
      # UDP header)
      message, addr = socket.recvfrom(65535)
      remote_ip, remote_port = addr

      # Do some resource accounting
      if self.on_loopback:
        nanny.tattle_quantity('looprecv', 64 + len(message))
      else:
        nanny.tattle_quantity('netrecv', 64 + len(message))

      # Return everything
      return (remote_ip, remote_port, message)

    except KeyError:
      # Socket is closed
      raise SocketClosedLocal("The socket has been closed!")
  
    except RepyException:
      # Let these through from the inner block
      raise

    except Exception, e:
      # Check if this is a would-block error
      if _is_recoverable_network_exception(e):
        raise SocketWouldBlockError("No messages currently available!")

      else: 
        # Unexpected, close the socket, and then raise SocketClosedLocal
        _cleanup_socket(self)       
        raise SocketClosedLocal("Unexpected error, socket closed!")

    finally:
      # Release the lock
      socket_lock.release()



  def close(self):
    """
    <Purpose>
        Closes a socket that is listening for messages.

    <Arguments>
        None.

    <Exceptions>
        None.

    <Side Effects>
        The IP address and port can be reused by other UDPServerSockets after
        this.

    <Resource Consumption>
        If applicable, this operation stops consuming the corresponding
        insocket.

    <Returns>
        True if this is the first close call to this socket, False otherwise.

    """
    # Get the socket lock    
    socket_lock = self.sock_lock
    # Acquire the lock
    socket_lock.acquire()
    try:
      # Clean up the socket
      _cleanup_socket(self)
      # Replace the socket
      self.socketobj = None

      return True

    finally:
      socket_lock.release()
 

  def __del__(self):
    # Clean up global resources on garbage collection.
    self.close()




class TCPServerSocket (object):
  """
  This object is a wrapper around a listening
  TCP socket. It allows for accepting incoming
  connections, and closing the socket.

  It operates in a strictly non-blocking mode,
  and uses Exceptions to indicate when an
  operation would result in blocking behavior.
  """
  # Fields:
  # socket: This is a listening TCP socket  
  # sock_lock: Threading Lock on socket object used for 
  #            synchronization.
  # on_loopback: true if the remote ip is a loopback address.
  #              this is used for resource accounting.
  #

  __slots__ = ["socketobj", "on_loopback", "sock_lock"]
  def __init__(self, sock, on_loopback):
    """
    <Purpose>
      Initializes the TCPServerSocket. The socket
      should already be established by listenforconnection
      prior to calling the initializer.

    <Arguments>
      socketobj: The TCP listening socket
      
      on_loopback: True/False based on whether local IP
                   is on loopback or not
      
    <Exceptions>
      None

    <Returns>
      A TCPServerSocket
    """
    # Store the parameters
    self.socketobj = sock
    self.sock_lock = threading.Lock()
    self.on_loopback = on_loopback     

    # Set the socket to non-blocking
    # locking should be unnecessary because there isn't another external
    # reference here yet
    sock.setblocking(0)
        


  def getconnection(self):
    """
    <Purpose>
      Accepts an incoming connection to a listening TCP socket.

    <Arguments>
      None

    <Exceptions>
      Raises SocketClosedLocal if close() has been called.
      Raises SocketWouldBlockError if the operation would block.
      Raises ResourcesExhaustedError if there are no free outsockets.

    <Resource Consumption>
      If successful, consumes 128 bytes of netrecv (64 bytes for
      a SYN and ACK packet) and 64 bytes of netsend (1 ACK packet).
      Uses an outsocket.

    <Returns>
      A tuple containing: (remote ip, remote port, socket object)
    """
    # Get the socket lock
    socket_lock = self.sock_lock

    # Wait for netsend and netrecv resources
    if self.on_loopback:
      nanny.tattle_quantity('looprecv',0)
      nanny.tattle_quantity('loopsend',0)
    else:
      nanny.tattle_quantity('netrecv',0)
      nanny.tattle_quantity('netsend',0)

    # Acquire the lock
    socket_lock.acquire()
    try:
      # Get the socket itself. This must be done after
      # we acquire the lock because it is possible that the
      # socket was closed/re-opened or that it was set to None,
      # etc.
      socket = self.socketobj
      if socket is None:
        raise KeyError # Indicates socket is closed

      # Try to accept
      new_socket, remote_host_info = socket.accept()
      remote_ip, remote_port = remote_host_info
      
      # Get new_socket id to register new_socket with nanny
      new_sockid = id(new_socket)
      # Check if remote_ip is on loopback
      is_on_loopback = _is_loopback_ipaddr(remote_ip)
      # Do some resource accounting
      if self.on_loopback:
        nanny.tattle_quantity('looprecv', 128)
        nanny.tattle_quantity('loopsend', 64)
      else:
        nanny.tattle_quantity('netrecv', 128)
        nanny.tattle_quantity('netsend', 64)

      try:
        nanny.tattle_add_item('outsockets', new_sockid)
      except ResourceExhaustedError:
        # Close the socket, and raise
        new_socket.close()
        raise

      wrapped_socket = EmulatedSocket(new_socket, is_on_loopback)

      # Return everything
      return (remote_ip, remote_port, wrapped_socket)

    except KeyError:
      # Socket is closed
      raise SocketClosedLocal("The socket has been closed!")
  
    except RepyException:
      # Let these through from the inner block
      raise

    except Exception, e:
      # Check if this is a would-block error
      if _is_recoverable_network_exception(e):
        raise SocketWouldBlockError("No connections currently available!")

      else: 
        # Unexpected, close the socket, and then raise SocketClosedLocal
        _cleanup_socket(self)       
        raise SocketClosedLocal("Unexpected error, socket closed!")

    finally:
      # Release the lock
      socket_lock.release()


  def close(self):
    """
    <Purpose>
      Closes the listening TCP socket.

    <Arguments>
      None

    <Exceptions>
      None

    <Side Effects>
      The IP and port can be re-used after closing.

    <Resource Consumption>
      Releases the insocket used.

    <Returns>
      True, if this is the first call to close.
      False otherwise.
    """
    # Get the socket lock
    socket_lock = self.sock_lock
    
    # Acquire the lock
    socket_lock.acquire()
    try:
      # Clean up the socket
      _cleanup_socket(self)
      # Replace the socket
      self.socketobj = None      
      # Done
      return True

    finally:
      socket_lock.release()
 

  def __del__(self):
    # Close the socket
    self.close()



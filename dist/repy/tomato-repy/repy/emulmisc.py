"""
   Author: Justin Cappos

   Start Date: 19 July 2008

   Description:

   Miscellaneous functions for the sandbox.   Random, exitall, getruntime, 
   etc.

   <Modified>
     Anthony - May 7 2009, changed the source of random data which is
     used in randomfloat. Now uses os.urandom to get random bytes,
     transforms the bytes into a random integer then uses it to
     create a float of 53bit resolution.
     Modified scheme from the random() function of the SystemRandom class,
     as defined in source code python 2.6.2 Lib/random.py
     
     Anthony - Jun 25 2009, will now use tracebackrepy.handle_internalerror
     to log when os.urandom raises a NotImplementedError.
"""

import nanny
import os               # for os.urandom(7)
import tracebackrepy    # for os.urandom so exception can be logged internally
import nonportable      # for getruntime
import harshexit        # for harshexit()
import threading        # for Lock()
import thread           # to catch thread.error
from exception_hierarchy import *

##### Public Functions

def randombytes():
  """
  <Purpose>
    Return a string of random bytes with length 1024

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    This function is metered because it may involve using a hardware source of randomness.

  <Resource Consumption>
    This operation consumes 1024 bytes of random data.

  <Returns>
    The string of bytes.
  """
  # Wait for random resources
  nanny.tattle_quantity('random', 0)

  # If an OS-specific source of randomness is not a found
  # a NotImplementedError would be raised. 
  # Anthony - a NotImplementedError will be logged as an internal
  # error so that we will hopefully be able to identify the system,
  # the exception is not passed on because the problem was not
  # caused by the user. The exit code 217 was chosen to be
  # unique from all other exit calls in repy.
  try:
    randomdata = os.urandom(1024)
  except NotImplementedError, e:
    tracebackrepy.handle_internalerror("os.urandom is not implemented " + \
        "(Exception was: %s)" % e.message, 217)

  # Tattle all 1024 now
  nanny.tattle_quantity('random',1024)
 
  return randomdata


def getruntime():
  """
   <Purpose>
      Return the amount of time the program has been running.   This is in
      wall clock time. This is guaranteed to be monotonic.

   <Arguments>
      None

   <Exceptions>
      None.

   <Side Effects>
      None

   <Returns>
      The elapsed time as float
  """
  return nonportable.getruntime()


def exitall():
  """
   <Purpose>
      Allows the user program to stop execution of the program without
      passing an exit event to the main program. 

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      Interactions with timers and connection / message receiving functions 
      are undefined.   These functions may be called after exit and may 
      have undefined state.

   <Returns>
      None.   The current thread does not resume after exit
  """
  harshexit.harshexit(200)


def createlock():
  """
   <Purpose>
      Returns a lock object to the user program.    A lock object supports
      two functions: acquire and release.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      The lock object.
  """
  # Return an instance of emulated_lock
  return emulated_lock()


def getthreadname():
  """
  <Purpose>
    Returns a string identifier for the currently executing thread.
    This identifier is unique to this thread.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A string identifier.
  """
  # Get the thread object
  tobj = threading.currentThread()

  # Return the name
  return tobj.getName()


def getlasterror():
  """
  <Purpose>
    Obtains debugging information about the last exception that occured in the current thread.

  <Arguments>
    None

  <Exceptions>
    None

  <Returns>
    A string with details of the last exception in the current thread, or None if there is no such
    exception.
  """
  # Call down into tracebackrepy
  return tracebackrepy.format_exception()


def log(*args):
  """
  <Purpose>
    Used to store program output. Prints output to console by default.

  <Arguments>
    Takes a variable number of arguments to print. They are wrapped in str(), so it is not necessarily a string.

  <Exceptions>
    None

  <Returns>
    Nothing
  """
  for arg in args:
    print arg,


##### Class Declarations

class emulated_lock (object):
  """
  This object is a slim wrapper around Python's
  threading.Lock(). It provides a simple lock object.
  """

  # We only have a single instance variable, "lock"
  # which is a threading.Lock() object
  __slots__ = ["lock"]

  def __init__(self):
    # Create our lock
    self.lock = threading.Lock()


  def acquire(self, blocking):
    """
    <Purpose>
      Acquires the lock.

    <Arguments>
      blocking:
          If False, returns immediately instead of waiting to acquire the lock.

    <Exceptions>
      None.

    <Side Effects>
      If successful, locks the object.

    <Returns>
     True if the lock was acquired.
    """
    # Call down
    return self.lock.acquire(blocking)


  def release(self):
    """
    <Purpose>
      Releases the lock.

    <Arguments>
      None

    <Exceptions>
      LockDoubleReleaseError if release is called on an unlocked lock.

    <Side Effects>
      Unlocks the object.

    <Returns>
      None
    """
    try:
      self.lock.release()
    except thread.error:
      raise LockDoubleReleaseError("Releasing an un-locked lock!")



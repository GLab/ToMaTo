"""
   Author: Justin Cappos

   Start Date: 19 July 2008

   Description:
   
   Provides a unique ID when requested...
   This really should use uniqueid.repy
"""

import threading        # to get the current thread name and a lock


# this dictionary contains keys that are thread names and values that are 
# integers.   The value starts at 0 and is incremented every time we give 
# out an ID.   The ID is formed from those two parts (thread name and ID)
uniqueid_idlist = [0]
uniqueid_idlock = threading.Lock()


def getuniqueid():
  """
   <Purpose>
      Provides a unique identifier.

   <Arguments>
      None

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      The identifier (the string)
  """

  uniqueid_idlock.acquire()

  # I'm using a list because I need a global, but don't want to use the global
  # keyword.   
  myid = uniqueid_idlist[0]
  uniqueid_idlist[0] = uniqueid_idlist[0] + 1

  uniqueid_idlock.release()

  myname = threading.currentThread().getName()

  return myname + ":"+str(myid)


# thread_name_prefix is the prefix that is pre-pended to the counter
# The counter is the first element of an array, and starts indexing from 1.
# The thread_name_lock is used to serialize access to the counter
thread_name_prefix = "Thread:"
thread_name_counter = [1]
thread_name_lock = threading.Lock()

# Gets a new thread name. This call is thread safe, and returns a new
# unique name on each call.
def get_new_thread_name(extra_prefix=""):
  """
  <Purpose>
    Returns a new and unique name that can be associated with a new thread.
    This is used so that threads can be uniquely identified.
  
    This call is thread safe, and guarentees unique-ness.

  <Arguments>
    extra_prefix:
          This is an optional string that is pre-pended to the
          string that would be otherwise returned.

  <Returns>
    A string name
  """

  # Acquire the lock
  thread_name_lock.acquire()

  # Construct the thread name
  thread_name = str(extra_prefix) + thread_name_prefix + str(thread_name_counter[0])

  # Increment the counter
  thread_name_counter[0] = thread_name_counter[0] + 1

  # Release the lock
  thread_name_lock.release()

  # Return the new name
  return thread_name





"""
   Author: Justin Cappos

   Program: nanny.py

   Start Date: 1 July 2008


   Description:

   This module handles the policy decisions and accounting to detect if there 
   is a resource violation.  The actual "stopping", etc. is done in the
   nonportable module.

   Note: this module was heavily revised in Dec 2010.   However, these changes 
   are not sufficient to support GACKS style resource trading and sharing.
   This is a more major change than I wanted to do at this point.
"""

# for sleep
import time

# needed for cpu, disk, and memory handling
import nonportable

# needed for handling internal errors
import tracebackrepy

# Import the exception hierarchy
from exception_hierarchy import *


# this is used to read in our dictionary of allowed resource utilization
import resourcemanipulation

import resource_constants

import threading



# I'm going to global information about the resources allowed and used...
# These will be initialized when the nanny is started.
# (this would obviously be wrong in GACKS)
_resources_allowed_dict = None

_resources_consumed_dict = None








# Updates the values in the consumption table (taking the current time into 
# account)
def _update_resource_consumption_table(resource, resource_allowed_dict, consumed_resource_dict):

  thetime = nonportable.getruntime()

  # I'm going to reduce all renewable resources by the appropriate amount given
  # the amount of elapsed time.

  elapsedtime = thetime - consumed_resource_dict['renewable_update_time'][resource]

  consumed_resource_dict['renewable_update_time'][resource] = thetime

  if elapsedtime < 0:
    # A negative number (likely a NTP reset).   Let's just ignore it.
    return

  # Remove the charge
  reduction = elapsedtime * resource_allowed_dict[resource]
    
  if reduction > consumed_resource_dict[resource]:

    # It would reduce it below zero (so put it at zero)
    consumed_resource_dict[resource] = 0.0
  else:

    # Subtract some for elapsed time...
    consumed_resource_dict[resource] = consumed_resource_dict[resource] - reduction



# I want to wait until a resource can be used again...
def _sleep_until_resource_drains(resource, resourcesalloweddict, resourcesuseddict):

  # It'll never drain!
  if resourcesalloweddict[resource] == 0:
    raise InternalRepyError, "Resource '"+resource+"' limit set to 0, won't drain!"
    

  # We may need to go through this multiple times because other threads may
  # also block and consume resources.
  while resourcesuseddict[resource] > resourcesalloweddict[resource]:

    # Sleep until we're expected to be under quota
    sleeptime = (resourcesuseddict[resource] - resourcesalloweddict[resource]) / resourcesalloweddict[resource]

    time.sleep(sleeptime)

    _update_resource_consumption_table(resource, resourcesalloweddict, resourcesuseddict)




def _create_resource_consumption_dict():
  """
   <Purpose>
      Initializes the consumed resource portion of the nanny.   This tracks
      resource use (instead of resource quantity)

   <Arguments>
      None.
         
   <Exceptions>
      InternalRepyError is raised if a resource is specified as both quantity and item based.

   <Side Effects>
      None.

   <Returns>
      A dict for tracking resources consumed.  It has locks, etc. in the right
      places.
  """

  returned_resource_dict = {}

  # things that are quantities should start at 0.0
  for resource in resource_constants.quantity_resources:
    returned_resource_dict[resource] = 0.0

  for resource in resource_constants.item_resources:
    # double check there is no overlap...
    if resource in resource_constants.quantity_resources:
      raise InternalRepyError("Resource '"+resource+"' cannot be both quantity and item based!")

    returned_resource_dict[resource] = set()

  # I need locks to protect races in accesses to some items...
  returned_resource_dict['fungible_locks'] = {}
  for init_resource in resource_constants.fungible_item_resources:
    returned_resource_dict['fungible_locks'][init_resource] = threading.Lock()

  returned_resource_dict['renewable_locks'] = {}
  for init_resource in resource_constants.renewable_resources:
    returned_resource_dict['renewable_locks'][init_resource] = threading.Lock()


  # I also need to track when the last update of a renewable resource occurred
  returned_resource_dict['renewable_update_time'] = {}

  # (Aside) JAC: I've thought about this and looked through the commit history.
  # I don't see any reason to initialize the renewable resources with the
  # current time (as was done before).
  for init_resource in resource_constants.renewable_resources:
    returned_resource_dict['renewable_update_time'][init_resource] = 0.0


  return returned_resource_dict


# let the nanny know that the process is consuming some resource
# can also be called with quantity '0' for a renewable resource so that the
# nanny will wait until there is some free "capacity"
def _tattle_quantity(resource, quantity, resourcesalloweddict, resourcesuseddict):
  """
   <Purpose>
      Notify the nanny of the consumption of a renewable resource.   A 
      renewable resource is something like CPU or network bandwidth that is 
      speficied in quantity per second.

   <Arguments>
      resource:
         A string with the resource name.   
      quantity:
         The amount consumed.   This can be zero (to indicate the program 
         should block if the resource is already over subscribed) but 
         cannot be negative

   <Exceptions>
      None.

   <Side Effects>
      May sleep the program until the resource is available.

   <Returns>
      None.
  """


  # I assume that the quantity will never be negative
  if quantity < 0:
    # This will cause the program to exit and log things if logging is
    # enabled. -Brent
    tracebackrepy.handle_internalerror("Resource '" + resource + 
        "' has a negative quantity " + str(quantity) + "!", 132)
    
  # get the lock for this resource
  resourcesuseddict['renewable_locks'][resource].acquire()
  
  # release the lock afterwards no matter what
  try: 
    # update the resource counters based upon the current time.
    _update_resource_consumption_table(resource, resourcesalloweddict, resourcesuseddict)

    # It's renewable, so I can wait for it to clear
    if resource not in resource_constants.renewable_resources:
      # Should never have a quantity tattle for a non-renewable resource
      # This will cause the program to exit and log things if logging is
      # enabled. -Brent
      tracebackrepy.handle_internalerror("Resource '" + resource + 
          "' is not renewable!", 133)
  

    resourcesuseddict[resource] = resourcesuseddict[resource] + quantity
    # I'll block if I'm over...
    _sleep_until_resource_drains(resource, resourcesalloweddict, resourcesuseddict)
  
  finally:
    # release the lock for this resource
    resourcesuseddict['renewable_locks'][resource].release()
    





def _tattle_add_item(resource, item, resourcesalloweddict, resourcesuseddict):
  """
   <Purpose>
      Let the nanny know that the process is trying to consume a fungible but 
      non-renewable resource.

   <Arguments>
      resource:
         A string with the resource name.   
      item:
         A unique identifier that specifies the resource.   It is used to
         prevent duplicate additions and removals and so must be unique for
         each item used.
         
   <Exceptions>
      InternalRepyError is raised if the consumption of the resource has exceded the limit.
      ResourceExhaustedError is raised if the resource is currently at the usage limit.

   <Side Effects>
      None.

   <Returns>
      None.
  """

  resourcesuseddict['fungible_locks'][resource].acquire()

  # always unlock as we exit...
  try: 

    # It's already acquired.   This is always allowed.
    if item in resourcesuseddict[resource]:
      return

    if len(resourcesuseddict[resource]) > resourcesalloweddict[resource]:
      raise InternalRepyError, "Should not be able to exceed resource count"

    if len(resourcesuseddict[resource]) == resourcesalloweddict[resource]:
      # it's clobberin time!
      raise ResourceExhaustedError("Resource '"+resource+"' limit exceeded!!")

    # add the item to the list.   We're done now...
    resourcesuseddict[resource].add(item)

  finally:
    resourcesuseddict['fungible_locks'][resource].release()

    



def _tattle_remove_item(resource, item, resourcesalloweddict, resourcesuseddict):
  """
   <Purpose>
      Let the nanny know that the process is releasing a fungible but 
      non-renewable resource.

   <Arguments>
      resource:
         A string with the resource name.   
      item:
         A unique identifier that specifies the resource.   It is used to
         prevent duplicate additions and removals and so must be unique for
         each item used.
         
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
  """

  resourcesuseddict['fungible_locks'][resource].acquire()

  # always unlock as we exit...
  try: 
    
    try:
      resourcesuseddict[resource].remove(item)
    except KeyError:
      # may happen because removal is idempotent
      pass

  finally:
    resourcesuseddict['fungible_locks'][resource].release()



# used for individual_item_resources
def _is_item_allowed(resource, item, resourcesalloweddict, resourcesuseddict):
  """
   <Purpose>
      Check if the process can acquire a non-fungible, non-renewable resource.

   <Arguments>
      resource:
         A string with the resource name.   
      item:
         A unique identifier that specifies the resource.   It has some
         meaning to the caller (like a port number for TCP or UDP), but is 
         opaque to the nanny.   
         
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True or False
  """

  if item in resourcesalloweddict[resource]:
    # this is semi nonsensical, but allows us to indicate which ports are used
    # through get_resource_information()
    resourcesuseddict[resource].add(item)
    return True

  else:
    return False






############################ Externally called ########################



def start_resource_nanny(resourcefilename):
  """
   <Purpose>
      Initializes the resource information the nanny needs to do monitoring.

   <Arguments>
      resourcefilename: the file that contains the set of resources we will
      use.
         
   <Exceptions>
      ResourceParseError if the resource file is invalid

   <Side Effects>
      None

   <Returns>
      None.
  """

  global _resources_allowed_dict

  global _resources_consumed_dict 

  # get the resource information from disk
  _resources_allowed_dict = resourcemanipulation.read_resourcedict_from_file(resourcefilename)

  # this sets up a dictionary with the correct locks, etc. for tracking
  # resource use.
  _resources_consumed_dict = _create_resource_consumption_dict()
  

def tattle_quantity(resource, quantity):
  return _tattle_quantity(resource, quantity, _resources_allowed_dict, _resources_consumed_dict)
  

def tattle_add_item(resource, item):
  return _tattle_add_item(resource, item, _resources_allowed_dict, _resources_consumed_dict)


def tattle_remove_item(resource, item):
  return _tattle_remove_item(resource, item, _resources_allowed_dict, _resources_consumed_dict)

def is_item_allowed(resource, item):
  return _is_item_allowed(resource, item, _resources_allowed_dict, _resources_consumed_dict)



# Armon: This is an extremely basic wrapper function, that just allows
# for pre/post processing if required in the future
def get_resource_limit(resource):
  """
  <Purpose>
    Returns the limit or availability of a resource.

  <Arguments>
    resource:
      The resource about which information is being requested.

  <Exceptions>
    KeyError if the resource does not exist.

  <Side Effects>
    None

  <Returns>
    The resource availability or limit.
  """

  return _resources_allowed_dict[resource]









def calculate_cpu_sleep_interval(cpulimit, percentused, elapsedtime):
  """
  <Purpose>
    Calculates proper CPU sleep interval to best achieve target cpulimit.
  
  <Arguments>
    cpulimit:
      The target cpu usage limit
    percentused:
      The percentage of cpu used in the interval between the last sample of the process
    elapsedtime:
      The amount of time elapsed between last sampling the process
  
  <Exceptions>
    ZeroDivisionError if elapsedtime is 0.
  
  <Side Effects>
    None, this just does math

  <Returns>
    Time period the process should sleep
  """
  # Debug: Used to calculate averages
  #global totaltime, rawcpu, appstart

  # Return 0 if elapsedtime is non-positive
  if elapsedtime <= 0:
    return 0
    
  # Calculate Stoptime
  #  Mathematically Derived from:
  #  (PercentUsed * TotalTime) / ( TotalTime + StopTime) = CPULimit
  stoptime = max(((percentused * elapsedtime) / cpulimit) - elapsedtime , 0)

  # Print debug info
  #rawcpu += percentused*elapsedtime
  #totaltime = time.time() - appstart
  #print totaltime , "," , (rawcpu/totaltime) , "," ,elapsedtime , "," ,percentused
  #print percentused, elapsedtime
  #print "Stopping: ", stoptime

  # Return amount of time to sleep for
  return stoptime



def get_resource_information():
  """
  <Purpose>
    Returns information about how many resources have been used.
  
  <Arguments>
    None
  
  <Exceptions>
    None
  
  <Side Effects>
    None

  <Returns>
    A tuple: (the allowed resource dict, and usage dict).   Usage information
    is sanitized to remove unnecessary things like locks.
  """


  # the resources we are allowed to use is easy.   We just copy this...
  resource_limit_dict = _resources_allowed_dict.copy()

  
  # from the other dict, we only take the resource information.   (this omits
  # locks and timing information that isn't needed)

  # first, let's do the easy thing, the quantity resources.   These are just 
  # floats
  resource_use_dict = {}
  for resourcename in resource_constants.quantity_resources:
    resource_use_dict[resourcename] = _resources_consumed_dict[resourcename]

  # for the fungible resources (files opened, etc,), we only need a count...
  for resourcename in resource_constants.fungible_item_resources:
    resource_use_dict[resourcename] = len(_resources_consumed_dict[resourcename])

  # for the individual item resources (ports, etc,), we copy the set...
  for resourcename in resource_constants.individual_item_resources:
    resource_use_dict[resourcename] = _resources_consumed_dict[resourcename].copy()

  # and that's it!
  return (resource_limit_dict, resource_use_dict)



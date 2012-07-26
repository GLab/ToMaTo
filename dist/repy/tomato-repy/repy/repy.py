""" 
<Author>
  Justin Cappos
  Ivan Beschastnikh (12/24/08) -- added usage
  Brent Couvrette   (2/27/09) -- added servicelog commandline option
  Conrad Meyer (5/22/09) -- switch option parsing to getopt

<Start Date>
  June 26th, 2008

<Description>
  Restricted execution environment for python.  Should stop someone
  from doing "bad things" (which is also defined to include many
  useful things).  This module allows the user to define code that
  gets called either on the receipt of a packet, when a timer fires,
  on startup, and on shutdown.  The restricted code can only do a few
  "external" things like send data packets and store data to disk.
  The CPU, memory, disk usage, and network bandwidth are all limited.

<Usage>
  Usage: repy.py [options] resourcefn program_to_run.repy [program args]

  Where [options] are some combination of the following:

  --simple               : Simple execution mode -- execute and exit
  --ip IP                : This flag informs Repy that it is allowed to bind to the given given IP.
                         : This flag may be asserted multiple times.
                         : Repy will attempt to use IP's and interfaces in the order they are given.
  --iface interface      : This flag informs Repy that it is allowed to bind to the given interface.
                         : This flag may be asserted multiple times.
  --nootherips           : Instructs Repy to only use IP's and interfaces that are explicitly given.
                         : It should be noted that loopback (127.0.0.1) is always permitted.
  --logfile filename.txt : Set up a circular log buffer and output to logfilename.txt
  --stop filename        : Repy will watch for the creation of this file and abort when it happens
                         : File can have format EXITCODE;EXITMESG. Code 44 is Stopped and is the default.
                         : EXITMESG will be printed prior to exiting if it is non-null.
  --status filename.txt  : Write status information into this file
  --cwd dir              : Set Current working directory
  --servicelog           : Enable usage of the servicelogger for internal errors
"""


# Let's make sure the version of python is supported
import checkpythonversion
checkpythonversion.ensure_python_version_is_supported()

import idhelper
import safe
import sys
import getopt
import emulcomm
import namespace
import nanny
import time
import threading
import loggingrepy

import nmstatusinterface

import harshexit

import statusstorage

import repy_constants   

import os

# Armon: Using VirtualNamespace as an abstraction around direct execution
import virtual_namespace

## we'll use tracebackrepy to print our exceptions
import tracebackrepy

import nonportable

from exception_hierarchy import *

# BAD: REMOVE these imports after we remove the API calls
import emulfile
import emulmisc
import emultimer

# Disables safe, and resumes normal fork
def nonSafe_fork():
  val = __orig_fork()
  if val == 0 and safe._builtin_globals_backup != None:
    safe._builtin_restore()
  return val

# Only override fork if it exists (e.g. Windows)
if "fork" in dir(os):  
  __orig_fork = os.fork
  os.fork = nonSafe_fork



def main(resourcefn, program, args):

  # Armon: Initialize the circular logger before starting the nanny
  if logfile:
    # time to set up the circular logger
    loggerfo = loggingrepy.circular_logger(logfile)
    # and redirect err and out there...
    sys.stdout = loggerfo
    sys.stderr = loggerfo
  else:
    # let's make it so that the output (via print) is always flushed
    sys.stdout = loggingrepy.flush_logger(sys.stdout)
    
  # start the nanny up and read the resource file.  
  nanny.start_resource_nanny(resourcefn)

  # now, let's fire up the cpu / disk / memory monitor...
  nonportable.monitor_cpu_disk_and_mem()

  # Armon: Update our IP cache
  emulcomm.update_ip_cache()


  # These will be the functions and variables in the user's namespace (along
  # with the builtins allowed by the safe module).
  usercontext = {'mycontext':{}}
  
  # Add to the user's namespace wrapped versions of the API functions we make
  # available to the untrusted user code.
  namespace.wrap_and_insert_api_functions(usercontext)

  # Convert the usercontext from a dict to a SafeDict
  usercontext = safe.SafeDict(usercontext)

  # Allow some introspection by providing a reference to the context
  usercontext["_context"] = usercontext

  # BAD:REMOVE all API imports
  usercontext["getresources"] = nonportable.get_resources
  #usercontext["openfile"] = emulfile.emulated_open
  #usercontext["listfiles"] = emulfile.listfiles
  #usercontext["removefile"] = emulfile.removefile
  #usercontext["exitall"] = emulmisc.exitall
  #usercontext["createlock"] = emulmisc.createlock
  #usercontext["getruntime"] = emulmisc.getruntime
  #usercontext["randombytes"] = emulmisc.randombytes
  #usercontext["createthread"] = emultimer.createthread
  #usercontext["sleep"] = emultimer.sleep
  #usercontext["getthreadname"] = emulmisc.getthreadname
  usercontext["createvirtualnamespace"] = virtual_namespace.createvirtualnamespace
  usercontext["getlasterror"] = emulmisc.getlasterror
      
  # grab the user code from the file
  try:
    filehandle = open(program)
    usercode = filehandle.read()
    filehandle.close()
  except:
    print "Failed to read the specified file: '"+program+"'"
    raise

  # Armon: Create the main namespace
  try:
    main_namespace = virtual_namespace.VirtualNamespace(usercode, program)
  except CodeUnsafeError, e:
    print "Specified repy program is unsafe!"
    print "Static-code analysis failed with error: "+str(e)
    harshexit.harshexit(5)

  # Let the code string get GC'ed
  usercode = None

  # If we are in "simple execution" mode, execute and exit
  if simpleexec:
    main_namespace.evaluate(usercontext)
    sys.exit(0)


  # I'll use this to detect when the program is idle so I know when to quit...
  idlethreadcount =  threading.activeCount()

  # call the initialize function
  usercontext['callfunc'] = 'initialize'
  usercontext['callargs'] = args[:]
 
  event_id = idhelper.getuniqueid()
  try:
    nanny.tattle_add_item('events', event_id)
  except Exception, e:
    tracebackrepy.handle_internalerror("Failed to acquire event for '" + \
              "initialize' event.\n(Exception was: %s)" % e.message, 140)
 
  try:
    main_namespace.evaluate(usercontext)
  except SystemExit:
    raise
  except:
    # I think it makes sense to exit if their code throws an exception...
    tracebackrepy.handle_exception()
    harshexit.harshexit(6)
  finally:
    nanny.tattle_remove_item('events', event_id)

  # I've changed to the threading library, so this should increase if there are
  # pending events
  while threading.activeCount() > idlethreadcount:
    # do accounting here?
    time.sleep(0.25)


  # Once there are no more pending events for the user thread, we exit
  harshexit.harshexit(0)


def usage(str_err=""):
  # Ivan 12/24/2008
  """
   <Purpose>
      Prints repy.py usage and possibly an error supplied argument
   <Arguments>
      str_err (string):
        Options error to print to stdout
   <Exceptions>
      None
   <Side Effects>
      Modifies stdout
   <Returns>
      None
  """
  print
  if str_err:
    print "Error:", str_err
  print """
Usage: repy.py [options] resourcefile program_to_run.repy [program args]

Where [options] are some combination of the following:

--simple               : Simple execution mode -- execute and exit
--ip IP                : This flag informs Repy that it is allowed to bind to the given given IP.
                       : This flag may be asserted multiple times.
                       : Repy will attempt to use IP's and interfaces in the order they are given.
--iface interface      : This flag informs Repy that it is allowed to bind to the given interface.
                       : This flag may be asserted multiple times.
--nootherips           : Instructs Repy to only use IP's and interfaces that are explicitly given.
                       : It should be noted that loopback (127.0.0.1) is always permitted.
--logfile filename.txt : Set up a circular log buffer and output to logfilename.txt
--stop filename        : Repy will watch for the creation of this file and abort when it happens
                       : File can have format EXITCODE;EXITMESG. Code 44 is Stopped and is the default.
                       : EXITMESG will be printed prior to exiting if it is non-null.
--status filename.txt  : Write status information into this file
--cwd dir              : Set Current working directory
--servicelog           : Enable usage of the servicelogger for internal errors
"""
  return


if __name__ == '__main__':
  global simpleexec
  global logfile

  # Armon: The CMD line path to repy is the first argument
  repy_location = sys.argv[0]

  # Get the directory repy is in
  repy_directory = os.path.dirname(repy_location)
  
  # Translate into an absolute path
  if os.path.isabs(repy_directory):
    absolute_repy_directory = repy_directory
  
  else:
    # This will join the currect directory with the relative path
    # and then get the absolute path to that location
    absolute_repy_directory = os.path.abspath(os.path.join(os.getcwd(), repy_directory))
  
  # Store the absolute path as the repy startup directory
  repy_constants.REPY_START_DIR = absolute_repy_directory
 
  # For security, we need to make sure that the Python path doesn't change even
  # if the directory does...
  newsyspath = []
  for item in sys.path[:]:
    if item == '' or item == '.':
      newsyspath.append(os.getcwd())
    else:
      newsyspath.append(item)

  # It should be safe now.   I'm assuming the user isn't trying to undercut us
  # by setting a crazy python path
  sys.path = newsyspath

  
  args = sys.argv[1:]

  try:
    optlist, fnlist = getopt.getopt(args, '', [
      'simple', 'ip=', 'iface=', 'nootherips', 'logfile=',
      'stop=', 'status=', 'cwd=', 'servicelog'
      ])

  except getopt.GetoptError:
    usage()
    sys.exit(1)

  # Set up the simple variable if needed
  simpleexec = False

  # By default we don't want to use the service logger
  servicelog = False

  # Default logfile (if the option --logfile isn't passed)
  logfile = None

  # Default stopfile (if the option --stopfile isn't passed)
  stopfile = None

  # Default stopfile (if the option --stopfile isn't passed)
  statusfile = None

  if len(fnlist) < 2:
    usage("Must supply a resource file and a program file to execute")
    sys.exit(1)

  for option, value in optlist:
    if option == '--simple':
      simpleexec = True

    elif option == '--ip':
      emulcomm.user_ip_interface_preferences = True

      # Append this ip to the list of available ones if it is new, since
      # multiple IP's may be specified
      if (True, value) not in emulcomm.user_specified_ip_interface_list:
        emulcomm.user_specified_ip_interface_list.append((True, value))

    elif option == '--iface':
      emulcomm.user_ip_interface_preferences = True
      
      # Append this interface to the list of available ones if it is new
      if (False, value) not in emulcomm.user_specified_ip_interface_list:
        emulcomm.user_specified_ip_interface_list.append((False, value))

    # Check if they have told us explicitly not to allow other IP's
    elif option == '--nootherips':
      # Set user preference to True
      emulcomm.user_ip_interface_preferences = True
      # Disable nonspecified IP's
      emulcomm.allow_nonspecified_ips = False
    
    elif option == '--logfile':
      # set up the circular log buffer...
      logfile = value

    elif option == '--stop':
      # Watch for the creation of this file and abort when it happens...
      stopfile = value

    elif option == '--status':
      # Write status information into this file...
      statusfile = value

    # Set Current Working Directory
    elif option == '--cwd':
      os.chdir(value)

    # Enable logging of internal errors to the service logger.
    elif option == '--servicelog':
      servicelog = True

  # Update repy current directory
  repy_constants.REPY_CURRENT_DIR = os.path.abspath(os.getcwd())

  # Initialize the NM status interface
  nmstatusinterface.init(stopfile, statusfile)
  
  # Write out our initial status
  statusstorage.write_status("Started")

  resourcefn = fnlist[0]
  progname = fnlist[1]
  progargs = fnlist[2:]

  # We also need to pass in whether or not we are going to be using the service
  # log for repy.  We provide the repy directory so that the vessel information
  # can be found regardless of where we are called from...
  tracebackrepy.initialize(servicelog, absolute_repy_directory)

  try:
    main(resourcefn, progname, progargs)
  except SystemExit:
    harshexit.harshexit(4)
  except:
    tracebackrepy.handle_exception()
    harshexit.harshexit(3)

"""
   Author: Justin Cappos

   Start Date: 14 Sept 2008

   Description:

   This module stores status information about the sandbox.   Use "read_status"
   and "write_status" to set and check the status...

   This module works by creating a file with an name that indicates the status.
   The order of operations is: find old file name(s), write new file, delete 
   old file(s).   File names contain a timestamp so that one can tell when it
   was last updated.   The actual format is: "prefix-status-timestamp".  

"""

# to store the current time...
import time

# needed to get a lock
import threading

# needed for listdir...
import os

# To allow access to a real fileobject 
# call type...
myfile = file

statusfilenameprefix = None

# This prevents writes to the nanny's status information after we want to stop
statuslock = threading.Lock()

def init(sfnp):
  global statusfilenameprefix
  statusfilenameprefix = sfnp


# Write out a status that can be read by another process...
def write_status(status, mystatusfilenameprefix=None):

  if not mystatusfilenameprefix:
    mystatusfilenameprefix = statusfilenameprefix

  # nothing set, nothing to do...
  if not mystatusfilenameprefix:
    return
  
  mystatusdir = os.path.dirname(mystatusfilenameprefix)
  if mystatusdir == '':
    mystatusdir = './'
  else:
    mystatusdir = mystatusdir+'/'

  # BUG: Is getting a directory list atomic wrt file creation / deletion?
  # get the current file list...
  # Fix.   Need to prepend the directory name we're writing into...
  existingfiles = os.listdir(mystatusdir)

  timestamp = time.time()

  # write the file
  myfile(mystatusfilenameprefix+"-"+status+"-"+str(timestamp),"w").close()

  # remove the old files...
  for filename in existingfiles:
    if len(filename.split('-')) == 3 and filename.split('-')[0] == os.path.basename(mystatusfilenameprefix):
      try:
        os.remove(mystatusdir+filename)
      except OSError, e:
        if e[0] == 2:
          # file not found, let's assume another instance removed it...
          continue

        # otherwise, let's re-raise the error
        raise
  

def read_status(mystatusfilenameprefix=None):

  if not mystatusfilenameprefix:
    mystatusfilenameprefix = statusfilenameprefix
  
  # BUG: is getting a dir list atomic wrt file creation / deletion?
  # get the current file list...
  # Fix.   Need to prepend the directory name we're writing into...
  if os.path.dirname(mystatusfilenameprefix):
    existingfiles = os.listdir(os.path.dirname(mystatusfilenameprefix))
  else:
    existingfiles = os.listdir('.')

  latesttime = 0
  lateststatus = None

  # find the newest status update...
  for filename in existingfiles:
    if filename.split('-')[0] == mystatusfilenameprefix:
      thisstatus = filename.split('-',2)[1]
      thistime = float(filename.split('-',2)[2])

      # is this the latest?
      if thistime > latesttime:
        latesttime = thistime
        lateststatus = thisstatus

  return (lateststatus, latesttime)




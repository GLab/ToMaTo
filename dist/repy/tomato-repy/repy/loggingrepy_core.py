"""
   Author: Justin Cappos

   Start Date: 22 July 2008

   Description:

   Refactored logging code that used to be in emulfile
"""

# needed for remove and path.exists
import os 

# for Lock
import threading

# I need to rename file so that the checker doesn't complain...
myfile = file


# used to make stdout flush as written   This is private to my code
class flush_logger_core:
  """
    A file-like class that can be used in lieu of stdout.   It always flushes
    data after a write.

  """

  def __init__(self, fobj):
    self.fileobj = fobj

    # I do not use these.   This is merely for API convenience
    self.mode = None
    self.name = None
    self.softspace = 0

    return None 


  def close(self):
    return self.fileobj.close()


  def flush(self):
    return self.fileobj.flush()


  def write(self,writeitem):
    self.fileobj.write(writeitem)
    self.flush()


  def writelines(self,writelist):
    self.fileobj.writelines(writelist)
    self.flush()

# End of flush_logger class




# helper function
def get_size(fn):
  fo = myfile(fn,"r")
  data = fo.read()
  fo.close()
  return len(data)



# used to implement the circular log buffer
class circular_logger_core:
  """
    A file-like class that writes to what is conceptually a circular buffer.   
    After being filled, the buffer is always >=16KB and always flushed after 
    write...   
    
    I accomplish this by actually writing to two files.   Once >=16 KB has been
    written, the first file will always* be of size 16KB and the second file
    fills as the user writes.   Once the second file reaches 16KB, it is
    moved to overwrite the first file and a new second file is created.
    
    *not always on some systems because moving files isn't atomic

  """


  def __init__(self, fnp, mbs = 16 * 1024):
    # I do not use these.   This is merely for API convenience
    self.mode = None
    self.name = None
    self.softspace = 0

    # the size before we "rotate" the logfiles
    self.maxbuffersize = mbs # default listed in constructor

    # filenames we'll use for the log data
    self.filenameprefix = fnp
    self.oldfn = fnp+".old"
    self.newfn = fnp+".new"

    # prevent race conditions when writing
    self.writelock = threading.Lock()

    
    # we need to set up the currentsize, activefo and first variables...
    if os.path.exists(self.newfn):
      # the new file exists.   

      if os.path.exists(self.oldfn):
        # the old file exists too (the common case)   

        self.currentsize = get_size(self.newfn)
        self.activefo = myfile(self.newfn,"a")
        self.first = False
        # now we have the fileobject and the size set up.   We're ready...
        return

      else:
        # a corner case.   The old file was removed but the new was not yet 
        # copied over
        os.rename(self.newfn, self.oldfn)
        self.currentsize = 0
        self.activefo = myfile(self.newfn,"w")
        self.first = False
        return

    else:
 
      if os.path.exists(self.oldfn):
        # the old file name exists, so we should start from here

        self.currentsize = get_size(self.oldfn)
        self.activefo = myfile(self.oldfn,"a")
        self.first = True
        # now we have the fileobject and the size set up.   We're ready...
        return

      else:
        # starting from nothing...
        self.currentsize = 0
        self.activefo = myfile(self.oldfn,"w")
        self.first = True
        return




  # No-op
  def close(self):
    return 



  # No-op, I always flush myself
  def flush(self):
    return


  def write(self,writeitem):
    # they / we can always log info (or else what happens on exception?)

    # acquire (and release later no matter what)
    self.writelock.acquire()
    try:
      writeamt = self.writedata(writeitem)
    finally:
      self.writelock.release()



  def writelines(self,writelist):
    # we / they can always log info (or else what happens on exception?)

    # acquire (and release later no matter what)
    self.writelock.acquire()
    try:
      for writeitem in writelist:
        self.writedata(writeitem)
    finally:
      self.writelock.release()


  # internal functions (not externally called)

  # rotate the log files (make the new the old, and get a new file
  def rotate_log(self):
    self.activefo.close()
    try:
      os.rename(self.newfn, self.oldfn)

    except WindowsError:  # Windows no likey when rename overwrites
      os.remove(self.oldfn)
      os.rename(self.newfn, self.oldfn)
 
    self.activefo = myfile(self.newfn,"w")
    

  def write_first_log(self):
    self.activefo.close()
    self.activefo = myfile(self.newfn,"w")
    


  # I could write this in about 1/4 the code, but it would be much harder to 
  # read.   
  def writedata(self, data):


    # first I'll dispose of the common case
    if len(str(data)) + self.currentsize <= self.maxbuffersize:
      # didn't fill the buffer
      self.activefo.write(str(data))
      self.activefo.flush()
      self.currentsize = self.currentsize + len(str(data))
      return len(str(data))

    # now I'll deal with the "longer-but-still-fits case"
    if len(str(data))+self.currentsize <= self.maxbuffersize*2:
      # finish off this file
      splitindex = self.maxbuffersize - self.currentsize
      self.activefo.write(str(data[:splitindex]))
      self.activefo.flush()

      # rotate logs
      if self.first:
        self.write_first_log()
        self.first = False
      else:
        self.rotate_log()

      # now write the last bit of data...
      self.activefo.write(str(data[splitindex:]))
      self.activefo.flush()
      self.currentsize = len(str(data[splitindex:]))
      return len(str(data))

    # now the "really-long-write case"
    # Note, I'm going to avoid doing any extra "alignment" on the data.   In
    # other words, if they write some multiple of 16KB, and they currently have
    # a full file and a file with 7 bytes, they'll end up with a full file and
    # a file with 7 bytes

    datasize = len(str(data))

    # this is what data the new file should contain (the old file will contain
    # the 16KB of data before this)
    lastchunk = (datasize + self.currentsize) % self.maxbuffersize

    # I'm going to write the old file and new file now
    #
    # Note: I break some of the guarantees about being able to 
    # recover disk state here 
    self.activefo.close()
    if self.first: 
      # remove existing files (unnecessary on some platforms)
      os.remove(self.oldfn)
    else:
      # remove existing files (unnecessary on some platforms)
      os.remove(self.oldfn)
      os.remove(self.newfn)

    oldfo = myfile(self.oldfn,"w")

    # write the data counting backwards from the end of the file
    oldfo.write(data[-(lastchunk+self.maxbuffersize):-lastchunk])
    oldfo.close()

    # next...
    self.activefo = myfile(self.newfn,"w")

    # now write the last bit of data...
    self.activefo.write(str(data[-lastchunk:]))
    self.activefo.flush()
    self.currentsize = len(str(data[-lastchunk:]))

    # charge them for only the data we actually wrote
    return self.currentsize + self.maxbuffersize



# End of circular_logger class

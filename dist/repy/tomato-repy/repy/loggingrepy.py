"""
   Author: Conrad Meyer

   Start Date: 30 Nov 2009

   Description:

   Wrapper around loggingrepy_core that provides restriction management
   and nannying.
"""


import nanny
import loggingrepy_core


get_size = loggingrepy_core.get_size
myfile = loggingrepy_core.myfile


class flush_logger(loggingrepy_core.flush_logger_core):
  """
    A file-like class that can be used in lieu of stdout.   It always flushes
    data after a write. This one uses nanny.

  """

  def write(self, writeitem):
    # block if already over
    nanny.tattle_quantity('lograte', 0)

    # do the actual write
    loggingrepy_core.flush_logger_core.write(self, writeitem)

    # block if over after log write
    writeamt = len(str(writeitem))
    nanny.tattle_quantity('lograte', writeamt)


  def writelines(self, writelist):
    # block if already over
    nanny.tattle_quantity('lograte', 0)

    # do the actual writelines()
    loggingrepy_core.flush_logger_core.writelines(self, writelist)

    # block if over after log write
    writeamt = 0
    for writeitem in writelist:
      writeamt = writeamt + len(str(writeitem))
    nanny.tattle_quantity('lograte', writeamt)




class circular_logger(loggingrepy_core.circular_logger_core):
  """
    A file-like class that writes to what is conceptually a circular buffer.   
    After being filled, the buffer is always >=16KB and always flushed after 
    write...   
    
    I accomplish this by actually writing to two files.   Once >=16 KB has been
    written, the first file will always* be of size 16KB and the second file
    fills as the user writes.   Once the second file reaches 16KB, it is
    moved to overwrite the first file and a new second file is created.
    
    *not always on some systems because moving files isn't atomic

    This version of the class reports resource consumption with nanny.

  """


  def __init__(self, fnp, mbs = 16*1024, use_nanny=True):
    loggingrepy_core.circular_logger_core.__init__(self, fnp, mbs)

    # Should we be using the nanny to limit the lograte
    self.should_nanny = use_nanny


  def write(self, writeitem):
    # they / we can always log info (or else what happens on exception?)

    # acquire (and release later no matter what)
    self.writelock.acquire()
    try:
      if self.should_nanny:
        # Only invoke the nanny if the should_nanny flag is set.
        # block if already over
        nanny.tattle_quantity('lograte',0)

      writeamt = self.writedata(writeitem)

      if self.should_nanny:
        # Only invoke the nanny if the should_nanny flag is set.
        nanny.tattle_quantity('lograte',writeamt)

    finally:
      self.writelock.release()


  def writelines(self, writelist):
    # we / they can always log info (or else what happens on exception?)

    # acquire (and release later no matter what)
    self.writelock.acquire()
    try:
      if self.should_nanny:
        # Only invoke the nanny if the should_nanny flag is set.
        # block if already over
        nanny.tattle_quantity('lograte',0)
  
      writeamt = 0
      for writeitem in writelist:
        writeamt = writeamt + self.writedata(writeitem)

      if self.should_nanny:
        # Only invoke the nanny if the should_nanny flag is set.
        nanny.tattle_quantity('lograte',writeamt)
  
    finally:
      self.writelock.release()

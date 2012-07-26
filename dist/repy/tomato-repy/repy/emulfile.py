"""
   Author: Justin Cappos, Armon Dadgar

   Start Date: 27 June 2008
   V.2 Start Date: January 14th 2009

   Description:

   This is a collection of functions, etc. that need to be emulated in order
   to provide the programmer with a reasonable environment.   This is used
   by repy.py to provide a highly restricted (but usable) environment.
"""

import nanny

# Used for path and file manipulation
import os 
import os.path

# Used to handle a fatal exception
import tracebackrepy

# Used to get a lock object
import threading

# Get access to the current working directory
import repy_constants

# Import all the exceptions
from exception_hierarchy import *

# Fix for ticket #983. By retaining a reference to unicode, we prevent
# os.path.abspath from failing in some versions of python when the unicode
# builtin is overwritten.
os.path.unicode = unicode

# Store a reference to open, so that we retain access
# after the builtin's are disabled
safe_open = open

##### Constants

# This restricts the number of characters in filenames
MAX_FILENAME_LENGTH = 120

# This is the set of characters which are allowed in a file name
ALLOWED_FILENAME_CHAR_SET = set('abcdefghijklmnopqrstuvwxyz0123456789._-')

# This is the set of filenames which are forbidden.
ILLEGAL_FILENAMES = set(["", ".", ".."])


##### Module data

# This set contains the filenames of every file which is open
# Access to this set should be serialized via the OPEN_FILES_LOCK
OPEN_FILES_LOCK = threading.Lock()
OPEN_FILES = set([])


##### Public Functions

def listfiles():
  """
   <Purpose>
      Allows the user program to get a list of files in their vessel.

   <Arguments>
      None

   <Exceptions>
      None

   <Side Effects>
      None

  <Resource Consumption>
    Consumes 4K of fileread.

   <Returns>
      A list of strings (file names)
  """
  # We will consume 4K of fileread
  nanny.tattle_quantity('fileread', 4096)

  # Get the list of files from the current directory
  files = os.listdir(repy_constants.REPY_CURRENT_DIR)


  # Return the files
  return files


def removefile(filename):
  """
   <Purpose>
      Allows the user program to remove a file in their area.

   <Arguments>
      filename: the name of the file to remove.   It must not contain 
      characters other than 'a-zA-Z0-9.-_' and cannot be '.', '..' or
      the empty string.

   <Exceptions>
      RepyArgumentError is raised if the filename is invalid.
      FileInUseError is raised if the file is already open.
      FileNotFoundError is raised if the file does not exist

   <Side Effects>
      None

  <Resource Consumption>
      Consumes 4K of fileread.   If successful, also consumes 4K of filewrite.

   <Returns>
      None
  """

  # raise an RepyArgumentError if the filename isn't valid
  _assert_is_allowed_filename(filename)

  OPEN_FILES_LOCK.acquire()
  try:
    # Check if the file is in use
    if filename in OPEN_FILES:
      raise FileInUseError('Cannot remove file "'+filename+'" because it is in use!')

    # Get the absolute file name
    absolute_filename = os.path.abspath(os.path.join(repy_constants.REPY_CURRENT_DIR, filename))

    # Check if the file exists
    nanny.tattle_quantity('fileread', 4096)
    if not os.path.isfile(absolute_filename):
      raise FileNotFoundError('Cannot remove non-existent file "'+filename+'".')

    # Consume the filewrite resources
    nanny.tattle_quantity('filewrite',4096)

    # Remove the file (failure is an internal error)
    os.remove(absolute_filename)

  
  finally:
    OPEN_FILES_LOCK.release()


def emulated_open(filename, create):
  """
   <Purpose>
      Allows the user program to open a file safely. 

   <Arguments>
      filename:
        The file that should be operated on. It must not contain characters 
        other than 'a-z0-9.-_' and cannot be '.', '..', the empty string or 
        begin with a period.

      create:
         A Boolean flag which specifies if the file should be created
         if it does not exist.

   <Exceptions>
      RepyArgumentError is raised if the filename is invalid.
      FileInUseError is raised if a handle to the file is already open.
      ResourceExhaustedError is raised if there are no available file handles.
      FileNotFoundError is raised if the filename is not found, and create is False.

   <Side Effects>
      Opens a file on disk, uses a file descriptor.

   <Resource Consumption>
      Consumes 4K of fileread. If the file is created, then 4K of filewrite is used.
      If a handle to the object is created, then a file descriptor is used.

   <Returns>
      A file-like object.
  """
  # Call directly into our private initializer
  return emulated_file(filename, create)



##### Private functions


def _assert_is_allowed_filename(filename):
  """
  <Purpose>
    Private method to check if a filename is allowed.

  <Arguments>
    filename:
      The filename to check.

  <Exceptions>
    Raises a RepyArgumentError if the filename is not allowed.

  <Returns>
    None
  """

  # Check the type
  if type(filename) is not str:
    raise RepyArgumentError("Filename is not a string!")

  # Check the length of the filename
  if len(filename) > MAX_FILENAME_LENGTH:
    raise RepyArgumentError("Filename exceeds maximum length! Maximum: "+str(MAX_FILENAME_LENGTH))

  # Check if the filename is forbidden
  if filename in ILLEGAL_FILENAMES:
    raise RepyArgumentError("Illegal filename provided!")

  # Check that each character in the filename is allowed
  for char in filename:
    if char not in ALLOWED_FILENAME_CHAR_SET:
      raise RepyArgumentError("Filename has disallowed character '"+char+"'")

  # Check to make sure the filename does not start with a period.
  if filename.startswith('.'):
    raise RepyArgumentError("Filename starts with a period, this is not allowed!")



##### Class Definitions


class emulated_file (object):
  """
    A safe class which enables a very primitive file interaction.
    We only allow reading and writing at a provided index.
  """

  # We use the following instance variables.
  # filename is the name of the file we've opened,
  # abs_filename is the absolute path to the file we've opened,
  # and is the unique handle used to tattle the "filesopened" to nanny.
  #
  # fobj is the actual underlying file-object from python.
  # seek_lock is a Lock object to serialize seeking
  # size is the byte size of the file, to detect seeking past the end.
  __slots__ = ["filename", "abs_filename", "fobj", "seek_lock", "filesize"]

  def __init__(self, filename, create):
    """
      This is an internal initializer.   See emulated_open for details.
    """
    # Initialize the fields, otherwise __del__ gets confused
    # when we throw an exception. This was not a problem when the
    # logic was in emulated_open, since we would never throw an
    # exception
    self.filename = filename
    self.abs_filename = None
    self.fobj = None
    self.seek_lock = threading.Lock()
    self.filesize = 0

    # raise an RepyArgumentError if the filename isn't valid
    _assert_is_allowed_filename(filename)

    # Check the  type of create
    if type(create) is not bool:
      raise RepyArgumentError("Create argument type is invalid! Must be a Boolean!")

    OPEN_FILES_LOCK.acquire()
    try:
      # Check if the file is in use
      if filename in OPEN_FILES:
        raise FileInUseError('Cannot open file "'+filename+'" because it is already open!')

      # Get the absolute file name
      self.abs_filename = os.path.abspath(os.path.join(repy_constants.REPY_CURRENT_DIR, filename))
      

      # Here is where we try to allocate a "file" resource from the
      # nanny system.   We will restore this below if there is an exception
      # This may raise a ResourceExhautedError
      nanny.tattle_add_item('filesopened', self.abs_filename)

      
      # charge for checking if the file exists.
      nanny.tattle_quantity('fileread', 4096)
      exists = os.path.isfile(self.abs_filename)

      # if there isn't a file already...
      if not exists:
        # if we shouldn't create it, it's an error
        if not create:
          raise FileNotFoundError('Cannot openfile non-existent file "'+filename+'" without creating it!')

        # okay, we should create it...
        nanny.tattle_quantity('filewrite', 4096)
        safe_open(self.abs_filename, "w").close() # Forces file creation

      # Store a file handle
      # Always open in mode r+b, this avoids Windows text-mode
      # quirks, and allows reading and writing
      self.fobj = safe_open(self.abs_filename, "r+b")

      # Add the filename to the open files
      OPEN_FILES.add(filename)

      # Get the file's size
      self.filesize = os.path.getsize(self.abs_filename)

    except RepyException:
      # Restore the file handle we tattled
      nanny.tattle_remove_item('filesopened', self.abs_filename)
      raise

    finally:
      OPEN_FILES_LOCK.release()


  def close(self):
    """
    <Purpose>
      Allows the user program to close the handle to the file.

    <Arguments>
      None.

    <Exceptions>
      FileClosedError is raised if the file is already closed.

    <Resource Consumption>
      Releases a file handle.

    <Returns>
      None.
    """

    # Acquire the lock to the set 
    OPEN_FILES_LOCK.acquire()

    # Tell nanny we're gone.
    nanny.tattle_remove_item('filesopened', self.abs_filename)
    
    # Acquire the seek lock
    self.seek_lock.acquire()
  
    try:
      # Release the file object
      fobj = self.fobj
      if fobj is not None:
        fobj.close()
        self.fobj = None
      else:
        raise FileClosedError("File '"+str(self.filename)+"' is already closed!")

      # Remove this file from the list of open files
      OPEN_FILES.remove(self.filename)

    finally:
      # Release the two locks we hold
      self.seek_lock.release()
      OPEN_FILES_LOCK.release()


  def readat(self,sizelimit,offset):
    """
    <Purpose>
      Reads from a file handle. Reading 0 bytes informs you if you have read
      past the end-of-file, but returns no data.

    <Arguments>
      sizelimit: 
        The maximum number of bytes to read from the file. Reading EOF will 
        read less.   By setting this value to None, the entire file is read.
      offset:
        Seek to a specific absolute offset before reading.

    <Exceptions>
      RepyArgumentError is raised if the offset or size is negative.
      FileClosedError is raised if the file is already closed.
      SeekPastEndOfFileError is raised if trying to read past the end of the file.

    <Resource Consumption>
      Consumes 4K of fileread for each 4K aligned-block of the file read.
      All reads will consume at least 4K.

    <Returns>
      The data that was read. This may be the empty string if we have reached the
      end of the file, or if the sizelimit was 0.
    """
    # Check the arguments
    if sizelimit < 0 and sizelimit != None:
      raise RepyArgumentError("Negative sizelimit specified!")
    if offset < 0:
      raise RepyArgumentError("Negative read offset speficied!")

    # Get the seek lock
    self.seek_lock.acquire()

    try:
      # Get the underlying file object
      fobj = self.fobj
      if fobj is None:
        raise FileClosedError("File '"+self.filename+"' is already closed!")

      # Check the provided offset
      if offset > self.filesize:
        raise SeekPastEndOfFileError("Seek offset extends past the EOF!")
      
      # Seek to the correct location
      fobj.seek(offset)

      # Wait for available file read resources
      nanny.tattle_quantity('fileread',0)

      if sizelimit != None:
        # Read the data
        data = fobj.read(sizelimit)
      else:
        # read all the data...
        data = fobj.read()

    finally:
      # Release the seek lock
      self.seek_lock.release()

    # Check how much we've read, in terms of 4K "blocks"
    end_offset = len(data) + offset
    disk_blocks_read = end_offset / 4096 - offset / 4096
    if end_offset % 4096 > 0:
      disk_blocks_read += 1

    # Charge 4K per block
    nanny.tattle_quantity('fileread', disk_blocks_read*4096)

    # Return the data
    return data


  def writeat(self,data,offset):
    """
    <Purpose>
      Allows the user program to write data to a file.

    <Arguments>
      data: The data to write
      offset: An absolute offset into the file to write

    <Exceptions>
      RepyArgumentError is raised if the offset is negative or the data is not
      a string.
      FileClosedError is raised if the file is already closed.
      SeekPastEndOfFileError is raised if trying to write past the EOF.

    <Side Effects>
      Writes to persistent storage.

    <Resource Consumption>
      Consumes 4K of filewrite for each 4K aligned-block of the file written.
      All writes consume at least 4K.

    <Returns>
      Nothing
    """
    # Check the arguments
    if offset < 0:
      raise RepyArgumentError("Negative read offset speficied!")
    if type(data) is not str:
      raise RepyArgumentError("Data must be specified as a string!")

    # Get the seek lock
    self.seek_lock.acquire()

    try:
      # Get the underlying file object
      fobj = self.fobj
      if fobj is None:
        raise FileClosedError("File '"+self.filename+"' is already closed!")
 
      # Check the provided offset
      if offset > self.filesize:
        raise SeekPastEndOfFileError("Seek offset extends past the EOF!")
      
      # Seek to the correct location
      fobj.seek(offset)

      # Wait for available file write resources
      nanny.tattle_quantity('filewrite',0)

      # Write the data and flush to disk
      fobj.write(data)
      fobj.flush()

      # Check if we expanded the file size
      if offset + len(data) > self.filesize:
        self.filesize = offset + len(data)

    finally:
      # Release the seek lock
      self.seek_lock.release()

    # Check how much we've written, in terms of 4K "blocks"
    end_offset = len(data) + offset
    disk_blocks_written = end_offset / 4096 - offset / 4096
    if end_offset % 4096 > 0:
      disk_blocks_written += 1

    # Charge 4K per block
    nanny.tattle_quantity('filewrite', disk_blocks_written*4096)


  def __del__(self):
    # this ensures that during interpreter cleanup, that the order of 
    # freed memory doesn't matter.   If we don't have this, then
    # OPEN_FILES_LOCK and other objects might get cleaned up first and cause
    # the close call below to print an exception
    if OPEN_FILES_LOCK == None:
      return


    # Make sure we are closed
    try:
      self.close()
    except FileClosedError:
      pass # Good, we are already closed.


# End of emulated_file class

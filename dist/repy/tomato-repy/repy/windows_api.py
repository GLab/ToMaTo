# Armon Dadgar
# 
# Creates python interface for windows api calls that are required 
#
# According to MSDN most of these calls are Windows 2K Pro and up
# Trying to replace the win32* stuff using ctypes

# Ctypes enable us to call the Windows API which written in C
import ctypes

# Needed so that we can sleep
import time 

# Used for OS detection
import os

# Used for processing command output (netstat, etc)
import textops

# Detect whether or not it is Windows CE/Mobile
MobileCE = False
if os.name == 'ce':
  MobileCE = True
else:
  import portable_popen

# Main Libraries
# Loaded depending on OS
if MobileCE:
  # kerneldll links to the library that has Windows Kernel Calls
  kerneldll = ctypes.cdll.coredll

  # Toolhelp library
  # Contains Tool helper functions
  toolhelp = ctypes.cdll.toolhelp

else:
  # kerneldll links to the library that has Windows Kernel Calls
  kerneldll = ctypes.windll.kernel32 
  # memdll links to the library that has Windows Process/Thread Calls
  memdll = ctypes.windll.psapi

# Types
DWORD = ctypes.c_ulong # Map Microsoft DWORD type to C long
WORD = ctypes.c_ushort # Map microsoft WORD type to C ushort
HANDLE = ctypes.c_ulong # Map Microsoft HANDLE type to C long
LONG = ctypes.c_long # Map Microsoft LONG type to C long
SIZE_T = ctypes.c_ulong # Map Microsoft SIZE_T type to C long
ULONG_PTR = ctypes.c_ulong # Map Microsoft ULONG_PTR to C long
LPTSTR = ctypes.c_char_p # Map Microsoft LPTSTR to a pointer to a string
LPCSTR = ctypes.c_char_p  # Map Microsoft LPCTSTR to a pointer to a string
ULARGE_INTEGER = ctypes.c_ulonglong # Map Microsoft ULARGE_INTEGER to 64 bit int
LARGE_INTEGER = ctypes.c_longlong # Map Microsoft ULARGE_INTEGER to 64 bit int
DWORDLONG = ctypes.c_ulonglong # Map Microsoft DWORDLONG to 64 bit int

# General Constants
ULONG_MAX = 4294967295 # Maximum value for an unsigned long, 2^32 -1

# Microsoft Constants
TH32CS_SNAPTHREAD = ctypes.c_ulong(0x00000004) # Create a snapshot of all threads
TH32CS_SNAPPROCESS = ctypes.c_ulong(0x00000002) # Create a snapshot of a process
TH32CS_SNAPHEAPLIST = ctypes.c_ulong(0x00000001) # Create a snapshot of a processes heap
INVALID_HANDLE_VALUE = -1
THREAD_QUERY_INFORMATION = 0x0040
THREAD_SET_INFORMATION = 0x0020
THREAD_SUSPEND_RESUME = 0x0002
THREAD_HANDLE_RIGHTS = THREAD_SET_INFORMATION | THREAD_SUSPEND_RESUME | THREAD_QUERY_INFORMATION
PROCESS_TERMINATE = 0x0001
PROCESS_QUERY_INFORMATION = 0x0400
SYNCHRONIZE = 0x00100000L
PROCESS_SET_INFORMATION = 0x0200
PROCESS_SET_QUERY_AND_TERMINATE = PROCESS_SET_INFORMATION | PROCESS_TERMINATE | PROCESS_QUERY_INFORMATION | SYNCHRONIZE
ERROR_ALREADY_EXISTS = 183
WAIT_FAILED = 0xFFFFFFFF
WAIT_OBJECT_0 = 0x00000000L
WAIT_ABANDONED = 0x00000080L
CE_FULL_PERMISSIONS = ctypes.c_ulong(0xFFFFFFFF)
NORMAL_PRIORITY_CLASS = ctypes.c_ulong(0x00000020)
HIGH_PRIORITY_CLASS = ctypes.c_ulong(0x00000080)
INFINITE = 0xFFFFFFFF
THREAD_PRIORITY_HIGHEST = 2
THREAD_PRIORITY_ABOVE_NORMAL = 1
THREAD_PRIORITY_NORMAL = 0
PROCESS_BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
PROCESS_NORMAL_PRIORITY_CLASS = 0x00000020
PROCESS_ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000

# How many times to attempt sleeping/resuming thread or proces
# before giving up with failure
ATTEMPT_MAX = 10 

# Which threads should not be put to sleep?
EXCLUDED_THREADS = []

# Key Functions
# Maps Microsoft API calls to more convenient name for internal use
# Also abstracts the linking library for each function for more portability

# Load the Functions that have a common library between desktop and CE
#_suspend_thread = kerneldll.SuspendThread # Puts a thread to sleep
# This workaround is needed to keep the Python Global Interpreter Lock (GIL)
# Normal ctypes CFUNCTYPE or WINFUNCTYPE prototypes will release the GIL
# Which causes the process to infinitely deadlock
# The downside to this method, is that a ValueError Exception is always thrown
_suspend_thread_proto = ctypes.PYFUNCTYPE(DWORD)
def _suspend_thread_err_check(result, func, args):
  return result
_suspend_thread_err = _suspend_thread_proto(("SuspendThread", kerneldll))
_suspend_thread_err.errcheck = _suspend_thread_err_check

def _suspend_thread(handle):
  result = 0
  try:
    result = _suspend_thread_err(handle)
  except ValueError:
    pass
  return result
      
_resume_thread = kerneldll.ResumeThread # Resumes Thread execution
_open_process = kerneldll.OpenProcess # Returns Process Handle
_create_process = kerneldll.CreateProcessW # Launches new process
_set_thread_priority = kerneldll.SetThreadPriority # Sets a threads scheduling priority
_thread_times = kerneldll.GetThreadTimes # Gets CPU time data for a thread

_process_exit_code = kerneldll.GetExitCodeProcess # Gets Process Exit code
_terminate_process = kerneldll.TerminateProcess # Kills a process
_close_handle = kerneldll.CloseHandle # Closes any(?) handle object
_get_last_error = kerneldll.GetLastError # Gets last error number of last error
_wait_for_single_object = kerneldll.WaitForSingleObject # Waits to acquire mutex
_create_mutex = kerneldll.CreateMutexW # Creates a Mutex, Unicode version
_release_mutex = kerneldll.ReleaseMutex # Releases mutex

try:
  _get_tick_count = kerneldll.GetTickCount64 # Try to get the 64 bit variant
except AttributeError: # This means the function does not exist
  _get_tick_count = kerneldll.GetTickCount # Use the 32bit version

_free_disk_space = kerneldll.GetDiskFreeSpaceExW # Determines free disk space

# Load CE Specific function
if MobileCE:
  # Uses kernel, but is slightly different on desktop
  _global_memory_status = kerneldll.GlobalMemoryStatus
  
  # Things using toolhelp
  _create_snapshot = toolhelp.CreateToolhelp32Snapshot # Makes snapshot of threads 
  _close_snapshot = toolhelp.CloseToolhelp32Snapshot # destroys a snapshot 
  _first_thread = toolhelp.Thread32First # Reads from Thread from snapshot
  _next_thread = toolhelp.Thread32Next # Reads next Thread from snapshot
  
  # Things using kernel
  # Windows CE uses thread identifiers and handles interchangably
  # Use internal ce method to handle this
  # _open_thread_ce
  
  # Non-Supported functions:
  # _process_times, there is no tracking of this on a process level
  # _process_memory, CE does not track memory usage
  # _current_thread_id, CE has this defined inline in a header file, so we need to do it
  # These must be handled specifically
  # We override this later
  _current_thread_id = None 
  
  # Heap functions only needed on CE for getting memory info
  _heap_list_first = toolhelp.Heap32ListFirst # Initializes Heap List
  _heap_list_next = toolhelp.Heap32ListNext # Iterates through the heap list
  _heap_first = toolhelp.Heap32First # Initializes Heap Entry
  _heap_next = toolhelp.Heap32Next # Iterates through the Heaps
  
  # Non-officially supported methods
  _get_current_permissions = kerneldll.GetCurrentPermissions
  _set_process_permissions = kerneldll.SetProcPermissions
# Load the Desktop Specific functions
else:
  # These are in the kernel library on the desktop
  _open_thread = kerneldll.OpenThread # Returns Thread Handle
  _create_snapshot = kerneldll.CreateToolhelp32Snapshot # Makes snapshot of threads 
  _first_thread = kerneldll.Thread32First # Reads from Thread from snapshot
  _next_thread = kerneldll.Thread32Next # Reads next Thread from snapshot
  _global_memory_status = kerneldll.GlobalMemoryStatusEx # Gets global memory info
  _current_thread_id = kerneldll.GetCurrentThreadId # Returns the thread_id of the current thread
  
  # These process specific functions are only available on the desktop
  _process_times = kerneldll.GetProcessTimes # Returns data about Process CPU use
  _process_memory = memdll.GetProcessMemoryInfo # Returns data on Process mem use
  
  # This is only available for desktop, sets the process wide priority
  _set_process_priority = kerneldll.SetPriorityClass 
  

# Classes
# Python Class which is converted to a C struct
# It encapsulates Thread Data, and is used in
# Windows Thread calls
class _THREADENTRY32(ctypes.Structure): 
    _fields_ = [('dwSize', DWORD), 
                ('cntUsage', DWORD), 
                ('th32thread_id', DWORD), 
                ('th32OwnerProcessID', DWORD),
                ('tpBasePri', LONG),
                ('tpDeltaPri', LONG),
                ('dwFlags', DWORD)]

# It encapsulates Thread Data, and is used in
# Windows Thread calls, CE Version
class _THREADENTRY32CE(ctypes.Structure): 
    _fields_ = [('dwSize', DWORD), 
                ('cntUsage', DWORD), 
                ('th32thread_id', DWORD), 
                ('th32OwnerProcessID', DWORD),
                ('tpBasePri', LONG),
                ('tpDeltaPri', LONG),
                ('dwFlags', DWORD),
                ('th32AccessKey', DWORD),
                ('th32CurrentProcessID', DWORD)]



# Python Class which is converted to a C struct
# It encapsulates Time data, with a low and high number
# We use it to get Process times (user/system/etc.)
class _FILETIME(ctypes.Structure): 
    _fields_ = [('dwLowDateTime', DWORD), 
                ('dwHighDateTime', DWORD)]



# Python Class which is converted to a C struct
# It encapsulates data about a Processes 
# Memory usage. A pointer to the struct is passed
# to the Windows API
class _PROCESS_MEMORY_COUNTERS(ctypes.Structure): 
    _fields_ = [('cb', DWORD), 
                ('PageFaultCount', DWORD), 
                ('PeakWorkingSetSize', SIZE_T), 
                ('WorkingSetSize', SIZE_T),
                ('QuotaPeakPagedPoolUsage', SIZE_T),
                ('QuotaPagedPoolUsage', SIZE_T),
                ('QuotaPeakNonPagedPoolUsage', SIZE_T),
                ('QuotaNonPagedPoolUsage', SIZE_T),
                ('PagefileUsage', SIZE_T),
                ('PeakPagefileUsage', SIZE_T)]


# Python Class which is converted to a C struct
# It encapsulates data about a heap space
# see http://msdn.microsoft.com/en-us/library/ms683443(VS.85).aspx
class _HEAPENTRY32(ctypes.Structure): 
    _fields_ = [('dwSize', SIZE_T), 
                ('hHandle', HANDLE), 
                ('dwAddress', ULONG_PTR), 
                ('dwBlockSize', SIZE_T),
                ('dwFlags', DWORD),
                ('dwLockCount', DWORD),
                ('dwResvd', DWORD),
                ('th32ProcessID', DWORD),
                ('th32HeapID', ULONG_PTR)]
                
# Python Class which is converted to a C struct
# It encapsulates data about a processes heaps
# see http://msdn.microsoft.com/en-us/library/ms683449(VS.85).aspx
class _HEAPLIST32(ctypes.Structure): 
    _fields_ = [('dwSize', SIZE_T), 
                ('th32ProcessID', DWORD), 
                ('th32HeapID', ULONG_PTR), 
                ('dwFlags', DWORD)]

# Python Class which is converted to a C struct
# It encapsulates data about a newly created process
# see http://msdn.microsoft.com/en-us/library/ms684873(VS.85).aspx
class _PROCESS_INFORMATION(ctypes.Structure): 
    _fields_ = [('hProcess', HANDLE), 
                ('hThread', HANDLE), 
                ('dwProcessId', DWORD), 
                ('dwThreadId', DWORD)]
                 

# Python Class which is converted to a C struct
# It encapsulates data about a Processes 
# after it is created
# see http://msdn.microsoft.com/en-us/library/ms686331(VS.85).aspx
class _STARTUPINFO(ctypes.Structure): 
    _fields_ = [('cb', DWORD), 
                ('lpReserved', LPTSTR), 
                ('lpDesktop', LPTSTR), 
                ('lpTitle', LPTSTR),
                ('dwX', DWORD),
                ('dwY', DWORD),
                ('dwXSize', DWORD),
                ('dwYSize', DWORD),
                ('dwXCountChars', DWORD),
                ('dwYCountChars', DWORD),
                ('dwFillAttribute', DWORD),
                ('dwFlags', DWORD),
                ('wShowWindow', DWORD),
                ('cbReserved2', WORD),
                ('lpReserved2', WORD),
                ('hStdInput', HANDLE),
                ('hStdOutput', HANDLE),
                ('hStdError', HANDLE)]

# Python Class which is converted to a C struct
# It encapsulates data about global memory
# This version is for Windows Desktop, and is not limited to 4 gb of ram
# see http://msdn.microsoft.com/en-us/library/aa366770(VS.85).aspx
class _MEMORYSTATUSEX(ctypes.Structure): 
    _fields_ = [('dwLength', DWORD), 
                ('dwMemoryLoad', DWORD), 
                ('ullTotalPhys', DWORDLONG), 
                ('ullAvailPhys', DWORDLONG),
                ('ullTotalPageFile', DWORDLONG),
                ('ullAvailPageFile', DWORDLONG),
                ('ullTotalVirtual', DWORDLONG),
                ('ullAvailVirtual', DWORDLONG),
                ('ullAvailExtendedVirtual', DWORDLONG)]        
 
# Python Class which is converted to a C struct
# It encapsulates data about global memory
# This version is for WinCE (< 4gb ram)
# see http://msdn.microsoft.com/en-us/library/bb202730.aspx
class _MEMORYSTATUS(ctypes.Structure): 
   _fields_ = [('dwLength', DWORD), 
               ('dwMemoryLoad', DWORD), 
               ('dwTotalPhys', DWORD), 
               ('dwAvailPhys', DWORD),
               ('dwTotalPageFile', DWORD),
               ('dwAvailPageFile', DWORD),
               ('dwTotalVirtual', DWORD),
               ('dwAvailVirtual', DWORD)]          
                                
# Exceptions

class DeadThread(Exception):
  """Gets thrown when a Tread Handle cannot be opened"""
  pass


class DeadProcess(Exception):
  """Gets thrown when a Process Handle cannot be opened. Eventually a DeadThread will get escalated to DeadProcess"""
  pass


class FailedMutex(Exception):
  """Gets thrown when a Mutex cannot be created, opened, or released"""
  pass


# Global variables

# For each Mutex, record the lock count to properly release
_mutex_lock_count = {}
   
# High level functions

# When getProcessTheads is called, it iterates through all the
# system threads, and this global counter stores the thead count
_system_thread_count = 0

# Returns list with the Thread ID of all threads associated with the pid
def get_process_threads(pid):
  """
  <Purpose>
    Many of the Windows functions for altering processes and threads require
    thread-based handles, as opposed to process based, so this function
    gets all of the threads associated with a given process
  
  <Arguments>
    pid:
           The Process Identifier number for which the associated threads should be returned
  
  <Returns>
    Array of Thread Identifiers, these are not thread handles
  """
  global _system_thread_count
  
  # Mobile requires different structuer
  if MobileCE:
    thread_class = _THREADENTRY32CE
  else:
    thread_class = _THREADENTRY32
    
  threads = [] # List object for threads
  current_thread = thread_class() # Current Thread Pointer
  current_thread.dwSize = ctypes.sizeof(thread_class)
  
  # Create Handle to snapshot of all system threads
  handle = _create_snapshot(TH32CS_SNAPTHREAD, 0)
  
  # Check if handle was created successfully
  if handle == INVALID_HANDLE_VALUE:
    _close_handle( handle )
    return []
  
  # Attempt to read snapshot
  if not _first_thread( handle, ctypes.pointer(current_thread)):
    _close_handle( handle )
    return []
  
  # Reset the global counter
  _system_thread_count = 0
  
  # Loop through threads, check for threads associated with the right process
  more_threads = True
  while (more_threads):
    # Increment the global counter
    _system_thread_count += 1
    
    # Check if current thread belongs to the process were looking for
    if current_thread.th32OwnerProcessID == ctypes.c_ulong(pid).value: 
      threads.append(current_thread.th32thread_id)
    more_threads = _next_thread(handle, ctypes.pointer(current_thread))
  
  # Cleanup snapshot
  if MobileCE:
    _close_snapshot(handle)
  _close_handle(handle)
    
  return threads  


def get_system_thread_count():
  """
  <Purpose>
    Returns the number of active threads running on the system.

  <Returns>
    The thread count.
  """
  global _system_thread_count
  
  # Call get_process_threads to update the global counter
  get_process_threads(os.getpid())  # Use our own pid
  
  # Return the global thread count
  return _system_thread_count


# Returns a handle for thread_id  
def get_thread_handle(thread_id):
  """
    <Purpose>
      Returns a thread handle for a given thread identifier. This is useful
      because a thread identified cannot be used directly for most operations.
  
    <Arguments>
      thread_id:
             The Thread Identifier, for which a handle is returned
  
   <Side Effects>
     If running on a mobile CE platform, execution permissions will be elevated.
     close_thread_handle must be called before get_thread_handle is called again,
     or permissions will not be set to their original level.
     
    <Exceptions>
      DeadThread on bad parameters or general error
  
    <Returns>
      Thread Handle
    """
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    handle = _open_thread_ce(thread_id)
  else:
    # Open handle to thread
    handle = _open_thread(THREAD_HANDLE_RIGHTS, 0, thread_id)
  
  # Check for a successful handle
  if handle: 
    return handle
  else: # Raise exception on failure
    raise DeadThread, "Error opening thread handle! thread_id: " + str(thread_id) + " Error Str: " + str(ctypes.WinError())  


# Closes a thread handle
def close_thread_handle(thread_handle):
  """
    <Purpose>
      Closes a given thread handle.
  
    <Arguments>
      ThreadHandle:
             The Thread handle which is closed
    """
    
  # Check if it is CE
  if MobileCE:
    # Opening a thread raises permissions,
    # so we need to revert to default
    _revert_permissions();
  
  # Close thread handle
  _close_handle(thread_handle)
    
    
# Suspend a thread with given thread_id
def suspend_thread(thread_id):
  """
    <Purpose>
      Suspends the execution of a thread.
      Will not execute on currently executing thread.
  
    <Arguments>
      thread_id:
             The thread identifier for the thread to be suspended.
  
    <Exceptions>
      DeadThread on bad parameters or general error.
  
    <Side Effects>
      Will suspend execution of the thread until resumed or terminated.
  
    <Returns>
      True on success, false on failure
  """
  global EXCLUDED_THREADS

  # Check if it is a white listed thread
  if thread_id in EXCLUDED_THREADS:
    return True
      
  # Open handle to thread
  handle = get_thread_handle(thread_id)
  
  # Try to suspend thread, save status of call
  status = _suspend_thread(handle)
  
  # Close thread handle
  close_thread_handle(handle)
  
  # -1 is returned on failure, anything else on success
  # Translate this to True and False
  return (not status == -1)



# Resume a thread with given thread_id
def resume_thread(thread_id):
  """
    <Purpose>
      Resumes the execution of a thread.
  
    <Arguments>
      thread_id:
             The thread identifier for the thread to be resumed
  
    <Exceptions>
      DeadThread on bad parameter or general error.
  
    <Side Effects>
      Will resume execution of a thread.
  
    <Returns>
      True on success, false on failure
    """
    
  # Get thread Handle
  handle = get_thread_handle(thread_id)
  
  # Attempt to resume thread, save status of call
  val = _resume_thread(handle)
  
  # Close Thread Handle
  close_thread_handle(handle)
  
  # -1 is returned on failure, anything else on success
  # Translate this to True and False
  return (not val == -1)



# Suspend a process with given pid
def suspend_process(pid):
  """
  <Purpose>
    Instead of manually getting a list of threads for a process and individually
    suspending each, this function will do the work transparently.
  
  <Arguments>
    pid:
      The Process Identifier number to be suspended.
  
  <Side Effects>
    Suspends the given process indefinitely.
  
  <Returns>
    True on success, false on failure
  """

  # Get List of threads related to Process
  threads = get_process_threads(pid)

  # Suspend each thread serially
  for t in threads:
    sleep = False # Loop until thread sleeps
    attempt = 0 # Number of times we've attempted to suspend thread
    while not sleep:
      if (attempt > ATTEMPT_MAX):
        return False
      attempt = attempt + 1
      try:
        sleep = suspend_thread(t)
      except DeadThread:
        # If the thread is dead, lets just say its asleep and continue
        sleep = True

  return True



# Resume a process with given pid
def resume_process(pid):
  """
  <Purpose>
    Instead of manually resuming each thread in a process, this functions
    handles that transparently.
  
  <Arguments>
    pid:
      The Process Identifier to be resumed.
  
  <Side Effects>
    Resumes thread execution
  
  <Returns>
    True on success, false on failure
  """
  
  # Get list of threads related to Process
  threads = get_process_threads(pid)
  
  # Resume each thread
  for t in threads:
    wake = False # Loop until thread wakes up
    attempt = 0 # Number of attempts to resume thread
    while not wake: 
      if (attempt > ATTEMPT_MAX):
        return False
      attempt = attempt + 1
      try:
        wake = resume_thread(t)
      except DeadThread:
        # If the thread is dead, its hard to wake it up, so contiue
        wake = True
  return True



# Suspends a process and restarts after a given time interval
def timeout_process(pid, stime):
  """
  <Purpose>
    Calls suspend_process and resume_process with a specified period of sleeping.
  
  <Arguments>
    pid:
      The process identifier to timeout execution.
    stime:
      The time period in seconds to timeout execution.
  
  <Exceptions>
    DeadProcess if there is a critical problem sleeping or resuming a thread.
    
  <Side Effects>
    Timeouts the execution of the process for specified interval.
    The timeout period is blocking, and will cause a general timeout in the
    calling thread.
    
  <Returns>
    True of success, false on failure.
  """
  if stime==0: # Don't waste time
    return True
  try:
    # Attempt to suspend process, return immediately on failure
    if suspend_process(pid):
      
      # Sleep for user defined period
      time.sleep (stime)
  
      # Attempt to resume process and return whether that succeeded
      return resume_process(pid)
    else:
      return False
  except DeadThread: # Escalate DeadThread to DeadProcess, because that is the underlying cause
    raise DeadProcess, "Failed to sleep or resume a thread!"


# Sets the current threads priority level
def set_current_thread_priority(priority=THREAD_PRIORITY_NORMAL,exclude=True):
  """
  <Purpose>
    Sets the priority level of the currently executing thread.
    
  <Arguments>
    Thread priority level. Must be a predefined constant.
    See THREAD_PRIORITY_NORMAL, THREAD_PRIORITY_ABOVE_NORMAL and THREAD_PRIORITY_HIGHEST
    
    exclude: If true, the thread will not be put to sleep when compensating for CPU use.

  <Exceptions>
    See get_thread_handle
  
  <Returns>
    True on success, False on failure.
  """
  global EXCLUDED_THREADS

  # Get thread identifier
  thread_id = _current_thread_id()
  
  # Check if we should exclude this thread
  if exclude:
    # Use a list copy, so that our swap doesn't cause any issues
    # if the CPU scheduler is already running
    new_list = EXCLUDED_THREADS[:]
    new_list.append(thread_id)
    EXCLUDED_THREADS = new_list
     
  # Open handle to thread
  handle = get_thread_handle(thread_id)
  
  # Try to change the priority
  status = _set_thread_priority(handle, priority)
  
  # Close thread handle
  close_thread_handle(handle)
  
  # Return the status of this call
  if status == 0:
    return False
  else:
    return True

# Gets a process handle
def get_process_handle(pid):
  """
  <Purpose>
    Get a process handle for a specified process identifier
  
  <Arguments>
    pid:
      The process identifier for which a handle is returned.
  
  <Exceptions>
    DeadProcess on bad parameter or general error.
  
  <Returns>
    Process handle
  """
  
  # Get handle to process
  handle = _open_process(PROCESS_SET_QUERY_AND_TERMINATE, 0, pid)
  
  # Check if we successfully got a handle
  if handle:
    return handle
  else: # Raise exception on failure
    raise DeadProcess, "Error opening process handle! Process ID: " + str(pid) + " Error Str: " + str(ctypes.WinError())


# Launches a new process
def launch_process(application,cmdline = None, priority = NORMAL_PRIORITY_CLASS):
  """
  <Purpose>
    Launches a new process.
  
  <Arguments>
    application:
      The path to the application to be started
    cmdline:
      The command line parameters that are to be used
    priority
      The priority of the process. See NORMAL_PRIORITY_CLASS and HIGH_PRIORITY_CLASS
      
  <Side Effects>
    A new process is created
  
  <Returns>
    Process ID on success, None on failure.
  """
  # Create struct to hold process info
  process_info = _PROCESS_INFORMATION()
  process_info_addr = ctypes.pointer(process_info)
  
  # Determine what is the cmdline Parameter
  if not (cmdline == None):
    cmdline_param = unicode(cmdline)
  else:
    cmdline_param = None
  
  # Adjust for CE
  if MobileCE:
    # Not Supported on CE
    priority = 0
    window_info_addr = 0
    # Always use absolute path
    application = unicode(os.path.abspath(application))
  else:
    # For some reason, Windows Desktop uses the first part of the second parameter as the
    # Application... This is documented on MSDN under CreateProcess in the user comments
    # Create struct to hold window info
    window_info = _STARTUPINFO()
    window_info_addr = ctypes.pointer(window_info)
    cmdline_param = unicode(application) + " " + cmdline_param
    application = None
  
  # Lauch process, and save status
  status = _create_process(
    application, 
    cmdline_param,
    None,
    None,
    False,
    priority,
    None,
    None,
    window_info_addr,
    process_info_addr)
  
  # Did we succeed?
  if status:
    # Close handles that we don't need
    _close_handle(process_info.hProcess)
    _close_handle(process_info.hThread)
    
    # Return pid
    return process_info.dwProcessId
  else:
    return None

# Helper function to launch a python script with some parameters
def launch_python_script(script, params=""):
  """
  <Purpose>
    Launches a python script with parameters
  
  <Arguments>
    script:
      The python script to be started. This should be an absolute path (and quoted if it contains spaces).
    params:
      A string command line parameter for the script
      
  <Side Effects>
    A new process is created
  
  <Returns>
    Process ID on success, None on failure.
  """
  
  # Get all repy constants
  import repy_constants
  
  # Create python command line string
  # Use absolute path for compatibility
  cmd = repy_constants.PYTHON_DEFAULT_FLAGS + " " + script + " " + params
  
  # Launch process and store return value
  retval = launch_process(repy_constants.PATH_PYTHON_INSTALL,cmd)
  
  return retval


# Sets the current process priority level
def set_current_process_priority(priority=PROCESS_NORMAL_PRIORITY_CLASS):
  """
  <Purpose>
    Sets the priority level of the currently executing process.

  <Arguments>
    Process priority level. Must be a predefined constant.
    See PROCESS_NORMAL_PRIORITY_CLASS, PROCESS_BELOW_NORMAL_PRIORITY_CLASS and PROCESS_ABOVE_NORMAL_PRIORITY_CLASS

  <Exceptions>
    See get_process_handle

  <Returns>
    True on success, False on failure.
  """
  # This is not supported, just return True
  if MobileCE:
    return True
    
  # Get our pid
  pid = os.getpid()
  
  # Get process handle
  handle = get_process_handle(pid)

  # Try to change the priority
  status = _set_process_priority(handle, priority)

  # Close Process Handle
  _close_handle(handle)

  # Return the status of this call
  if status == 0:
    return False
  else:
    return True
    
# Kill a process with specified pid
def kill_process(pid):
  """
  <Purpose>
    Terminates a process.
  
  <Arguments>
    pid:
      The process identifier to be killed.
  
  <Exceptions>
    DeadProcess on bad parameter or general error.
  
  <Side Effects>
    Terminates the process
  
  <Returns>
    True on success, false on failure.
  """
  
  try:
    # Get process handle
    handle = get_process_handle(pid)
  except DeadProcess: # This is okay, since we're trying to kill it anyways
    return True
  
  dead = False # Status of Process we're trying to kill
  attempt = 0 # Attempt Number
  
  # Keep hackin' away at it
  while not dead:
    if (attempt > ATTEMPT_MAX):
      raise DeadProcess, "Failed to kill process! Process ID: " + str(pid) + " Error Str: " + str(ctypes.WinError())
  
    # Increment attempt count
    attempt = attempt + 1 
  
    # Attempt to terminate process
    # 0 is return code for failure, convert it to True/False
    dead = not 0 == _terminate_process(handle, 0)
  
  # Close Process Handle
  _close_handle(handle)
  
  return True


# Get info about a processes CPU time, normalized to seconds
def get_process_cpu_time(pid):
  """
  <Purpose>
    See process_times

  <Arguments>
    See process_times

  <Exceptions>
    See process_times

  <Returns>
    The amount of CPU time used by the kernel and user in seconds.
  """
  # Get the times
  times = process_times(pid)

  # Add kernel and user time together...   It's in units of 100ns so divide
  # by 10,000,000
  total_time = (times['KernelTime'] + times['UserTime'] ) / 10000000.0

  return total_time


# Get information about a process CPU use times
def process_times(pid):
  """
  <Purpose>
    Gets information about a processes CPU time utilization.
    Because Windows CE does not keep track of this information at a process level,
    if a thread terminates (belonging to the pid), then it is possible for the 
    KernelTime and UserTime to be lower than they were previously.
  
  <Arguments>
    pid:
      The process identifier about which the information is returned
  
  <Exceptions>
    DeadProcess on bad parameter or general error.
  
  <Returns>
    Dictionary with the following indices:
    CreationTime: the time at which the process was created
    KernelTime: the execution time of the process in the kernel
    UserTime: the time spent executing user code
  """
  
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    return _process_times_ce(pid)
  
  # Open process handle
  handle = get_process_handle(pid)
  
  # Create all the structures needed to make API Call
  creation_time = _FILETIME()
  exit_time = _FILETIME()
  kernel_time = _FILETIME()
  user_time = _FILETIME()
  
  # Pass all the structures as pointers into process_times
  _process_times(handle, ctypes.pointer(creation_time), ctypes.pointer(exit_time), ctypes.pointer(kernel_time), ctypes.pointer(user_time))
  
  # Close Process Handle
  _close_handle(handle)
  
  # Extract the values from the structures, and return then in a dictionary
  return {"CreationTime":creation_time.dwLowDateTime,"KernelTime":kernel_time.dwLowDateTime,"UserTime":user_time.dwLowDateTime}


# Get the CPU time of the current thread
def get_current_thread_cpu_time():
  """
  <Purpose>
    Gets the total CPU time for the currently executing thread.

  <Exceptions>
    An Exception will be raised if the underlying system call fails.

  <Returns>
    A floating amount of time in seconds.
  """
  # Get our thread identifier
  thread_id = _current_thread_id()

  # Open handle to thread
  handle = get_thread_handle(thread_id)

  # Create all the structures needed to make API Call
  creation_time = _FILETIME()
  exit_time = _FILETIME()
  kernel_time = _FILETIME()
  user_time = _FILETIME()
  
  # Pass all the structures as pointers into threadTimes
  res = _thread_times(handle, ctypes.pointer(creation_time), ctypes.pointer(exit_time), ctypes.pointer(kernel_time), ctypes.pointer(user_time))

  # Close thread Handle
  close_thread_handle(handle)
    
  # Sum up the cpu time
  time_sum = kernel_time.dwLowDateTime
  time_sum += user_time.dwLowDateTime

  # Units are 100 ns, so divide by 10M
  time_sum /= 10000000.0
  
  # Check the result, error if result is 0
  if res == 0:
    raise Exception,(res, _get_last_error(), "Error getting thread CPU time! Error Str: " + str(ctypes.WinError()))

  # Return the time
  return time_sum


# Wait for a process to exit
def wait_for_process(pid):
  """
  <Purpose>
    Blocks execution until the specified Process finishes execution.
  
  <Arguments>
    pid:
      The process identifier to wait for
  """
  try:
    # Get process handle
    handle = get_process_handle(pid)
  except DeadProcess:
    # Process is likely dead, so just return
    return

  # Pass in code as a pointer to store the output
  status = _wait_for_single_object(handle, INFINITE)
  if status != WAIT_OBJECT_0:
    raise EnvironmentError, "Failed to wait for Process!"
  
  # Close the Process Handle
  _close_handle(handle)
  

# Get the exit code of a process
def process_exit_code(pid):
  """
  <Purpose>
    Get the exit code of a process
  
  <Arguments>
    pid:
      The process identifier for which the exit code is returned.
  
  <Returns>
    The process exit code, or 0 on failure.
  """
  
  try:
    # Get process handle
    handle = get_process_handle(pid)
  except DeadProcess:
    # Process is likely dead, so give anything other than 259
    return 0
 
  # Store the code, 0 by default
  code = ctypes.c_int(0)
  
  # Pass in code as a pointer to store the output
  _process_exit_code(handle, ctypes.pointer(code))
  
  # Close the Process Handle
  _close_handle(handle)
  return code.value



# Get information on process memory use
def process_memory_info(pid):
  """
  <Purpose>
    Get information about a processes memory usage.
    On Windows CE, all of the dictionary indices will return the same
    value. This is due to the imprecision of CE's memory tracking,
    and all of the indices are only returned for compatibility reasons.
  
  <Arguments>
    pid:
      The process identifier for which memory info is returned
  
  <Exceptions>
    DeadProcess on bad parameters or general error.
  
  <Returns>
    Dictionary with memory data associated with description.
  """
  
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    return _process_memory_info_ce(pid)
    
  # Open process Handle
  handle = get_process_handle(pid)
  
  # Define structure to hold memory data
  meminfo = _PROCESS_MEMORY_COUNTERS()
  
  # Pass pointer to meminfo to processMemory to store the output
  _process_memory(handle, ctypes.pointer(meminfo), ctypes.sizeof(_PROCESS_MEMORY_COUNTERS))
  
  # Close Process Handle
  _close_handle(handle)
  
  # Extract data from meminfo structure and return as python
  # dictionary structure
  return {'PageFaultCount':meminfo.PageFaultCount,
          'PeakWorkingSetSize':meminfo.PeakWorkingSetSize,
          'WorkingSetSize':meminfo.WorkingSetSize,
          'QuotaPeakPagedPoolUsage':meminfo.QuotaPeakPagedPoolUsage,
          'QuotaPagedPoolUsage':meminfo.QuotaPagedPoolUsage,
          'QuotaPeakNonPagedPoolUsage':meminfo.QuotaPeakNonPagedPoolUsage,
          'QuotaNonPagedPoolUsage':meminfo.QuotaNonPagedPoolUsage,
          'PagefileUsage':meminfo.PagefileUsage,
          'PeakPagefileUsage':meminfo.PeakPagefileUsage}  


# INFO: Pertaining to _mutex_lock_count:
# With Mutexes, each time they are acquired, they must be released the same number of times.
# For this reason we account for the number of times a mutex has been acquired, and release_mutex
# will call the underlying release enough that the mutex will actually be released.
# The entry for _mutex_lock_count is initialized in create_mutex, incremented in acquire_mutex
# and zero'd out in release_mutex
          

# Creates and returns a handle to a Mutex
def create_mutex(name):
  """
  <Purpose>
    Creates and returns a handle to a mutex
  
  <Arguments>
    name:
      The name of the mutex to be created
  
  <Exceptions>
    FailedMutex on bad parameters or failure to create mutex.
  
  <Side Effects>
    Creates a global mutex and retains control.
  
  <Returns>
    handle to the mutex.
  """
  # Attempt to create Mutex
  handle = _create_mutex(None, 0, unicode(name))
  
  # Check for a successful handle
  if not handle == False: 
    # Try to acquire the mutex for 200 milliseconds, check if it is abandoned
    val = _wait_for_single_object(handle, 200)
    
    # If the mutex is signaled, or abandoned release it
    # If it was abandoned, it will become normal now
    if (val == WAIT_OBJECT_0) or (val == WAIT_ABANDONED):
      _release_mutex(handle)
    
    # Initialize the lock count to 0, since it has not been signaled yet.
    _mutex_lock_count[handle] = 0
    return handle
  else: # Raise exception on failure
    raise FailedMutex, (_get_last_error(), "Error creating mutex! Mutex name: " + str(name) + " Error Str: " + str(ctypes.WinError()))



# Waits for specified interval to acquire Mutex
# time should be in milliseconds
def acquire_mutex(handle, time):
  """
  <Purpose>
    Acquires exclusive control of a mutex
  
  <Arguments>
    handle:
      Handle to a mutex object
    time:
      the time to wait in milliseconds to get control of the mutex
  
  <Side Effects>
    If successful, the calling thread had exclusive control of the mutex
  
  <Returns>
    True if the mutex is acquired, false otherwise.
  """
  
  # Wait up to time to acquire lock, fail otherwise
  val = _wait_for_single_object(handle, time)
  
  # Update lock count
  _mutex_lock_count[handle] += 1
  
  # WAIT_OBJECT_0 is returned on success, other on failure
  return (val == WAIT_OBJECT_0) or (val == WAIT_ABANDONED)



# Releases a mutex
def release_mutex(handle):
  """
  <Purpose>
    Releases control of a mutex
  
  <Arguments>
    handle:
      Handle to the mutex object to be release
  
  <Exceptions>
    FailedMutex if a general error is occurred when releasing the mutex.
    This is not raised if the mutex is not owned, and a release is attempted.
  
  <Side Effects>
    If controlled previous to calling, then control will be given up
  
  <Returns>
    None.
  """
  
  # Get the lock count
  count = _mutex_lock_count[handle]
  
  # 0 out the count
  _mutex_lock_count[handle] = 0
  
  # Attempt to release a Mutex
  for i in range(0, count):
    try:
      release = _release_mutex(handle)
  
      # 0 return value means failure
      if release == 0:
        raise FailedMutex, (_get_last_error(), "Error releasing mutex! Mutex id: " + str(handle) + " Error Str: " + str(ctypes.WinError()))
    except FailedMutex, e:
      if (e[0] == 288): # 288 is for non-owned mutex, which is ok
        pass
      else:
        raise

def exists_outgoing_network_socket(localip, localport, remoteip, remoteport):
  """
  <Purpose>
    Determines if there exists a network socket with the specified unique tuple.
    Assumes TCP.
    * Not supported on Windows Mobile.

  <Arguments>
    localip: The IP address of the local socket
    localport: The port of the local socket
    remoteip:  The IP of the remote host
    remoteport: The port of the remote host
    
  <Returns>
    A Tuple, indicating the existence and state of the socket. E.g. (Exists (True/False), State (String or None))
  """
  if MobileCE:
    return False 
  
  # This only works if all are not of the None type
  if not (localip and localport and remoteip and remoteport):
    return (False, None)

  # Construct search strings, add a space so port 8 wont match 80
  localsocket = localip+":"+str(localport)+" "
  remotesocket = remoteip+":"+str(remoteport)+" "

  # Launch up a shell, get the feedback
  netstat_process = portable_popen.Popen(["netstat", "-an"])

  netstat_output, _ = netstat_process.communicate()

  target_lines = textops.textops_grep(localsocket, \
      textops.textops_rawtexttolines(netstat_output, linedelimiter="\r\n"))
  target_lines = textops.textops_grep(remotesocket, target_lines)

  target_lines = textops.textops_grep("tcp ", target_lines, case_sensitive=False)
  
  # Check each line, to make sure the local socket comes before the remote socket
  # Since we are just using find, the "order" is not imposed, so if the remote socket
  # is first that implies it is an inbound connection
  if len(target_lines) > 0:
    # Check each entry
    for line in target_lines:
      # Check the indexes for the local and remote socket, make sure local
      # comes first  
      local_index = line.find(localsocket)
      remote_index = line.find(remotesocket)
      if local_index <= remote_index and local_index != -1:
        # Replace tabs with spaces, explode on spaces
        parts = line.replace("\t","").strip("\r\n").split()
        # Get the state
        socket_state = parts[-1]
      
        return (True, socket_state)
 
    return (False, None)

  # If there were no entries, then there is no socket!
  else:
    return (False, None)

def exists_listening_network_socket(ip, port, tcp):
  """
  <Purpose>
    Determines if there exists a network socket with the specified ip and port which is the LISTEN state.
    *Note: Not currently supported on Windows CE. It will always return False on this platform.
  <Arguments>
    ip: The IP address of the listening socket
    port: The port of the listening socket
    tcp: Is the socket of TCP type, else UDP

  <Returns>
    True or False.
  """
  if MobileCE:
    return False

  # This only works if both are not of the None type
  if not (ip and port):
    return False

  # UDP connections are stateless, so for TCP check for the LISTEN state
  # and for UDP, just check that there exists a UDP port
  if tcp:
    find = ["tcp", "LISTEN"]
  else:
    find = ["udp"]

  # Launch up a shell, get the feed back
  netstat_process = portable_popen.Popen(["netstat", "-an"])

  netstat_output, _ = netstat_process.communicate()

  target_lines = textops.textops_grep(ip+':'+str(port)+' ', \
      textops.textops_rawtexttolines(netstat_output, linedelimiter="\r\n"))

  for term in find:   # Add additional grep's
    target_lines = textops.textops_grep(term, target_lines, case_sensitive=False)

  # Convert to an integer
  num = len(target_lines)

  return (num > 0)


def _fetch_ipconfig_infomation():
  """
  <Purpose>
    Fetch's the information from ipconfig and stores it in a useful format.
    * Not Supported on Windows Mobile.
  <Returns>
    A dictionary object.
  """
  
  # Launch up a shell, get the feedback
  process = portable_popen.Popen(["ipconfig", "/all"])

  # Get the output
  outputdata = process.stdout.readlines()
  
  # Close the pipe
  process.stdout.close()
  
  # Stores the info
  info_dict = {}
  
  # Store the current container
  current_container = None
  
  # Process each line
  for line in outputdata:
    # Strip unwanted characters
    line = line.strip("\r\n")
    
    # Check if this line is blank, skip it
    if line.strip() == "":
      continue
    
    # This is a top-level line if it does not start with a space
    if not line.startswith(" "):
      # Do some cleanup
      line = line.strip(" :")
      
      # Check if this exists in the top return dictionary, if not add it
      if line not in info_dict:
        info_dict[line] = {}
      
      # Set the current container
      current_container = line
    
    # Otherwise, this line just contains some information
    else:
      # Check if we are in a container
      if not current_container:
        continue
      
      # Cleanup
      line = line.strip()
      line = line.replace(". ", "")
      
      # Explode on the colon
      (key, value) = line.split(":",1)
      
      # More cleanup
      key = key.strip()
      value = value.strip()
      
      # Store this
      info_dict[current_container][key] = value
  
  # Return everything
  return info_dict    


def get_available_interfaces():
  """
  <Purpose>
    Returns a list of available network interfaces.
    * Not Supported on Windows Mobile.
  <Returns>
    An array of string interfaces
  """
  if MobileCE:
    return []
    
  # Get the information from ipconfig
  ipconfig_data = _fetch_ipconfig_infomation()
  
  # Get the keys
  ipconfig_data_keys = ipconfig_data.keys()
  
  # Remove the Generic "Windows IP Configuration"
  if "Windows IP Configuration" in ipconfig_data_keys:
    index = ipconfig_data_keys.index("Windows IP Configuration")
    del ipconfig_data_keys[index]
    
  # Return the keys
  return ipconfig_data_keys


def get_interface_ip_addresses(interfaceName):
  """
  <Purpose>
    Returns the IP address associated with the interface.
    * Not Supported on Windows Mobile.
  <Arguments>
    interfaceName: The string name of the interface, e.g. eth0

  <Returns>
    A list of IP addresses associated with the interface.
  """
  if MobileCE:
    return []
    
  # Get the information from ipconfig
  ipconfig_data = _fetch_ipconfig_infomation()
  
  # Check if the interface exists
  if interfaceName not in ipconfig_data:
    return []
  
  # Check if there is an IP address
  if "IP Address" in ipconfig_data[interfaceName]:
    return [ipconfig_data[interfaceName]["IP Address"]]
  
  return []


# Windows CE Stuff
# Internal function, not public

# Get information about a process CPU use times
# Windows CE does not have a GetProcessTimes function, so we will emulate it
def _process_times_ce(pid):
  # Get List of threads related to Process
  threads = get_process_threads(pid)
  
  # Create all the structures needed to make API Call
  creation_time = _FILETIME()
  exit_time = _FILETIME()
  kernel_time = _FILETIME()
  user_time = _FILETIME()
  
  # Create counters for each category
  # Only adds the "low date time" (see _FILETIME()), since thats what we return
  creation_time_sum = 0
  exit_time_sum = 0 # We don't return this, but we keep it anyways
  kernel_time_sum = 0
  user_time_sum = 0
  
  # Get the process times for each thread
  for t in threads:
    # Open handle to thread
    handle = get_thread_handle(t)
  
    # Pass all the structures as pointers into threadTimes
    _thread_times(handle, ctypes.pointer(creation_time), ctypes.pointer(exit_time), ctypes.pointer(kernel_time), ctypes.pointer(user_time))
  
    # Close thread Handle
    close_thread_handle(handle)
    
    # Update all the counters
    creation_time_sum += creation_time.dwLowDateTime
    exit_time_sum += exit_time.dwLowDateTime
    kernel_time_sum += kernel_time.dwLowDateTime
    user_time_sum += user_time.dwLowDateTime
  
  # Return the proper values in a dictionaries
  return {"CreationTime":creation_time_sum,"KernelTime":kernel_time_sum,"UserTime":user_time_sum}



# Windows CE does not have a GetProcessMemoryInfo function,
# so memory usage may be more inaccurate
# We iterate over all of the process's heap spaces, and tally up the
# total size, and return that value for all types of usage
def _process_memory_info_ce(pid):
  heap_size = 0 # Keep track of heap size
  heap_list = _HEAPLIST32() # List of heaps
  heap_entry = _HEAPENTRY32() # Current Heap entry
  
  heap_list.dwSize = ctypes.sizeof(_HEAPLIST32)
  heap_entry.dwSize = ctypes.sizeof(_HEAPENTRY32)
  
  # Create Handle to snapshot of all system threads
  handle = _create_snapshot(TH32CS_SNAPHEAPLIST, pid)
  
  # Check if handle was created successfully
  if handle == INVALID_HANDLE_VALUE:
    return {}
  
  # Attempt to read snapshot
  if not _heap_list_first( handle, ctypes.pointer(heap_list)):
    _close_snapshot(handle)
    _close_handle(handle)
    return {}
  
  # Loop through threads, check for threads associated with the right process
  more_heaps = True
  while (more_heaps):
    
    # Check if there is a heap entry here
    if _heap_first(handle, ctypes.pointer(heap_entry), heap_list.th32ProcessID, heap_list.th32HeapID):
      
      # Loop through available heaps
      more_entries = True
      while more_entries:
        # Increment the total heap size by the current heap size
        heap_size += heap_entry.dwBlockSize
        
        heap_entry.dwSize = ctypes.sizeof(_HEAPENTRY32)
        more_entries = _heap_next(handle, ctypes.pointer(heap_entry)) # Go to next Heap entry
    
    heap_list.dwSize = ctypes.sizeof(_HEAPLIST32)
    more_heaps = _heap_list_next(handle, ctypes.pointer(heap_list)) # Go to next Heap List
  
  # Cleanup snapshot
  _close_snapshot(handle)
  _close_handle(handle)
  
  # Since we only have one value, return that for all different possible sets
  return {'PageFaultCount':heap_size,
          'PeakWorkingSetSize':heap_size,
          'WorkingSetSize':heap_size,
          'QuotaPeakPagedPoolUsage':heap_size,
          'QuotaPagedPoolUsage':heap_size,
          'QuotaPeakNonPagedPoolUsage':heap_size,
          'QuotaNonPagedPoolUsage':heap_size,
          'PagefileUsage':heap_size,
          'PeakPagefileUsage':heap_size}  


# Windows CE does not have a separate handle for threads
# Since handles and identifiers are interoperable, just return the ID
# Set process permissions higher or else this will fail
def _open_thread_ce(thread_id):
	# Save original permissions
	global _original_permissions_ce
	_original_permissions_ce = _get_process_permissions()
	
	# Get full system control
	_set_current_proc_permissions(CE_FULL_PERMISSIONS)
	
	return thread_id

# Sets the permission level of the current process
def _set_current_proc_permissions(permission):
	_set_process_permissions(permission)

# Global variable to store permissions
_original_permissions_ce = None

# Returns the permission level of the current process
def _get_process_permissions():
	return _get_current_permissions()

# Reverts permissions to original
def _revert_permissions():
	global _original_permissions_ce
	if not _original_permissions_ce == None:
		_set_current_proc_permissions(_original_permissions_ce)

# Returns ID of current thread on WinCE
def _current_thread_id_ce():
  # We need to check this specific memory address
  loc = ctypes.cast(0xFFFFC808, ctypes.POINTER(ctypes.c_ulong))
  # Then follow the pointer to get the value there
  return loc.contents.value

# Over ride this for CE
if MobileCE:
  _current_thread_id = _current_thread_id_ce
  
## Resource Determining Functions
# For number of CPU's check the %NUMBER_OF_PROCESSORS% Environment variable 


# Determines available and used disk space
def disk_util(directory):
  """"
  <Purpose>
    Gets information about disk utilization, and free space.
  
  <Arguments>
    directory:
      The directory to be queried. This can be a folder, or a drive root.
      If set to None, then the current directory will be used.
  
  <Exceptions>
    EnvironmentError on bad parameter.
  
  <Returns>
    Dictionary with the following indices:
    bytesAvailable: The number of bytes available to the current user
    total_bytes: The total number of bytes
    freeBytes: The total number of free bytes
  """  
  # Define values that need to be passed to the function
  bytes_free = ULARGE_INTEGER(0)
  total_bytes = ULARGE_INTEGER(0)
  total_free_bytes = ULARGE_INTEGER(0)
  
  # Allow for a Null parameter
  dirchk = None
  if not directory == None:
    dirchk = unicode(directory)
  
  status = _free_disk_space(dirchk, ctypes.pointer(bytes_free), ctypes.pointer(total_bytes), ctypes.pointer(total_free_bytes))
    
  # Check if we succeded
  if status == 0:
    raise EnvironmentError("Failed to determine free disk space: Directory: "+directory)
  
  return {"bytesAvailable":bytes_free.value,"total_bytes":total_bytes.value,"freeBytes":total_free_bytes.value}

# Get global memory information
def global_memory_info():
  """"
  <Purpose>
    Gets information about memory utilization
  
  <Exceptions>
    EnvironmentError on general error.
  
  <Returns>
    Dictionary with the following indices:
    load: The percentage of memory in use
    totalPhysical: The total amount of physical memory
    availablePhysical: The total free amount of physical memory
    totalPageFile: The current size of the committed memory limit, in bytes. This is physical memory plus the size of the page file, minus a small overhead.
    availablePageFile: The maximum amount of memory the current process can commit, in bytes.
    totalVirtual: The size of the user-mode portion of the virtual address space of the calling process, in bytes
    availableVirtual: The amount of unreserved and uncommitted memory currently in the user-mode portion of the virtual address space of the calling process, in bytes.
  """
  # Check if it is CE
  if MobileCE:
    # Use the CE specific function
    return _global_memory_info_ce()
    
  # Initialize the data structure
  mem_info = _MEMORYSTATUSEX() # Memory usage ints
  mem_info.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
  
  # Make the call, save the status
  status = _global_memory_status(ctypes.pointer(mem_info))
 
  # Check if we succeded
  if status == 0:
    raise EnvironmentError("Failed to get global memory info!")

  # Return Dictionary
  return {"load":mem_info.dwMemoryLoad,
  "totalPhysical":mem_info.ullTotalPhys,
  "availablePhysical":mem_info.ullAvailPhys,
  "totalPageFile":mem_info.ullTotalPageFile,
  "availablePageFile":mem_info.ullAvailPageFile,
  "totalVirtual":mem_info.ullTotalVirtual,
  "availableVirtual":mem_info.ullAvailVirtual}
    
def _global_memory_info_ce():
  # Initialize the data structure
  mem_info = _MEMORYSTATUS() # Memory usage ints
  mem_info.dwLength = ctypes.sizeof(_MEMORYSTATUS)
  
  # Make the call
  _global_memory_status(ctypes.pointer(mem_info))
  
  # Return Dictionary
  return {"load":mem_info.dwMemoryLoad,
  "totalPhysical":mem_info.dwTotalPhys,
  "availablePhysical":mem_info.dwAvailPhys,
  "totalPageFile":mem_info.dwTotalPageFile,
  "availablePageFile":mem_info.dwAvailPageFile,
  "totalVirtual":mem_info.dwTotalVirtual,
  "availableVirtual":mem_info.dwAvailVirtual}
  
  
  

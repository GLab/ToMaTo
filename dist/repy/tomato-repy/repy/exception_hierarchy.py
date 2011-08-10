"""

This file contains the exception hierarchy for repy. This allows repy modules
to import a single file to have access to all the defined exceptions.

"""

# This list maintains the exceptions that are exported to the user
# If the exception is not listed here, the user cannot explicitly
# catch that error.
_EXPORTED_EXCEPTIONS = ["RepyException",
                        "RepyArgumentError",
                        "CodeUnsafeError",
                        "ContextUnsafeError",
                        "ResourceUsageError",
                        "ResourceExhaustedError",
                        "ResourceForbiddenError",
                        "FileError",
                        "FileNotFoundError",
                        "FileInUseError",
                        "SeekPastEndOfFileError",
                        "FileClosedError",
                        "LockDoubleReleaseError",
                        "NetworkError",
                        "NetworkAddressError",
                        "AlreadyListeningError",
                        "DuplicateTupleError",
                        "CleanupInProgressError",
                        "InternetConnectivityError",
                        "AddressBindingError",
                        "ConnectionRefusedError",
                        "LocalIPChanged",
                        "SocketClosedLocal",
                        "SocketClosedRemote",
                        "SocketWouldBlockError",
                        "TimeoutError",
                       ]



##### High-level, generic exceptions

class InternalRepyError (Exception):
  """
  All Fatal Repy Exceptions derive from this exception.
  This error should never make it to the user-code.
  """
  pass

class RepyException (Exception):
  """All Repy Exceptions derive from this exception."""
  pass

class RepyArgumentError (RepyException):
  """
  This Exception indicates that an argument was provided
  to a repy API as an in-appropriate type or value.
  """
  pass

class TimeoutError (RepyException):
  """
  This generic error indicates that a timeout has
  occurred.
  """
  pass


##### Code Safety Exceptions

class CodeUnsafeError (RepyException):
  """
  This indicates that the static code analysis failed due to
  unsafe constructions or a syntax error.
  """
  pass

class ContextUnsafeError (RepyException):
  """
  This indicates that the context provided to evaluate() was
  unsafe, and could not be converted into a SafeDict.
  """
  pass


##### Resource Related Exceptions

class ResourceUsageError (RepyException):
  """
  All Resource Usage Exceptions derive from this exception.
  """
  pass

class ResourceExhaustedError (ResourceUsageError):
  """
  This Exception indicates that a resource has been
  Exhausted, and that the operation has failed for that
  reason.
  """
  pass

class ResourceForbiddenError (ResourceUsageError):
  """
  This Exception indicates that a specified resource
  is forbidden, and cannot be used.
  """
  pass


##### File Related Exceptions

class FileError (RepyException):
  """All File-Related Exceptions derive from this exception."""
  pass

class FileNotFoundError (FileError):
  """
  This Exception indicates that a file which does not exist was
  used as an argument to a function expecting a real file.
  """
  pass

class FileInUseError (FileError):
  """
  This Exception indicates that a file which is in use was
  used as an argument to a function expecting the file to
  be un-used.
  """
  pass

class SeekPastEndOfFileError (FileError):
  """
  This Exception indicates that an attempt was made to
  seek past the end of a file.
  """
  pass

class FileClosedError (FileError):
  """
  This Exception indicates that the file is closed,
  and that the operation is therfor invalid.
  """
  pass


##### Safety exceptions from safe.py

class SafeException(RepyException):
    """Base class for Safe Exceptions"""
    def __init__(self,*value):
        self.value = str(value)
    def __str__(self):
        return self.value

class CheckNodeException(SafeException):
    """AST Node class is not in the whitelist."""
    pass

class CheckStrException(SafeException):
    """A string in the AST looks insecure."""
    pass

class RunBuiltinException(SafeException):
    """During the run a non-whitelisted builtin was called."""
    pass


##### Lock related exceptions

class LockDoubleReleaseError(RepyException):
  """
  This exception indicates that an attempt was made to
  release a lock that was not acquired.
  """
  pass


##### Network exceptions

class NetworkError (RepyException):
  """
  This exception parent-classes all of the networking exceptions.
  """
  pass

class NetworkAddressError (NetworkError):
  """
  This exception is raised when a DNS lookup fails.
  """
  pass

class AlreadyListeningError (NetworkError):
  """
  This exception indicates that there is an existing
  listen on the local IP / Port pair that are specified.
  """
  pass

class DuplicateTupleError (NetworkError):
  """
  This exception indicates that there is another socket
  which has a duplicate tuple (local ip, local port, remote ip, remote port)
  """
  pass

class CleanupInProgressError (NetworkError):
  """
  This exception indicates that the socket is still
  being cleaned up by the operating system, and that
  it is unavailable.
  """
  pass

class InternetConnectivityError (NetworkError):
  """
  This exception is raised when there is no route to an IP passed to
  sendmessage or openconnection.
  """
  pass

class AddressBindingError (NetworkError):
  """
  This exception is raised when binding to an ip and port fails.
  """
  pass

class ConnectionRefusedError (NetworkError):
  """
  This exception is raised when a TCP connection request is refused.
  """
  pass

class LocalIPChanged (NetworkError):
  """
  This exception indicates that the local IP has changed.
  """
  pass

class SocketClosedLocal (NetworkError):
  """
  This indicates that the socket was closed locally.
  """
  pass

class SocketClosedRemote (NetworkError):
  """
  This indicates that the socket was closed on the remote end.
  """
  pass

class SocketWouldBlockError (NetworkError):
  """
  This indicates that the socket operation would have blocked.
  """
  pass

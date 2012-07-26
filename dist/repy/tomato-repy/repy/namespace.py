"""
<Program>
  namespace.py

<Started>
  September 2009

<Author>
  Justin Samuel

<Purpose>
  This is the namespace layer that ensures separation of the namespaces of
  untrusted code and our code. It provides a single public function to be
  used to setup the context in which untrusted code is exec'd (that is, the
  context that is seen as the __builtins__ by the untrusted code).
  
  The general idea is that any function or object that is available between
  trusted and untrusted code gets wrapped in a function or object that does
  validation when the function or object is used. In general, if user code
  is not calling any functions improperly, neither the user code nor our
  trusted code should ever notice that the objects and functions they are
  dealing with have been wrapped by this namespace layer.
  
  All of our own api functions are wrapped in NamespaceAPIFunctionWrapper
  objects whose wrapped_function() method is mapped in to the untrusted
  code's context. When called, the wrapped_function() method performs
  argument, return value, and exception validation as well as additional
  wrapping and unwrapping, as needed, that is specific to the function
  that was ultimately being called. If the return value or raised exceptions
  are not considered acceptable, a NamespaceViolationError is raised. If the
  arguments are not acceptable, a TypeError is raised.
  
  Note that callback functions that are passed from untrusted user code
  to trusted code are also wrapped (these are arguments to wrapped API
  functions, so we get to wrap them before calling the underlying function).
  The reason we wrap these is so that we can intercept calls to the callback
  functions and wrap arguments passed to them, making sure that handles
  passed as arguments to the callbacks get wrapped before user code sees them.
  
  The function and object wrappers have been defined based on the API as
  documented at https://seattle.cs.washington.edu/wiki/RepyLibrary
  
  Example of using this module (this is really the only way to use the module):
  
    import namespace  
    usercontext = {}
    namespace.wrap_and_insert_api_functions(usercontext)
    safe.safe_exec(usercode, usercontext)
  
  The above code will result in the dict usercontext being populated with keys
  that are the names of the functions available to the untrusted code (such as
  'open') and the values are the wrapped versions of the actual functions to be
  called (such as 'emulfile.emulated_open').
  
  Note that some functions wrapped by this module lose some python argument
  flexibility. Wrapped functions can generally only have keyword args in
  situations where the arguments are optional. Using keyword arguments for
  required args may not be supported, depending on the implementation of the
  specific argument check/wrapping/unwrapping helper functions for that
  particular wrapped function. If this becomes a problem, it can be dealt with
  by complicating some of the argument checking/wrapping/unwrapping code in
  this module to make the checking functions more flexible in how they take
  their arguments.
  
  Implementation details:
  
  The majority of the code in this module is made up of helper functions to do
  argument checking, etc. for specific wrapped functions.
  
  The most important parts to look at in this module for maintenance and
  auditing are the following:
  
    USERCONTEXT_WRAPPER_INFO
    
      The USERCONTEXT_WRAPPER_INFO is a dictionary that defines the API
      functions that are wrapped and inserted into the user context when
      wrap_and_insert_api_functions() is called.
    
    FILE_OBJECT_WRAPPER_INFO
    LOCK_OBJECT_WRAPPER_INFO
    TCP_SOCKET_OBJECT_WRAPPER_INFO
    TCP_SERVER_SOCKET_OBJECT_WRAPPER_INFO
    UDP_SERVER_SOCKET_OBJECT_WRAPPER_INFO
    VIRTUAL_NAMESPACE_OBJECT_WRAPPER_INFO
    
      The above four dictionaries define the methods available on the wrapped
      objects that are returned by wrapped functions. Additionally, timerhandle
      and commhandle objects are wrapped but instances of these do not have any
      public methods and so no *_WRAPPER_INFO dictionaries are defined for them.
  
    NamespaceObjectWrapper
    NamespaceAPIFunctionWrapper
  
      The above two classes are the only two types of objects that will be
      allowed in untrusted code. In fact, instances of NamespaceAPIFunctionWrapper
      are never actually allowed in untrusted code. Rather, each function that
      is wrapped has a single NamespaceAPIFunctionWrapper instance created
      when wrap_and_insert_api_functions() is called and what is actually made
      available to the untrusted code is the wrapped_function() method of each
      of the corresponding NamespaceAPIFunctionWrapper instances.
      
    NamespaceInternalError
    
      If this error is raised anywhere (along with any other unexpected exceptions),
      it should result in termination of the running program (see the except blocks
      in NamespaceAPIFunctionWrapper.wrapped_function).
"""

import types

# To check if objects are thread.LockType objects.
import thread

import emulcomm
import emulfile
import emulmisc
import emultimer
import nonportable
import safe # Used to get SafeDict
import tracebackrepy
import virtual_namespace

from exception_hierarchy import *

# Save a copy of a few functions not available at runtime.
_saved_getattr = getattr
_saved_callable = callable
_saved_hash = hash
_saved_id = id


##############################################################################
# Public functions of this module to be called from the outside.
##############################################################################

def wrap_and_insert_api_functions(usercontext):
  """
  This is the main public function in this module at the current time. It will
  wrap each function in the usercontext dict in a wrapper with custom
  restrictions for that specific function. These custom restrictions are
  defined in the dictionary USERCONTEXT_WRAPPER_INFO.
  """

  _init_namespace()

  for function_name in USERCONTEXT_WRAPPER_INFO:
    function_info = USERCONTEXT_WRAPPER_INFO[function_name]
    wrapperobj = NamespaceAPIFunctionWrapper(function_info)
    usercontext[function_name] = wrapperobj.wrapped_function





##############################################################################
# Helper functions for the above public function.
##############################################################################

# Whether _init_namespace() has already been called.
initialized = False

def _init_namespace():
  """
  Performs one-time initialization of the namespace module.
  """
  global initialized
  if not initialized:
    initialized = True
    _prepare_wrapped_functions_for_object_wrappers()





# These dictionaries will ultimately contain keys whose names are allowed
# methods that can be called on the objects and values which are the wrapped
# versions of the functions which are exposed to users. If a dictionary
# is empty, it means no methods can be called on a wrapped object of that type.
file_object_wrapped_functions_dict = {}
lock_object_wrapped_functions_dict = {}
tcp_socket_object_wrapped_functions_dict = {}
tcp_server_socket_object_wrapped_functions_dict = {}
udp_server_socket_object_wrapped_functions_dict = {}
virtual_namespace_object_wrapped_functions_dict = {}

def _prepare_wrapped_functions_for_object_wrappers():
  """
  Wraps functions that will be used whenever a wrapped object is created.
  After this has been called, the dictionaries such as
  file_object_wrapped_functions_dict have been populated and therefore can be
  used by functions such as wrap_socket_obj().
  """
  objects_tuples = [(FILE_OBJECT_WRAPPER_INFO, file_object_wrapped_functions_dict),
                    (LOCK_OBJECT_WRAPPER_INFO, lock_object_wrapped_functions_dict),
                    (TCP_SOCKET_OBJECT_WRAPPER_INFO, tcp_socket_object_wrapped_functions_dict),
                    (TCP_SERVER_SOCKET_OBJECT_WRAPPER_INFO, tcp_server_socket_object_wrapped_functions_dict),
                    (UDP_SERVER_SOCKET_OBJECT_WRAPPER_INFO, udp_server_socket_object_wrapped_functions_dict),
                    (VIRTUAL_NAMESPACE_OBJECT_WRAPPER_INFO, virtual_namespace_object_wrapped_functions_dict)]

  for description_dict, wrapped_func_dict in objects_tuples:
    for function_name in description_dict:
      function_info = description_dict[function_name]
      wrapperobj = NamespaceAPIFunctionWrapper(function_info, is_method=True)
      wrapped_func_dict[function_name] = wrapperobj.wrapped_function





##############################################################################
# Helper functions.
##############################################################################

def _handle_internalerror(message, exitcode):
  """
  Terminate the running program. This is used rather than
  tracebackrepy.handle_internalerror directly in order to make testing easier."""
  tracebackrepy.handle_internalerror(message, exitcode)





def _is_in(obj, sequence):
  """
  A helper function to do identity ("is") checks instead of equality ("==")
  when using X in [A, B, C] type constructs. So you would write:
    if _is_in(type(foo), [int, long]):
  instead of:
    if type(foo) in [int, long]:
  """
  for item in sequence:
    if obj is item:
      return True
  return False





##############################################################################
# Constants that define which functions should be wrapped and how. These are
# used by the functions wrap_and_insert_api_functions() and
# wrap_builtin_functions().
##############################################################################

class BaseProcessor(object):
  """Base type for ValueProcess and ObjectProcessor."""





class ValueProcessor(BaseProcessor):
  """
  This is for simple/builtin types and combinations of them. Basically,
  anything that needs to be copied when used as an argument or return
  value and doesn't need to be wrapped or unwrapped as it passes through
  the namespace layer.
  """

  def check(self):
    raise NotImplementedError

  def copy(self, val):
    return _copy(val)



class ObjectProcessor(BaseProcessor):
  """
  This is for for anything that needs to be wrapped or unwrapped (not copied)
  as it passes through the namespace layer.
  """

  def check(self):
    raise NotImplementedError

  def wrap(self, val):
    raise NotImplementedError

  def unwrap(self, val):
    return val._wrapped__object





class Str(ValueProcessor):
  """Allows str or unicode."""

  def __init__(self, maxlen=None, minlen=None):
    self.maxlen = maxlen
    self.minlen = minlen



  def check(self, val):
    if not _is_in(type(val), [str, unicode]):
      raise RepyArgumentError("Invalid type %s" % type(val))

    if self.maxlen is not None:
      if len(val) > self.maxlen:
        raise RepyArgumentError("Max string length is %s" % self.maxlen)

    if self.minlen is not None:
      if len(val) < self.minlen:
        raise RepyArgumentError("Min string length is %s" % self.minlen)





class Int(ValueProcessor):
  """Allows int or long."""

  def __init__(self, min=0):
    self.min = min



  def check(self, val):
    if not _is_in(type(val), [int, long]):
      raise RepyArgumentError("Invalid type %s" % type(val))

    if val < self.min:
      raise RepyArgumentError("Min value is %s." % self.min)


class NoneOrInt(ValueProcessor):
  """Allows a NoneType or an int. This doesn't enforce min limit on the
  ints."""

  def check(self, val):
    if val is not None and not _is_in(type(val), [int, long]):
      raise RepyArgumentError("Invalid type %s" % type(val))






class StrOrInt(ValueProcessor):
  """Allows a string or int. This doesn't enforce max/min/length limits on the
  strings and ints."""

  def check(self, val):
    if not _is_in(type(val), [int, long, str, unicode]):
      raise RepyArgumentError("Invalid type %s" % type(val))





class Float(ValueProcessor):
  """Allows float, int, or long."""

  def __init__(self, allow_neg=False):
    self.allow_neg = allow_neg



  def check(self, val):
    if not _is_in(type(val), [int, long, float]):
      raise RepyArgumentError("Invalid type %s" % type(val))

    if not self.allow_neg:
      if val < 0:
        raise RepyArgumentError("Must be non-negative.")





class Bool(ValueProcessor):
  """Allows bool."""

  def check(self, val):
    if type(val) is not bool:
      raise RepyArgumentError("Invalid type %s" % type(val))





class ListOfStr(ValueProcessor):
  """Allows lists of strings. This doesn't enforce max/min/length limits on the
  strings and ints."""

  def check(self, val):
    if not type(val) is list:
      raise RepyArgumentError("Invalid type %s" % type(val))

    for item in val:
      Str().check(item)





class List(ValueProcessor):
  """Allows lists. The list may contain anything."""
  
  def check(self, val):
    if not type(val) is list:
      raise RepyArgumentError("Invalid type %s" % type(val))





class Dict(ValueProcessor):
  """Allows dictionaries. The dictionaries may contain anything."""

  def check(self, val):
    if not type(val) is dict:
      raise RepyArgumentError("Invalid type %s" % type(val))





class DictOfStrOrInt(ValueProcessor):
  """
  Allows a tuple that contains dictionaries that only contain string keys
  and str or int values. This doesn't enforce max/min/length limits on the
  strings and ints.
  """

  def check(self, val):
    if not type(val) is dict:
      raise RepyArgumentError("Invalid type %s" % type(val))

    for key, value in val.items():
      Str().check(key)
      StrOrInt().check(value)





class Func(ValueProcessor):
  """Allows a user-defined function object."""

  def check(self, val):
    if not _is_in(type(val), [types.FunctionType, types.LambdaType, types.MethodType]):
      raise RepyArgumentError("Invalid type %s" % type(val))





class NonCopiedVarArgs(ValueProcessor):
  """Allows any number of arguments. This must be the last arg listed. """

  def check(self, val):
    pass



  def copy(self, val):
    return val





class File(ObjectProcessor):
  """Allows File objects."""

  def check(self, val):
    if not isinstance(val, emulfile.emulated_file):
      raise RepyArgumentError("Invalid type %s" % type(val))



  def wrap(self, val):
    return NamespaceObjectWrapper("file", val, file_object_wrapped_functions_dict)





class Lock(ObjectProcessor):
  """Allows Lock objects."""

  def check(self, val):
    if not isinstance(val, emulmisc.emulated_lock):
      raise RepyArgumentError("Invalid type %s" % type(val))



  def wrap(self, val):
    return NamespaceObjectWrapper("lock", val, lock_object_wrapped_functions_dict)





class UDPServerSocket(ObjectProcessor):
  """Allows UDPServerSocket objects."""

  def check(self, val):
    if not isinstance(val, emulcomm.UDPServerSocket):
      raise RepyArgumentError("Invalid type %s" % type(val))



  def wrap(self, val):
    return NamespaceObjectWrapper("socket", val, udp_server_socket_object_wrapped_functions_dict)





class TCPServerSocket(ObjectProcessor):
  """Allows TCPServerSocket objects."""

  def check(self, val):
    if not isinstance(val, emulcomm.TCPServerSocket):
      raise RepyArgumentError("Invalid type %s" % type(val))



  def wrap(self, val):
    return NamespaceObjectWrapper("socket", val, tcp_server_socket_object_wrapped_functions_dict)





class TCPSocket(ObjectProcessor):
  """Allows TCPSocket objects."""

  def check(self, val):
    if not isinstance(val, emulcomm.EmulatedSocket):
      raise RepyArgumentError("Invalid type %s" % type(val))



  def wrap(self, val):
    return NamespaceObjectWrapper("socket", val, tcp_socket_object_wrapped_functions_dict)





class VirtualNamespace(ObjectProcessor):
  """Allows VirtualNamespace objects."""

  def check(self, val):
    if not isinstance(val, virtual_namespace.VirtualNamespace):
      raise RepyArgumentError("Invalid type %s" % type(val))



  def wrap(self, val):
    return NamespaceObjectWrapper("VirtualNamespace", val,
                                  virtual_namespace_object_wrapped_functions_dict)





class SafeDict(ObjectProcessor):
  """Allows SafeDict objects."""

  # TODO: provide a copy function that won't actually copy so that
  # references are maintained.
  def check(self, val):
    if not isinstance(val, safe.SafeDict):
      raise RepyArgumentError("Invalid type %s" % type(val))





class DictOrSafeDict(ObjectProcessor):
  """Allows SafeDict objects or regular dict objects."""

  # TODO: provide a copy function that won't actually copy so that
  # references are maintained.
  def check(self, val):
    if type(val) is not dict:
      SafeDict(val).check()





# These are the functions in the user's name space excluding the builtins we
# allow. Each function is a key in the dictionary. Each value is a dictionary
# that defines the functions to be used by the wrapper when a call is
# performed. It is the same dictionary that is passed as a constructor to
# the NamespaceAPIFunctionWrapper class to create the actual wrappers.
# The public function wrap_and_insert_api_functions() uses this dictionary as
# the basis for what is populated in the user context. Anything function
# defined here will be wrapped and made available to untrusted user code.
USERCONTEXT_WRAPPER_INFO = {
  'gethostbyname' :
      {'func' : emulcomm.gethostbyname,
       'args' : [Str()],
       'return' : Str()},
  'getmyip' :
      {'func' : emulcomm.getmyip,
       'args' : [],
       'return' : Str()},
  'sendmessage' :
      {'func' : emulcomm.sendmessage,
       'args' : [Str(), Int(), Str(), Str(), Int()],
       'return' : Int()},
  'listenformessage' :
      {'func' : emulcomm.listenformessage,
       'args' : [Str(), Int()],
       'return' : UDPServerSocket()},
  'openconnection' :
      {'func' : emulcomm.openconnection,
       'args' : [Str(), Int(), Str(), Int(), Float()],
#      'raise' : [AddressBindingError, PortRestrictedError, PortInUseError,
#                 ConnectionRefusedError, TimeoutError, RepyArgumentError],
       'return' : TCPSocket()},
  'listenforconnection' :
      {'func' : emulcomm.listenforconnection,
       'args' : [Str(), Int()],
       'return' : TCPServerSocket()},
  'openfile' :
      {'func' : emulfile.emulated_open,
       'args' : [Str(maxlen=120), Bool()],
       'return' : File()},
  'listfiles' :
      {'func' : emulfile.listfiles,
       'args' : [],
       'return' : ListOfStr()},
  'removefile' :
      {'func' : emulfile.removefile,
       'args' : [Str(maxlen=120)],
       'return' : None},
  'exitall' :
      {'func' : emulmisc.exitall,
       'args' : [],
       'return' : None},
  'createlock' :
      {'func' : emulmisc.createlock,
       'args' : [],
       'return' : Lock()},
  'getruntime' :
      {'func' : emulmisc.getruntime,
       'args' : [],
       'return' : Float()},
  'randombytes' :
      {'func' : emulmisc.randombytes,
       'args' : [],
       'return' : Str(maxlen=1024, minlen=1024)},
  'createthread' :
      {'func' : emultimer.createthread,
       'args' : [Func()],
       'return' : None},
  'sleep' :
      {'func' : emultimer.sleep,
       'args' : [Float()],
       'return' : None},
  'log' :
      {'func' : emulmisc.log,
       'args' : [NonCopiedVarArgs()],
       'return' : None},
  'getthreadname' :
      {'func' : emulmisc.getthreadname,
       'args' : [],
       'return' : Str()},
  'createvirtualnamespace' :
      {'func' : virtual_namespace.createvirtualnamespace,
       'args' : [Str(), Str()],
       'return' : VirtualNamespace()},
  'getresources' :
      {'func' : nonportable.get_resources,
       'args' : [],
       'return' : (Dict(), Dict(), List())},
}

FILE_OBJECT_WRAPPER_INFO = {
  'close' :
      {'func' : emulfile.emulated_file.close,
       'args' : [],
       'return' : None},
  'readat' :
      {'func' : emulfile.emulated_file.readat,
       'args' : [NoneOrInt(), Int(min=0)],
       'return' : Str()},
  'writeat' :
      {'func' : emulfile.emulated_file.writeat,
       'args' : [Str(), Int(min=0)],
       'return' : None},
}

TCP_SOCKET_OBJECT_WRAPPER_INFO = {
  'close' :
      {'func' : emulcomm.EmulatedSocket.close,
       'args' : [],
       'return' : Bool()},
  'recv' :
      {'func' : emulcomm.EmulatedSocket.recv,
       'args' : [Int(min=1)],
       'return' : Str()},
  'send' :
      {'func' : emulcomm.EmulatedSocket.send,
       'args' : [Str()],
       'return' : Int(min=0)},
}

# TODO: Figure out which real object should be wrapped. It doesn't appear
# to be implemented yet as there is no "getconnection" in the repy_v2 source.
TCP_SERVER_SOCKET_OBJECT_WRAPPER_INFO = {
  'close' :
      {'func' : emulcomm.TCPServerSocket.close,
       'args' : [],
       'return' : Bool()},
  'getconnection' :
      {'func' : emulcomm.TCPServerSocket.getconnection,
       'args' : [],
       'return' : (Str(), Int(), TCPSocket())},
}

UDP_SERVER_SOCKET_OBJECT_WRAPPER_INFO = {
  'close' :
      {'func' : emulcomm.UDPServerSocket.close,
       'args' : [],
       'return' : Bool()},
  'getmessage' :
      {'func' : emulcomm.UDPServerSocket.getmessage,
       'args' : [],
       'return' : (Str(), Int(), Str())},
}

LOCK_OBJECT_WRAPPER_INFO = {
  'acquire' :
      # A string for the target_func indicates a function by this name on the
      # instance rather is what should be wrapped.
      {'func' : 'acquire',
       'args' : [Bool()],
       'return' : Bool()},
  'release' :
      # A string for the target_func indicates a function by this name on the
      # instance rather is what should be wrapped.
      {'func' : 'release',
       'args' : [],
       'return' : None},
}

VIRTUAL_NAMESPACE_OBJECT_WRAPPER_INFO = {
  # Evaluate must take a dict or SafeDict, and can
  # only return a SafeDict. We must _not_ copy the
  # dict since that will screw up the references in the dict.
  'evaluate' :
      {'func' : 'evaluate',
       'args' : [DictOrSafeDict()],
       'return' : SafeDict()},
}


##############################################################################
# The classes we define from which actual wrappers are instantiated.
##############################################################################

def _copy(obj, objectmap=None):
  """
  <Purpose>
    Create a deep copy of an object without using the python 'copy' module.
    Using copy.deepcopy() doesn't work because builtins like id and hasattr
    aren't available when this is called.
  <Arguments>
    obj
      The object to make a deep copy of.
    objectmap
      A mapping between original objects and the corresponding copy. This is
      used to handle circular references.
  <Exceptions>
    TypeError
      If an object is encountered that we don't know how to make a copy of.
    NamespaceViolationError
      If an unexpected error occurs while copying. This isn't the greatest
      solution, but in general the idea is we just need to abort the wrapped
      function call.
  <Side Effects>
    A new reference is created to every non-simple type of object. That is,
    everything except objects of type str, unicode, int, etc.
  <Returns>
    The deep copy of obj with circular/recursive references preserved.
  """
  try:
    # If this is a top-level call to _copy, create a new objectmap for use
    # by recursive calls to _copy.
    if objectmap is None:
      objectmap = {}
    # If this is a circular reference, use the copy we already made.
    elif _saved_id(obj) in objectmap:
      return objectmap[_saved_id(obj)]

    # types.InstanceType is included because the user can provide an instance
    # of a class of their own in the list of callback args to settimer.
    if _is_in(type(obj), [str, unicode, int, long, float, complex, bool, frozenset,
                          types.NoneType, types.FunctionType, types.LambdaType,
                          types.MethodType, types.InstanceType]):
      return obj

    elif type(obj) is list:
      temp_list = []
      # Need to save this in the objectmap before recursing because lists
      # might have circular references.
      objectmap[_saved_id(obj)] = temp_list

      for item in obj:
        temp_list.append(_copy(item, objectmap))

      return temp_list

    elif type(obj) is tuple:
      temp_list = []

      for item in obj:
        temp_list.append(_copy(item, objectmap))

      # I'm not 100% confident on my reasoning here, so feel free to point
      # out where I'm wrong: There's no way for a tuple to directly contain
      # a circular reference to itself. Instead, it has to contain, for
      # example, a dict which has the same tuple as a value. In that
      # situation, we can avoid infinite recursion and properly maintain
      # circular references in our copies by checking the objectmap right
      # after we do the copy of each item in the tuple. The existence of the
      # dictionary would keep the recursion from being infinite because those
      # are properly handled. That just leaves making sure we end up with
      # only one copy of the tuple. We do that here by checking to see if we
      # just made a copy as a result of copying the items above. If so, we
      # return the one that's already been made.
      if _saved_id(obj) in objectmap:
        return objectmap[_saved_id(obj)]

      retval = tuple(temp_list)
      objectmap[_saved_id(obj)] = retval
      return retval

    elif type(obj) is set:
      temp_list = []
      # We can't just store this list object in the objectmap because it isn't
      # a set yet. If it's possible to have a set contain a reference to
      # itself, this could result in infinite recursion. However, sets can
      # only contain hashable items so I believe this can't happen.

      for item in obj:
        temp_list.append(_copy(item, objectmap))

      retval = set(temp_list)
      objectmap[_saved_id(obj)] = retval
      return retval

    elif type(obj) is dict:
      temp_dict = {}
      # Need to save this in the objectmap before recursing because dicts
      # might have circular references.
      objectmap[_saved_id(obj)] = temp_dict

      for key, value in obj.items():
        temp_key = _copy(key, objectmap)
        temp_dict[temp_key] = _copy(value, objectmap)

      return temp_dict

    # We don't copy certain objects. This is because copying an emulated file
    # object, for example, will cause the destructor of the original one to
    # be invoked, which will close the actual underlying file. As the object
    # is wrapped and the client does not have access to it, it's safe to not
    # wrap it.
    elif isinstance(obj, (NamespaceObjectWrapper, emulfile.emulated_file,
                          emulcomm.EmulatedSocket, emulcomm.TCPServerSocket,
                          emulcomm.UDPServerSocket, thread.LockType,
                          virtual_namespace.VirtualNamespace)):
      return obj

    else:
      raise TypeError("_copy is not implemented for objects of type " + str(type(obj)))

  except Exception, e:
    raise NamespaceInternalError("_copy failed on " + str(obj) + " with message " + str(e))





class NamespaceInternalError(Exception):
  """Something went wrong and we should terminate."""





class NamespaceObjectWrapper(object):
  """
  Instances of this class are used to wrap handles and objects returned by
  api functions to the user code.
  
  The methods that can be called on these instances are mostly limited to
  what is in the allowed_functions_dict passed to the constructor. The
  exception is that a simple __repr__() is defined as well as an __iter__()
  and next(). However, instances won't really be iterable unless a next()
  method is defined in the allowed_functions_dict.
  """

  def __init__(self, wrapped_type_name, wrapped_object, allowed_functions_dict):
    """
    <Purpose>
      Constructor
    <Arguments>
      self
      wrapped_type_name
        The name (a string) of what type of wrapped object. For example,
        this could be "timerhandle".
      wrapped_object
        The actual object to be wrapped.
      allowed_functions_dict
        A dictionary of the allowed methods that can be called on the object.
        The keys should be the names of the methods, the values are the
        wrapped functions that will be called.
    """
    # Only one underscore at the front so python doesn't do its own mangling
    # of the name. We're not trying to keep this private in the private class
    # variable sense of python where nothing is really private, instead we just
    # want a double-underscore in there as extra protection against untrusted
    # code being able to access the values.
    self._wrapped__type_name = wrapped_type_name
    self._wrapped__object = wrapped_object
    self._wrapped__allowed_functions_dict = allowed_functions_dict



  def __getattr__(self, name):
    """
    When a method is called on an instance, we look for the method in the
    allowed_functions_dict that was provided to the constructor. If there
    is such a method in there, we return a function that will properly
    invoke the method with the correct 'self' as the first argument.
    """
    if name in self._wrapped__allowed_functions_dict:
      wrapped_func = self._wrapped__allowed_functions_dict[name]

      def __do_func_call(*args, **kwargs):
        return wrapped_func(self._wrapped__object, *args, **kwargs)

      return __do_func_call

    else:
      # This is the standard way of handling "it doesn't exist as far as we
      # are concerned" in __getattr__() methods.
      raise AttributeError, name



  def __iter__(self):
    """
    We provide __iter__() as part of the class rather than through __getattr__
    because python won't look for the attribute in the object to determine if
    the object is iterable, instead it will look directly at the class the
    object is an instance of. See the docstring for next() for more info.
    """
    return self



  def next(self):
    """
    We provide next() as part of the class rather than through __getattr__
    because python won't look for the attribute in the object to determine if
    the object is iterable, instead it will look directly at the class the
    object is an instance of. We don't want everything that is wrapped to
    be considered iterable, though, so we return a TypeError if this gets
    called but there isn't a wrapped next() method.
    """
    if "next" in self._wrapped__allowed_functions_dict:
      return self._wrapped__allowed_functions_dict["next"](self._wrapped__object)

    raise TypeError("You tried to iterate a non-iterator of type " + str(type(self._wrapped__object)))



  def __repr__(self):
    return "<Namespace wrapped " + self._wrapped__type_name + ": " + repr(self._wrapped__object) + ">"



  def __hash__(self):
    return _saved_hash(self._wrapped__object)



  def __eq__(self, other):
    """In addition to __hash__, this is necessary for use as dictionary keys."""
    # We could either assume "other" is a wrapped object and try to compare
    # its wrapped object against this wrapped object, or we could just compare
    # the hashes of each. If we try to unwrap the other object, it means you
    # couldn't compare a wrapped object to an unwrapped one.
    return _saved_hash(self) == _saved_hash(other)



  def __ne__(self, other):
    """
    It's good for consistency to define __ne__ if one is defining __eq__,
    though this is not needed for using objects as dictionary keys.
    """
    return _saved_hash(self) != _saved_hash(other)




class NamespaceAPIFunctionWrapper(object):
  """
  Instances of this class exist solely to provide function wrapping. This is
  done by creating an instance of the class and then making available the
  instance's wrapped_function() method to any code that should only be allowed
  to call the wrapped version of the function.
  """

  def __init__(self, func_dict, is_method=False):
    """
    <Purpose>
      Constructor.
    <Arguments>
      self
      func_dict
        A dictionary whose with the following keys whose values are the
        corresponding funcion:
          func (required) -- a function or a string of the name
            of the method on the underlying object.
          args (required)
          return (required)
      is_method -- if this is an object's method being wrapped
            rather than a regular function.
    <Exceptions>
      None
    <Side Effects>
      None
    <Returns>
      None
    """

    # Required in func_dict.
    self.__func = func_dict["func"]
    self.__args = func_dict["args"]
    self.__return = func_dict["return"]
    self.__is_method = is_method

    # Make sure that the __target_func really is a function or a string
    # indicating a function by that name on the underlying object should
    # be called.
    if not _saved_callable(self.__func) and type(self.__func) is not str:
      raise TypeError("The func was neither callable nor a string when " +
                      "constructing a namespace-wrapped function. The object " +
                      "used for target_func was: " + repr(self.__func))

    if type(self.__func) is str:
      self.__func_name = self.__func
    else:
      self.__func_name = self.__func.__name__



  def _process_args(self, args):
    args_to_return = []

    for index in range(len(args)):
      # Armon: If there are more arguments than there are type specifications
      # and we are using NonCopiedVarArgs, then check against that.
      if index >= len(self.__args) and isinstance(self.__args[-1], NonCopiedVarArgs):
        arg_type = self.__args[-1]
      else:
        arg_type = self.__args[index]

      # We only copy simple types, which means we only copy ValueProcessor not
      # ObjectProcessor arguments.
      if isinstance(arg_type, ValueProcessor):
        temparg = arg_type.copy(args[index])
      elif isinstance(arg_type, ObjectProcessor):
        temparg = arg_type.unwrap(args[index])
      else:
        raise NamespaceInternalError("Unknown argument expectation.")

      arg_type.check(temparg)

      args_to_return.append(temparg)

    return args_to_return



  def _process_retval_helper(self, processor, retval):
    try:
      if isinstance(processor, ValueProcessor):
        tempretval = processor.copy(retval)
        processor.check(tempretval)
      elif isinstance(processor, ObjectProcessor):
        processor.check(retval)
        tempretval = processor.wrap(retval)
      elif processor is None:
        if retval is not None:
          raise InternalRepyError("Expected None but wasn't.")
        tempretval = None
      else:
        raise InternalRepyError("Unknown retval expectation.")
      return tempretval

    except RepyArgumentError, err:
      raise InternalRepyError("Invalid retval type: %s" % err)



  def _process_retval(self, retval):

    try:
      # Allow the return value to be a tuple of processors.
      if type(retval) is tuple:
        if len(retval) != len(self.__return):
          raise InternalRepyError("Returned tuple of wrong size: %s" % str(retval))
        tempretval = []
        for index in range(len(retval)):
          tempitem = self._process_retval_helper(self.__return[index], retval[index])
          tempretval.append(tempitem)
        tempretval = tuple(tempretval)
      else:
        tempretval = self._process_retval_helper(self.__return, retval)

    except Exception, e:
      raise InternalRepyError(
          "Function '" + self.__func_name + "' returned with unallowed return type " +
          str(type(retval)) + " : " + str(e))


    return tempretval



  def wrapped_function(self, *args, **kwargs):
    """
    <Purpose>
      Act as the function that is wrapped but perform all required sanitization
      and checking of data that goes into and comes out of the underlying
      function.
    <Arguments>
      self
      *args
      **kwargs
        The arguments to the underlying function.
    <Exceptions>
      NamespaceViolationError
        If some aspect of the arguments or function call is not allowed.
      Anything else that the underlying function may raise.
    <Side Effects>
      Anything that the underyling function may do.
    <Returns>
      Anything that the underlying function may return.
    """
    try:
      # We don't allow keyword args.
      if kwargs:
        raise RepyArgumentError("Keyword arguments not allowed when calling %s." %
                                self.__func_name)

      if self.__is_method:
        # This is a method of an object instance rather than a standalone function.
        # The "self" argument will be passed implicitly by python in some cases, so
        # we remove it from the args we check. For the others, we'll add it back in
        # after the check.
        args_to_check = args[1:]
      else:
        args_to_check = args

      if len(args_to_check) != len(self.__args):
        if not self.__args or not isinstance(self.__args[-1:][0], NonCopiedVarArgs):
          raise RepyArgumentError("Wrong number of arguments (%s) when calling %s." %
                                  (len(args_to_check), self.__func_name))

      args_copy = self._process_args(args_to_check)

      args_to_use = None

      # If it's a string rather than a function, then this is our convention
      # for indicating that we want to wrap the function of this particular
      # object. We use this if the function to wrap isn't available without
      # having the object around, such as with real lock objects.
      if type(self.__func) is str:
        func_to_call = _saved_getattr(args[0], self.__func)
        args_to_use = args_copy
      else:
        func_to_call = self.__func
        if self.__is_method:
          # Sanity check the object we're adding back in as the "self" argument.
          if not isinstance(args[0], (NamespaceObjectWrapper, emulfile.emulated_file,
                                      emulcomm.EmulatedSocket, emulcomm.TCPServerSocket,
                                      emulcomm.UDPServerSocket, thread.LockType,
                                      virtual_namespace.VirtualNamespace)):
            raise NamespaceInternalError("Wrong type for 'self' argument.")
          # If it's a method but the function was not provided as a string, we
          # actually do have to add the first argument back in. Yes, this whole
          # area of code is ugly.
          args_to_use = [args[0]] + args_copy
        else:
          args_to_use = args_copy
      
      retval = func_to_call(*args_to_use)

      return self._process_retval(retval)

    except RepyException:
      # TODO: this should be changed to RepyError along with all references to
      # RepyException in the rest of the repy code.
      # We allow any RepyError to continue up to the client code.
      raise

    except:
      # Any other exception is unexpected and thus is a programming error on
      # our side, so we terminate.
      _handle_internalerror("Unexpected exception from within Repy API", 843)

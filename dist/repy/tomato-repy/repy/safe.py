"""An attempt at creating a safe_exec for python.

This file is public domain and is not suited for any serious purpose.
This code is not guaranteed to work. Use at your own risk!
Beware!  Trust no one!

Please e-mail philhassey@yahoo.com if you find any security holes.

Known limitations:
    - Safe doesn't have any testing for timeouts/DoS.  One-liners
        like these will lock up the system: "while 1: pass", "234234**234234"
    - Lots of (likely) safe builtins and safe AST Nodes are not allowed.
        I suppose you can add them to the whitelist if you want them.  I
        trimmed it down as much as I thought I could get away with and still
        have useful python code.
    - Might not work with future versions of python - this is made with
        python 2.4 in mind.  _STR_NOT_BEGIN might have to be extended
        in the future with more magic variable prefixes.  Or you can
        switch to conservative mode, but then even variables like "my_var" 
        won't work, which is sort of a nuisance.
    - If you get data back from a safe_exec, don't call any functions
        or methods - they might not be safe with __builtin__ restored
        to its normal state.  Work with them again via an additional safe_exec.
    - The "context" sent to the functions is not tested at all.  If you 
        pass in a dangerous function {'myfile':file} the code will be able
        to call it.
"""

# Built-in Objects
# http://docs.python.org/lib/builtin.html

# AST Nodes - compiler
# http://docs.python.org/lib/module-compiler.ast.html

# Types and members - inspection
# http://docs.python.org/lib/inspect-types.html
# The standard type heirarchy
# http://docs.python.org/ref/types.html

# Based loosely on - Restricted "safe" eval - by Babar K. Zafar
# (it isn't very safe, but it got me started)
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496746

# Securing Python: Controlling the abilities of the interpreter
# (or - why even trying this is likely to end in tears)
# http://us.pycon.org/common/talkdata/PyCon2007/062/PyCon_2007.pdf

# Changes
# 2007-03-13: added test for unicode strings that contain __, etc
# 2007-03-09: renamed safe_eval to safe_exec, since that's what it is.
# 2007-03-09: use "exec code in context" , because of test_misc_recursive_fnc
# 2007-03-09: Removed 'type' from _BUILTIN_OK - see test_misc_type_escape
# 2007-03-08: Cleaned up the destroy / restore mechanism, added more tests
# 2007-03-08: Fixed how contexts work.
# 2007-03-07: Added test for global node
# 2007-03-07: Added test for SyntaxError
# 2007-03-07: Fixed an issue where the context wasn't being reset (added test) 
# 2007-03-07: Added unittest for dir()
# 2007-03-07: Removed 'isinstance', 'issubclass' from builtins whitelist
# 2007-03-07: Removed 'EmptyNode', 'Global' from AST whitelist
# 2007-03-07: Added import __builtin__; s/__builtins__/__builtin__ 

import UserDict     # This is to get DictMixin
import threading    # This is to get a lock
import time         # This is to sleep
import subprocess   # This is to start the external process
import harshexit    # This is to kill the external process on timeout
import nonportable  # This is to get the current runtime
import os           # This is for some path manipulation
import repy_constants # This is to get our start-up directory
import exception_hierarchy # This is for exception classes shared with tracebackrepy
import compiler
import platform # This is for detecting Nokia tablets
import __builtin__

# Armon: This is how long we will wait for the external process
# to validate the safety of the user code before we timeout, 
# and exit with an exception
EVALUTATION_TIMEOUT = 10

if platform.machine().startswith('armv'):
  # The Nokia needs more time to evaluate code safety, especially
  # when under heavy loads
  EVALUTATION_TIMEOUT = 200

_NODE_CLASS_OK = [
    'Add', 'And', 'AssAttr', 'AssList', 'AssName', 'AssTuple',
    'Assert', 'Assign','AugAssign', 'Bitand', 'Bitor', 'Bitxor', 'Break',
    'CallFunc', 'Class', 'Compare', 'Const', 'Continue',
    'Dict', 'Discard', 'Div', 'Ellipsis', 'Expression', 'FloorDiv',
    'For', 'Function', 'Getattr', 'If', 'Keyword',
    'LeftShift', 'List', 'ListComp', 'ListCompFor', 'ListCompIf', 'Mod',
    'Module', 'Mul', 'Name', 'Node', 'Not', 'Or', 'Pass', 'Power',
    'Print', 'Printnl', 'Return', 'RightShift', 'Slice', 'Sliceobj',
    'Stmt', 'Sub', 'Subscript', 'Tuple', 'UnaryAdd', 'UnarySub', 'While',
    ]
_NODE_ATTR_OK = []
_STR_OK = ['__init__','__del__','__iter__']
_STR_NOT_CONTAIN = ['__']
_STR_NOT_BEGIN = ['im_','func_','tb_','f_','co_',]

## conservative settings
#_NODE_ATTR_OK = ['flags']
#_STR_NOT_CONTAIN = ['_']
#_STR_NOT_BEGIN = []

# Checks the string safety
def _is_string_safe(token):
  """
  <Purpose>
    Checks if a string is safe based on the defined rules.

  <Arguments>
    token: A value to check.

  <Returns>
    True if token is safe, false otherwise
  """

  # Check if it is explicitly allowed or the wrong type
  if type(token) is not str and type(token) is not unicode:
    return True
  if token in _STR_OK:
    return True

  # Check all the prohibited sub-strings
  for forbidden_substring in _STR_NOT_CONTAIN:
    if forbidden_substring in token:
      return False

  # Check all the prohibited prefixes
  for forbidden_prefix in _STR_NOT_BEGIN:
    if token[:len(forbidden_prefix)] == forbidden_prefix:
      return False

  # Safe otherwise
  return True


def _check_node(node):
    if node.__class__.__name__ not in _NODE_CLASS_OK:
        raise exception_hierarchy.CheckNodeException(node.lineno,node.__class__.__name__)
    for k,v in node.__dict__.items():
        # Don't allow the construction of unicode literals
        if type(v) == unicode:
          raise exception_hierarchy.CheckStrException(node.lineno,k,v)

        if k in _NODE_ATTR_OK: continue

        # Check the safety of any strings
        if not _is_string_safe(v):
          raise exception_hierarchy.CheckStrException(node.lineno,k,v)

    for child in node.getChildNodes():
        _check_node(child)

def _check_ast(code):
    ast = compiler.parse(code)
    _check_node(ast)

_type = type

def safe_type(*args, **kwargs):
  if len(args) != 1 or kwargs:
    raise exception_hierarchy.RunBuiltinException(
      'type() may only take exactly one non-keyword argument.')
  return _type(args[0])

_BUILTIN_REPLACE = {
  'type' : safe_type
}

# r = [v for v in dir(__builtin__) if v[0] != '_' and v[0] == v[0].upper()] ; r.sort() ; print r
_BUILTIN_OK = [
    '__debug__','quit','exit',
    
    'ArithmeticError', 'AssertionError', 'AttributeError', 'DeprecationWarning', 'EOFError', 'Ellipsis', 'EnvironmentError', 'Exception', 'False', 'FloatingPointError', 'FutureWarning', 'IOError', 'ImportError', 'IndentationError', 'IndexError', 'KeyError', 'KeyboardInterrupt', 'LookupError', 'MemoryError', 'NameError', 'None', 'NotImplemented', 'NotImplementedError', 'OSError', 'OverflowError', 'OverflowWarning', 'PendingDeprecationWarning', 'ReferenceError', 'RuntimeError', 'RuntimeWarning', 'StandardError', 'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'True', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError', 'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError',
    
    'abs', 'bool', 'cmp', 'complex', 'dict', 'divmod', 'filter', 'float', 'frozenset', 'hex', 'int', 'len', 'list', 'long', 'map', 'max', 'min', 'object', 'oct', 'pow', 'range', 'reduce', 'repr', 'round', 'set', 'slice', 'str', 'sum', 'tuple',  'xrange', 'zip','id',
    ]
    
#this is zope's list...
    #in ['False', 'None', 'True', 'abs', 'basestring', 'bool', 'callable',
             #'chr', 'cmp', 'complex', 'divmod', 'float', 'hash',
             #'hex', 'id', 'int', 'isinstance', 'issubclass', 'len',
             #'long', 'oct', 'ord', 'pow', 'range', 'repr', 'round',
             #'str', 'tuple', 'unichr', 'unicode', 'xrange', 'zip']:
    
    
_BUILTIN_STR = [
    'copyright','credits','license','__name__','__doc__',
    ]

def _builtin_fnc(k):
    def fnc(*vargs,**kargs):
        raise exception_hierarchy.RunBuiltinException(k)
    return fnc
_builtin_globals = None
_builtin_globals_r = None
def _builtin_init():
    global _builtin_globals, _builtin_globals_r
    if _builtin_globals != None: return
    _builtin_globals_r = __builtin__.__dict__.copy()
    r = _builtin_globals = {}
    for k in __builtin__.__dict__.keys():
        v = None
        # It's important to check _BUILTIN_REPLACE before _BUILTIN_OK because
        # even if the name is defined in both, there must be a security reason
        # why it was supposed to be replaced, not just allowed.
        if k in _BUILTIN_REPLACE: v = _BUILTIN_REPLACE[k]
        elif k in _BUILTIN_OK: v = __builtin__.__dict__[k]
        elif k in _BUILTIN_STR: v = ''
        else: v = _builtin_fnc(k)
        r[k] = v

    # Armon: Make SafeDict available
    _builtin_globals["SafeDict"] = get_SafeDict

    # Make the repy exception hierarchy available
    # For every exception in the _EXPORTED_EXCEPTIONS list, make that available
    # as a builtin
    for exception_name in exception_hierarchy._EXPORTED_EXCEPTIONS:
      _builtin_globals[exception_name] = exception_hierarchy.__dict__[exception_name]


def _builtin_destroy():
    _builtin_init()
    for k,v in _builtin_globals.items():
        __builtin__.__dict__[k] = v
def _builtin_restore():
    for k,v in _builtin_globals_r.items():
        __builtin__.__dict__[k] = v



# Get a lock for serial_safe_check
SAFE_CHECK_LOCK = threading.Lock()

# Wraps safe_check to serialize calls
def serial_safe_check(code):
  """
  <Purpose>
    Serializes calls to safe_check. This is because safe_check forks a new process
    which may take many seconds to return. This prevents us from forking many new
    python processes.
  
  <Arguments>
    code: See safe_check.
    
  <Exceptions>
    As with safe_check.
  
  <Return>
    See safe_check.
  """
  # Acquire the lock
  SAFE_CHECK_LOCK.acquire()
  
  try:
    # Call safe check
    return safe_check(code)
  
  finally:
    # Release
    SAFE_CHECK_LOCK.release()
      
    
def safe_check(code):
    """Check the code to be safe."""
    # NOTE: This code will not work in Windows Mobile due to the reliance on subprocess
    
    # Get the path to safe_check.py by using the original start directory of python
    path_to_safe_check = os.path.join(repy_constants.REPY_START_DIR, "safe_check.py")
    
    # Start a safety check process, reading from the user code and outputing to a pipe we can read
    proc = subprocess.Popen(["python", path_to_safe_check],stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    # Write out the user code, close so the other end gets an EOF
    proc.stdin.write(code)
    proc.stdin.close()
    
    # Wait for the process to terminate
    starttime = nonportable.getruntime()
    status = None
    
    # Only wait up to EVALUTATION_TIMEOUT seconds before terminating
    while status == None and (nonportable.getruntime() - starttime < EVALUTATION_TIMEOUT):
      status = proc.poll()
      time.sleep(0.02)
      
    else:
      # Check if the process is still running
      if status == None:
        # Try to terminate the external process
        try:
          harshexit.portablekill(proc.pid)
        except:
          pass
      
        # Raise an exception
        raise Exception, "Evaluation of code safety exceeded timeout threshold ("+str(nonportable.getruntime() - starttime)+" seconds)"
    
    
    # Read the output and close the pipe
    output = proc.stdout.read()
    proc.stdout.close()
    
    # Check the output, None is success, else it is a failure
    if output == "None":
      return True
    
    # If there is no output, this is a fatal error condition
    elif output == "":
      raise Exception, "Fatal error while evaluating code safety!"
      
    else:
      # Raise the error from the output
      raise exception_hierarchy.SafeException, output


# Have the builtins already been destroyed?
BUILTINS_DESTROYED = False

def safe_run(code,context=None):
    """Exec code with only safe builtins on."""
    global BUILTINS_DESTROYED
    if context == None: context = {}
    
    # Destroy the builtins if needed
    if not BUILTINS_DESTROYED:
      BUILTINS_DESTROYED = True
      _builtin_destroy()
      
    try:
        #exec code in _builtin_globals,context
        context['__builtins__'] = _builtin_globals
        exec code in context
        #_builtin_restore()
    except:
        #_builtin_restore()
        raise

def safe_exec(code,context = None):
    """Check the code to be safe, then run it with only safe builtins on."""
    serial_safe_check(code)
    safe_run(code,context)
    

# Functional constructor for SafeDict
def get_SafeDict(*args,**kwargs):
  return SafeDict(*args,**kwargs)

# Safe dictionary, which prohibits "bad" keys
class SafeDict(UserDict.DictMixin):
  """
  <Purpose>
    A dictionary implementation which prohibits "unsafe" keys
    from being set or get.
  """

  def __init__(self,from_dict=None):
    # Create the underlying dictionary
    self.__under__ = {}

    # Break if we are done...
    if from_dict is None:
      return
    if type(from_dict) is not dict and not isinstance(from_dict,SafeDict):
      return

    # If we are given a dict, try to copy its keys
    for key,value in from_dict.items():
      # Skip __builtins__ and __doc__ since safe_run/python inserts that
      if key in ["__builtins__","__doc__"]:
        continue

      # Check the key type
      if type(key) is not str and type(key) is not unicode:
        raise TypeError, "'SafeDict' keys must be of string type!"

      # Check if the key is safe
      if _is_string_safe(key):
        self.__under__[key] = value

      # Throw an exception if the key is unsafe
      else:
        raise ValueError, "Unsafe key: '"+key+"'"

  # Allow getting items
  def __getitem__(self,key):
    if type(key) is not str and type(key) is not unicode:
      raise TypeError, "'SafeDict' keys must be of string type!"
    if not _is_string_safe(key):
      raise ValueError, "Unsafe key: '"+key+"'"

    return self.__under__.__getitem__(key)

  # Allow setting items
  def __setitem__(self,key,value):
    if type(key) is not str and type(key) is not unicode:
      raise TypeError, "'SafeDict' keys must be of string type!"
    if not _is_string_safe(key):
      raise ValueError, "Unsafe key: '"+key+"'"

    return self.__under__.__setitem__(key,value)

  # Allow deleting items
  def __delitem__(self,key):
    if type(key) is not str and type(key) is not unicode:
      raise TypeError, "'SafeDict' keys must be of string type!"
    if not _is_string_safe(key):
      raise ValueError, "Unsafe key: '"+key+"'"

    return self.__under__.__delitem__(key)

  # Allow checking if a key is set
  def __contains__(self,key):
    if type(key) is not str and type(key) is not unicode:
      raise TypeError, "'SafeDict' keys must be of string type!"
    if not _is_string_safe(key):
      raise ValueError, "Unsafe key: '"+key+"'"

    return self.__under__.__contains__(key)

  # Return the key set
  def keys(self):
    # Get the keys from the underlying dict
    keys = self.__under__.keys()

    # Filter out the unsafe keys
    safe_keys = []

    for key in keys:
      if _is_string_safe(key):
        safe_keys.append(key)

    # Return the safe keys
    return safe_keys

  # Allow a copy of us
  def copy(self):
    # Create a new instance
    copy_inst = SafeDict(self.__under__)

    # Return a new instance
    return copy_inst

  # Make our fields read-only
  # This means __getattr__ can do its normal thing, but any
  # setters need to be overridden to prohibit adding/deleting/updating

  def __setattr__(self,name,value):
    # Allow setting __under__ on initialization
    if name == "__under__" and name not in self.__dict__:
      self.__dict__[name] = value
      return

    raise TypeError,"'SafeDict' attributes are read-only!"

  def __delattr__(self,name):
    raise TypeError,"'SafeDict' attributes are read-only!"


if __name__ == '__main__':
    import unittest
    
    class TestSafe(unittest.TestCase):
        def test_check_node_import(self):
            self.assertRaises(exception_hierarchy.CheckNodeException,safe_exec,"import os")
        def test_check_node_from(self):
            self.assertRaises(exception_hierarchy.CheckNodeException,safe_exec,"from os import *")
        def test_check_node_exec(self):
            self.assertRaises(exception_hierarchy.CheckNodeException,safe_exec,"exec 'None'")
        def test_check_node_raise(self):
            self.assertRaises(exception_hierarchy.CheckNodeException,safe_exec,"raise Exception")
        def test_check_node_global(self):
            self.assertRaises(exception_hierarchy.CheckNodeException,safe_exec,"global abs")
        
        def test_check_str_x(self):
            self.assertRaises(exception_hierarchy.CheckStrException,safe_exec,"x__ = 1")
        def test_check_str_str(self):
            self.assertRaises(exception_hierarchy.CheckStrException,safe_exec,"x = '__'")
        def test_check_str_class(self):
            self.assertRaises(exception_hierarchy.CheckStrException,safe_exec,"None.__class__")
        def test_check_str_func_globals(self):
            self.assertRaises(exception_hierarchy.CheckStrException,safe_exec,"def x(): pass; x.func_globals")
        def test_check_str_init(self):
            safe_exec("def __init__(self): pass")
        def test_check_str_subclasses(self):
            self.assertRaises(exception_hierarchy.CheckStrException,safe_exec,"object.__subclasses__")
        def test_check_str_properties(self):
            code = """
class X(object):
    def __get__(self,k,t=None):
        1/0
"""
            self.assertRaises(exception_hierarchy.CheckStrException,safe_exec,code)
        def test_check_str_unicode(self):
            self.assertRaises(exception_hierarchy.CheckStrException,safe_exec,"u'__'")
        
        def test_run_builtin_open(self):
            self.assertRaises(exception_hierarchy.RunBuiltinException,safe_exec,"open('test.txt','w')")
        def test_run_builtin_getattr(self):
            self.assertRaises(exception_hierarchy.RunBuiltinException,safe_exec,"getattr(None,'x')")
        def test_run_builtin_abs(self):
            safe_exec("abs(-1)")
        def test_run_builtin_open_fnc(self):
            def test():
                f = open('test.txt','w')
            self.assertRaises(exception_hierarchy.RunBuiltinException,safe_exec,"test()",{'test':test})
        def test_run_builtin_open_context(self):
            #this demonstrates how python jumps into some mystical
            #restricted mode at this point .. causing this to throw
            #an IOError.  a bit strange, if you ask me.
            self.assertRaises(IOError,safe_exec,"test('test.txt','w')",{'test':open})
        def test_run_builtin_type_context(self):
            #however, even though this is also a very dangerous function
            #python's mystical restricted mode doesn't throw anything.
            safe_exec("test(1)",{'test':type})
        def test_run_builtin_dir(self):
            self.assertRaises(exception_hierarchy.RunBuiltinException,safe_exec,"dir(None)")
        
        def test_run_exeception_div(self):
            self.assertRaises(ZeroDivisionError,safe_exec,"1/0")
        def test_run_exeception_i(self):
            self.assertRaises(ValueError,safe_exec,"(-1)**0.5")
        
        def test_misc_callback(self):
            self.value = None
            def test(): self.value = 1
            safe_exec("test()", {'test':test})
            self.assertEqual(self.value, 1)
        def test_misc_safe(self):
            self.value = None
            def test(v): self.value = v
            code = """
class Test:
    def __init__(self,value):
        self.x = value
        self.y = 4
    def run(self):
        for n in xrange(0,34):
            self.x += n
            self.y *= n
        return self.x+self.y
b = Test(value)
r = b.run()
test(r)
"""
            safe_exec(code,{'value':3,'test':test})
            self.assertEqual(self.value, 564)
            
        def test_misc_context_reset(self):
            #test that local contact is reset
            safe_exec("abs = None")
            safe_exec("abs(-1)")
            safe_run("abs = None")
            safe_run("abs(-1)")
            
        def test_misc_syntax_error(self):
            self.assertRaises(SyntaxError,safe_exec,"/")
            
        def test_misc_context_switch(self):
            self.value = None
            def test(v): self.value = v
            safe_exec("""
def test2():
    open('test.txt','w')
test(test2)
""",{'test':test})
            self.assertRaises(exception_hierarchy.RunBuiltinException,safe_exec,"test()",{'test':self.value})
        
        def test_misc_context_junk(self):
            #test that stuff isn't being added into *my* context
            #except what i want in it..
            c = {}
            safe_exec("b=1",c)
            self.assertEqual(c['b'],1)
            
        def test_misc_context_later(self):
            #honestly, i'd rec that people don't do this, but
            #at least we've got it covered ...
            c = {}
            safe_exec("def test(): open('test.txt','w')",c)
            self.assertRaises(exception_hierarchy.RunBuiltinException,c['test'])
        
        #def test_misc_test(self):
            #code = "".join(open('test.py').readlines())
            #safe_check(code)
            
        def test_misc_builtin_globals_write(self):
            #check that a user can't modify the special _builtin_globals stuff
            safe_exec("abs = None")
            self.assertNotEqual(_builtin_globals['abs'],None)
            
        #def test_misc_builtin_globals_used(self):
            ##check that the same builtin globals are always used
            #c1,c2 = {},{}
            #safe_exec("def test(): pass",c1)
            #safe_exec("def test(): pass",c2)
            #self.assertEqual(c1['test'].func_globals,c2['test'].func_globals)
            #self.assertEqual(c1['test'].func_globals,_builtin_globals)
        
        def test_misc_builtin_globals_used(self):
            #check that the same builtin globals are always used
            c = {}
            safe_exec("def test1(): pass",c)
            safe_exec("def test2(): pass",c)
            self.assertEqual(c['test1'].func_globals,c['test2'].func_globals)
            self.assertEqual(c['test1'].func_globals['__builtins__'],_builtin_globals)
            self.assertEqual(c['__builtins__'],_builtin_globals)
            
        def test_misc_type_escape(self):
            #tests that 'type' isn't allowed anymore
            #with type defined, you could create magical classes like this: 
            code = """
def delmethod(self): 1/0
foo=type('Foo', (object,), {'_' + '_del_' + '_':delmethod})()
foo.error
"""
            try:
                self.assertRaises(exception_hierarchy.RunBuiltinException,safe_exec,code)
            finally:
                pass
            
        def test_misc_recursive_fnc(self):
            code = "def test():test()\ntest()"
            self.assertRaises(RuntimeError,safe_exec,code)
            

    unittest.main()

    #safe_exec('print locals()')

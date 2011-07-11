"""
Author: Armon Dadgar
Date: June 11th, 2009
Description:
  This simple script reads "code" from stdin, and runs the safe _check_ast code on it.
  The resulting return value or exception is serialized and written to stdout.
  The purpose of this script is to be called from the main repy.py script to that the
  memory used by the safe function call will be reclaimed when this process quits.

"""

import safe
import sys

# This block allows or denies different actions in the safe module.   I'm 
# doing this here rather than the natural place in the safe module because
# I want to keep that module unmodified to make upgrading easier.

# Allow the user to do try, except, finally, etc.
safe._NODE_CLASS_OK.append("TryExcept")
safe._NODE_CLASS_OK.append("TryFinally")
safe._NODE_CLASS_OK.append("Raise")
safe._NODE_CLASS_OK.append("ExcepthandlerType")
safe._NODE_CLASS_OK.append("Invert")

# Armon: Repy V2, remove support for print()
safe._NODE_CLASS_OK.remove("Print")
safe._NODE_CLASS_OK.remove("Printnl")

# needed for traceback
# NOTE: still needed for tracebackrepy
safe._BUILTIN_OK.append("isinstance")
safe._BUILTIN_OK.append("BaseException")
safe._BUILTIN_OK.append("WindowsError")
safe._BUILTIN_OK.append("type")
safe._BUILTIN_OK.append("issubclass")
# needed to allow primitive marshalling to be built
safe._BUILTIN_OK.append("ord")
safe._BUILTIN_OK.append("chr")
# should not be used!   Use exitall instead.
safe._BUILTIN_OK.remove("exit")
safe._BUILTIN_OK.remove("quit")

safe._STR_OK.append("__repr__")
safe._STR_OK.append("__str__")
# allow __ in strings.   I'm 99% sure this is okay (do I want to risk it?)
safe._NODE_ATTR_OK.append('value')

if __name__ == "__main__":
  # Get the user "code"
  usercode = sys.stdin.read()
  
  # Output buffer
  output = ""
  
  # Check the code
  try:
    value = safe._check_ast(usercode)
    output += str(value)
  except Exception,e:
    output += str(type(e)) + " " + str(e)
  
  # Write out
  sys.stdout.write(output)
  sys.stdout.flush()
  

"""
Author: Justin Cappos

Start Date: Feb 27th, 2009

Description:
Exits if they are using an unsupported Python version...

Python v2.5 and v2.6 are officially supported, v2.7 is unofficially supported.

"""

import sys


def ensure_python_version_is_supported():
  # sys.version_info looks like this:
  # (2, 5, 0, 'final', 0)

  # Let's get the version number they have
  majorversionnumber, minorversionnumber = sys.version_info[:2]

  # Let's ensure they have 2.X where X is 5 or greater.   According to the 
  # Python folks, any minor revisions will be backwards compatible.   Also,
  # if new features are added, safe should not allow the user to use them
  # (unless they are additional arguments to an existing, allowed call).
  # This should allow us to keep the VM standardized across different Python
  # versions.
  if majorversionnumber != 2 or minorversionnumber < 5:
    print >> sys.stderr, "Python version not supported!   Use 2.5.X, 2.6.X, or 2.7.X"
    sys.exit(93)


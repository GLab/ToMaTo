#!/usr/bin/python
# -*- coding: utf-8 -*-    

from tests import *

import sys, unittest
loader = unittest.TestLoader()
if len(sys.argv)==1:
    sys.argv += ["hosts", "simpletest"]
for test in sys.argv[1:]:
    loader.loadTestsFromName("tests."+test)
unittest.main()


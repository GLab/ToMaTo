#!/usr/bin/python
# -*- coding: utf-8 -*-    

from tests import *

import sys, unittest
loader = unittest.TestLoader()
sys.argv.insert(1, '-v')
if len(sys.argv)==2:
    sys.argv += ["hosts", "templates", "kvm", "openvz", "tinc", "topology"]
for test in sys.argv[2:]:
    loader.loadTestsFromName("tests."+test)
unittest.main()


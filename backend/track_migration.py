#!/usr/bin/python

import sys, glabnetman

from south.management.commands import startmigration
cmd = startmigration.Command()
initial = argv[0] == "initial"
cmd.handle(app="glabnetman", name=argv[0], initial=initial)

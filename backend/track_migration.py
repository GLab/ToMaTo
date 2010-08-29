#!/usr/bin/python

import sys, glabnetman

from south.management.commands import startmigration
cmd = startmigration.Command()
initial = sys.argv[1] == "initial"
cmd.handle(app="glabnetman", name=sys.argv[1], initial=initial, auto=True)

#!/usr/bin/python
# -*- coding: utf-8 -*-    

import glabnetman #@UnusedImport

from django.core.management import call_command
call_command('syncdb')
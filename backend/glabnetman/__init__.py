# -*- coding: utf-8 -*-

import os
os.environ['DJANGO_SETTINGS_MODULE']="glabnetman.config"

def syncdb():
	from django.core.management import call_command
	call_command('syncdb')
	
def login(username, password):
	import ldapauth
	return ldapauth.login(username, password)
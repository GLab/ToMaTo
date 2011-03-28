# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import tomato.config as config
import tomato.util as util
import time, atexit

class User():
	def __init__ (self, name, is_user, is_admin):
		self.name = name
		self.is_user = is_user
		self.is_admin = is_admin
		
class CachedUser():
	def __init__(self, user, password):
		self.user = user
		self.password = password
		self.cachetime = time.time()

users={}

def cleanup():
	for user in users.values():
		if time.time() - user.cachetime > 3600:
			del users[user.user.name]
	
cleanup_task = util.RepeatedTimer(3, cleanup)
cleanup_task.start()
atexit.register(cleanup_task.stop)

def provider_login(user, password):
	raise Exception("No auth provider used")

exec("from %s_provider import login as provider_login" % config.auth_provider) #pylint: disable-msg=W0122

def login(username, password):
	if users.has_key(username):
		cached = users[username] 
		if cached.password == password:
			return cached.user 
	user = provider_login(username, password)
	cached = CachedUser(user, password)
	users[username] = cached
	return cached.user		
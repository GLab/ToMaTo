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

from ..lib.decorators import cached #@UnresolvedImport

@cached(300)
def server_info():
	"""
	undocumented
	"""
	return {
		"TEMPLATE_TRACKER_URL": "http://%s:%d/announce" % (config.PUBLIC_ADDRESS, config.TRACKER_PORT),
	}

@cached(300)
def host_public_key():
	return misc.getPublicKey()

@cached(300)
def external_urls():
	return misc.getExternalURLs()

def link_statistics(siteA, siteB, type=None, after=None, before=None): #@ReservedAssignment
	return link.getStatistics(siteA, siteB, type, after, before)

def mailAdmins(subject, text, global_contact = True, issue="admin"):
	if not currentUser():
		raise ErrorUnauthorized()
	misc.mailAdmins(subject, text, global_contact, issue)
	
def mailUser(user, subject, text):
	if not currentUser():
		raise ErrorUnauthorized()
	misc.mailUser(user, subject, text)

from .. import misc, config, link, currentUser
from ..lib.rpc import ErrorUnauthorized  #@UnresolvedImport
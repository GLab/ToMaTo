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

from django.db import models, transaction
import xmlrpclib, traceback

class Error(models.Model):	
	class Type:
		Error = "error"
		Info = "info"
	date_first = models.DateTimeField(auto_now_add=True)
	date_last = models.DateTimeField(auto_now=True)
	occurrences = models.IntegerField(default=1)
	type = models.CharField(max_length=20, default=Type.Error)
	title = models.CharField(max_length=255)
	message = models.TextField(blank=True)
	class Meta:
		ordering=["-date_last"]	
	def toDict(self):
		return {"id": self.id, "type": self.type, "occurrences": self.occurrences, "date_first": self.date_first, "date_last": self.date_last, "title": self.title, "message": self.message} # pylint: disable-msg=E1101

def errors_all():
	return Error.objects.all() # pylint: disable-msg=E1101

def errors_add(title, message, type=Error.Type.Error):
	title = title[:250]
	try:
		error = Error.objects.get(type=type, title=title, message=message)
		error.occurrences += 1
		error.save()
	except:
		try:
			error = Error.objects.create(type=type, title=title[:250], message=message) # pylint: disable-msg=E1101
			_send_notifications(error)
		except: #just commit the old transaction and try again
			if transaction.is_dirty():
				transaction.commit()
			error = Error.objects.create(type=type, title=title[:250], message=message) # pylint: disable-msg=E1101
			_send_notifications(error)
			
def errors_remove(error_id):
	if not error_id:
		Error.objects.all().delete()
	else:
		Error.objects.get(id=error_id).delete() # pylint: disable-msg=E1101

class Fault(xmlrpclib.Fault):
	def __str__ (self):
		return "Error %s: %s" % (self.faultCode, self.faultString)

UNKNOWN_ERROR = -1
AUTHENTICATION_ERROR = 300
USER_ERROR = 400
INTERNAL_ERROR = 500

def _must_log(exc):
	if isinstance(exc, Fault):
		return exc.faultCode in [UNKNOWN_ERROR, INTERNAL_ERROR]
	if hasattr(exc, "mustLog"):
		return exc.mustLog
	return True 

def log_info(title, message):
	errors_add(title, message, type=Error.Type.Info)

def _send_notifications(error):
	import config, auth #here to break import cycle
	title = "new %s" % error.type
	message = "A new %(type)s has occurred in ToMaTo:\n\nTitle: %(title)s\nType: %(type)s\nDate: %(date_first)s\n\n%(message)s" % error.toDict()
	for name in config.ERROR_NOTIFY:
		user = auth.getUser(name)
		if not user:
			continue
		user.sendMessage(title, message)

def log(exc):
	if _must_log(exc):
		traceback.print_exc(exc)
		errors_add('%s:%s' % (exc.__class__.__name__, exc), traceback.format_exc(exc))

def wrap(exc):
	if isinstance(exc, Fault):
		return exc
	return new('%s:%s' % (exc.__class__.__name__, exc))

def new(text, code=UNKNOWN_ERROR):
	return Fault(code, text)

def check(condition, errorStr, formatOpt = None, code=USER_ERROR):
	if not condition:
		if formatOpt:
			errorStr = errorStr % formatOpt
		raise new(errorStr, code)
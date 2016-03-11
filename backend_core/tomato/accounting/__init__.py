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

from ..db import *
from ..lib.decorators import *
import time
from ..lib.service import get_backend_users_proxy

from quota import TYPES, KEEP_RECORDS

#TODO: aggregate per user
#TODO: fetch and save current records of to-be-deleted objects



@util.wrap_task
def housekeep():
	try:
		exec_js(js_code("accounting_housekeep"), now=time.time(), types=TYPES, keep_records=KEEP_RECORDS, max_age={k: v.total_seconds() for k, v in MAX_AGE.items()})
	except:
		import traceback
		traceback.print_exc()


@util.wrap_task
def aggregate():
	try:
		exec_js(js_code("accounting_aggregate"), now=time.time(), types=TYPES, keep_records=KEEP_RECORDS, max_age={k: v.total_seconds() for k, v in MAX_AGE.items()})
	except:
		import traceback
		traceback.print_exc()


@util.wrap_task
def updateQuota():
	api = get_backend_users_proxy()
	username_list = api.username_list()
	# step 1: remove quota entries for nonexistent users
	# step 2: create empty quota entries for users that haven't been updated yet
	# step 3: update quota entries
	# fixme: implement this.

# fixme: I am not sure if the db/js functions need to be changed, and what does what.
from .. import scheduler
scheduler.scheduleRepeated(60, housekeep) #every minute @UndefinedVariable
scheduler.scheduleRepeated(60, aggregate) #every minute @UndefinedVariable
scheduler.scheduleRepeated(60, updateQuota) #every minute @UndefinedVariable

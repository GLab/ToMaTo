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

import unittest
import tests
from tomato.tasks import *
from tomato.util import curry

class Test(unittest.TestCase):
	def setUp(self):
		self.var = []
	def _fails(self, task, depends):
		assert False
	def _succeeds(self, task, depends):
		return "success"
	def _add(self, var, val):
		var.append(val)
		
	def testSuccess(self):
		proc = Process("name")
		proc.addTask(Task("name", self._succeeds, None, None, []))
		proc.run()
		assert proc.getStatus() == Status.SUCCEEDED, proc.getStatus()
	def testFails(self):
		proc = Process("name")
		proc.addTask(Task("name", self._fails, None, None, []))
		try:
			proc.run()
			assert proc.getStatus() == Status.FAILED, proc.getStatus()
		except AssertionError:
			raise
		except:
			assert False, "must not throw exception"
	def testFinished(self):
		proc = Process("name")
		proc.addTask(Task("t1", self._succeeds, None, curry(self._add, [self.var, "t1"]), []))
		proc.run()
		assert proc.getStatus() == Status.SUCCEEDED, proc.getStatus()
		assert "t1" in self.var, "task.onFinished not executed"
		proc = Process("name", onFinished=curry(self._add, [self.var, "t2"]))
		proc.addTask(Task("t2", self._succeeds, None, None, []))
		proc.run()
		assert proc.getStatus() == Status.SUCCEEDED, proc.getStatus()
		assert "t2" in self.var, "process.onFinished not executed"
	def testReverse(self):
		proc = Process("name")
		proc.addTask(Task("t1", self._fails, curry(self._add, [self.var, "t1"]), None, []))
		try:
			proc.run()
			assert "t1" in self.var, "task not reversed"
			assert proc.getStatus() == Status.ABORTED, proc.getStatus()
		except AssertionError:
			raise
		except:
			assert False, "must not throw exception"
	def testDepend(self):
		proc = Process("name")
		proc.addTask(Task("t1", self._succeeds, None, curry(self._add, [self.var, "t1"]), []))
		proc.addTask(Task("t2", self._succeeds, None, curry(self._add, [self.var, "t2"]), []))
		proc.addTask(Task("t3", self._fails, None, curry(self._add, [self.var, "t3"]), ["t1", "t2"]))
		proc.addTask(Task("t4", self._succeeds, None, curry(self._add, [self.var, "t4"]), ["t3"]))
		try:
			proc.run()
			assert "t1" in self.var, "t1 not executed"
			assert "t2" in self.var, "t2 not executed"
			assert "t3" in self.var, "t3 not executed"
			assert "t4" not in self.var, "t4 executed"
			assert proc.getStatus() == Status.FAILED, proc.getStatus()
		except AssertionError:
			raise
		except:
			assert False, "must not throw exception"
	
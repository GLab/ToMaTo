# -*- coding: utf-8 -*-

from django.db import models

class State():
	"""
	The state of the topology, this is an assigned value. The states are considered to be in order:
	created -> uploaded -> prepared -> started
	created		the topology has been created but not uploaded
	uploaded	the topology has been uploaded to the hosts but has not been prepared yet
	prepared	the topology has been uploaded and all devices have been prepared
	started		the topology has been uploaded and prepared and is currently up and running
	"""
	CREATED="created"
	UPLOADED="uploaded"
	PREPARED="prepared"
	STARTED="started"

class Topology(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=30, blank=True)

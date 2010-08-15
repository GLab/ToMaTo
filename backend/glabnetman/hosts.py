# -*- coding: utf-8 -*-

from django.db import models

class HostGroup(models.Model):
	name = models.CharField(max_length=10)
	
class Host(models.Model):
	group = models.ForeignKey(HostGroup)
	hostname = models.CharField(max_length=50)

# -*- coding: utf-8 -*-

from django.db import models

class Topology(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=30, blank=True)

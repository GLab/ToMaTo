# -*- coding: utf-8 -*-

from django.db import models

import generic

class KVMDevice(generic.Device):
	kvm_id = models.IntegerField()
	template = models.CharField(max_length=30)
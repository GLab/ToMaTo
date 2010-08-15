# -*- coding: utf-8 -*-

from django.db import models

import generic

class OpenVZDevice(generic.Device):
	openvz_id = models.IntegerField()
	root_password = models.CharField(max_length=50, null=True)
	template = models.CharField(max_length=30)

class ConfiguredInterface(generic.Interface):
	use_dhcp = models.NullBooleanField()
	ip4address = models.CharField(max_length=15, null=True)
	ip4netmask = models.CharField(max_length=15, null=True)


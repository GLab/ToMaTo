# -*- coding: utf-8 -*-

from django.db import models

import dummynet

class TincConnection(dummynet.EmulatedConnection):
	tinc_id = models.IntegerField()
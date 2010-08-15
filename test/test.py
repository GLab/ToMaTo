# -*- coding: utf-8 -*-    
import os
os.environ['DJANGO_SETTINGS_MODULE']="settings"

import settings
from models.models import *

from django.core.management import setup_environ, call_command

call_command('syncdb')
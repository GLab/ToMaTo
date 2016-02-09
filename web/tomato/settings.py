# -*- coding: utf-8 -*-
# Django settings for glabnetman project.

import os
from django import VERSION as DJANGO_VERSION
from lib import settings

settings.init('/etc/tomato/config.yaml', settings.Config.TOMATO_MODULE_WEB)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
	# ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''  # Or path to database file if using sqlite3.
DATABASE_USER = ''  # Not used with sqlite3.
DATABASE_PASSWORD = ''  # Not used with sqlite3.
DATABASE_HOST = ''  # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''  # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# Make this unique, and don't share it with anybody.
import random
SECRET_KEY = str(random.random())
if "SECRET_KEY" in os.environ:
	SECRET_KEY = os.environ["SECRET_KEY"]

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.RemoteUserAuthBackend',)

ROOT_URLCONF = 'tomato.urls'

CACHES = {
	'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 3600,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_NAME = 'tomato'
SESSION_COOKIE_AGE = 30 * 24 * 3600
SESSION_COOKIE_SECURE = False


TEMPLATE_CONTEXT_PROCESSORS = ('django.core.context_processors.request',)

CURRENT_DIR = os.path.dirname(__file__)
TEMPLATE_DIRS = (os.path.join(CURRENT_DIR, 'templates'),)

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sites',
	'tomato.crispy_forms',
	'tomato'
)

server_protocol = "http"
server_host = "localhost"
server_port = "8000"
if "BACKEND_PORT_8000_TCP" in os.environ:
	server_host = os.getenv('BACKEND_PORT_8000_TCP_ADDR')
	server_port = os.getenv('BACKEND_PORT_8000_TCP_PORT')

server_httprealm = "G-Lab ToMaTo"

tutorial_list_url = "http://packages.tomato-lab.org/tutorials/index.json"
default_executable_archives_list_url = ""

CRISPY_TEMPLATE_PACK = "bootstrap3"

if DJANGO_VERSION < (1, 4):
	TEMPLATE_LOADERS = (
		'django.template.loaders.filesystem.load_template_source',
		'django.template.loaders.app_directories.load_template_source',
	)
	SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# access tokens can be created via GitHub settings -> My Personal Access Tokens
# The token needs the scope 'repo' or 'public_repo' (depending on whether the repository is private or not)
github_access_token = ""
github_repository_owner = "GLab"
github_repository_name = "ToMaTo"

# enable API duration log.
# this slows down the webfrontend due to disk read/write operations after each API call.
# in exchange, it accurately logs the average duration of each API call.
enable_duration_log = False
# for better performance, the log should be placed on a fast disk (or even tmpfs or similar).
# there is no reason for this log to be persistent.
duration_log_location = "/tmp/webfrontend_api_duration_log.json"
# the log saves the last n durations. A higher n means more protection against deviations.
# however, when actively debugging, this means that it takes longer for changes to become visible.
# this problem can be skipped by clearing the log file before testing a new change.
duration_log_size = 25

# specify how often user information is updated (seconds between updates).
# a longer interval improves performance for webfrontend and backend,
# but it means that it takes some time for user account changes to be applied.
# updates are only done when the user opens a page which uses the API.
account_info_update_time = 120

try:
	import sys
	for path in filter(os.path.exists, ["/etc/tomato/web.conf", os.path.expanduser("~/.tomato/web.conf"), "web.conf"]):
		try:
			execfile(path)
			print >> sys.stderr, "Loaded config from %s" % path
		except Exception, exc:
			print >> sys.stderr, "Failed to load config from %s: %s" % (path, exc)
except:
	import traceback
	traceback.print_exc()

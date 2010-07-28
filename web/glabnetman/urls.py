# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r'^top/$', 'glabnetman.topologymanager.views.index'),
	(r'^top/(?P<top_id>\d+)/$', 'glabnetman.topologymanager.views.detail'),
	(r'^top/(?P<top_id>\d+)/showxml$', 'glabnetman.topologymanager.views.showxml'),
	(r'^top/(?P<top_id>\d+)/remove$', 'glabnetman.topologymanager.views.remove'),
	(r'^top/(?P<top_id>\d+)/deploy$', 'glabnetman.topologymanager.views.deploy'),
	(r'^top/(?P<top_id>\d+)/create$', 'glabnetman.topologymanager.views.create'),
	(r'^top/(?P<top_id>\d+)/destroy$', 'glabnetman.topologymanager.views.destroy'),
	(r'^top/(?P<top_id>\d+)/start$', 'glabnetman.topologymanager.views.start'),
	(r'^top/(?P<top_id>\d+)/stop$', 'glabnetman.topologymanager.views.stop'),
)

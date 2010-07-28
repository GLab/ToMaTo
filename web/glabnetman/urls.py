# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'glabnetman.main.views.index'),
	(r'^logout$', 'glabnetman.main.views.logout'),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^top/$', 'glabnetman.top.views.index'),
	(r'^top/(?P<top_id>\d+)/$', 'glabnetman.top.views.detail'),
	(r'^top/(?P<top_id>\d+)/showxml$', 'glabnetman.top.views.showxml'),
	(r'^top/(?P<top_id>\d+)/remove$', 'glabnetman.top.views.remove'),
	(r'^top/(?P<top_id>\d+)/deploy$', 'glabnetman.top.views.deploy'),
	(r'^top/(?P<top_id>\d+)/create$', 'glabnetman.top.views.create'),
	(r'^top/(?P<top_id>\d+)/destroy$', 'glabnetman.top.views.destroy'),
	(r'^top/(?P<top_id>\d+)/start$', 'glabnetman.top.views.start'),
	(r'^top/(?P<top_id>\d+)/stop$', 'glabnetman.top.views.stop'),
)

# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'glabnetman.main.index'),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^logout$', 'glabnetman.main.logout'),
	(r'^help$', 'glabnetman.main.help'),
	(r'^help/(?P<page>.*)$', 'glabnetman.main.help'),
	(r'^task/(?P<task_id>.*)$', 'glabnetman.main.task_status'),
	(r'^top/$', 'glabnetman.top.index'),
	(r'^top\?host_filter=(?P<host_filter>.*)$', 'glabnetman.top.index'),
	(r'^top/create$', 'glabnetman.top.create'),
	(r'^top/(?P<top_id>\d+)/edit$', 'glabnetman.top.edit'),
	(r'^top/(?P<top_id>\d+)/upload_image/(?P<device_id>.*)$', 'glabnetman.top.upload_image'),
	(r'^top/(?P<top_id>\d+)/download_image/(?P<device_id>.*)$', 'glabnetman.top.download_image'),
	(r'^top/(?P<top_id>\d+)/vncview/(?P<device_id>.*)$', 'glabnetman.top.vncview'),
	(r'^top/(?P<top_id>\d+)/details$', 'glabnetman.top.details'),
	(r'^top/(?P<top_id>\d+)/showxml$', 'glabnetman.top.showxml'),
	(r'^top/(?P<top_id>\d+)/prepare$', 'glabnetman.top.prepare'),
	(r'^top/(?P<top_id>\d+)/destroy$', 'glabnetman.top.destroy'),
	(r'^top/(?P<top_id>\d+)/start$', 'glabnetman.top.start'),
	(r'^top/(?P<top_id>\d+)/stop$', 'glabnetman.top.stop'),
	(r'^top/(?P<top_id>\d+)/remove$', 'glabnetman.top.remove'),
	(r'^host/$', 'glabnetman.host.index'),
	(r'^host/add$', 'glabnetman.host.add'),
	(r'^host/remove/(?P<hostname>.*)$', 'glabnetman.host.remove'),
)

# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'glabnetman.main.views.index'),
	(r'^logout$', 'glabnetman.main.views.logout'),
	(r'^task/(?P<task_id>.*)$', 'glabnetman.main.views.task_status'),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^top/$', 'glabnetman.top.views.index'),
	(r'^top/create$', 'glabnetman.top.views.create'),
	(r'^top/edit$', 'glabnetman.top.views.edit'),
	(r'^top/upload$', 'glabnetman.top.views.upload'),
	(r'^top/download$', 'glabnetman.top.views.download'),
	(r'^top/(?P<top_id>\d+)/$', 'glabnetman.top.views.action'),
	(r'^top/(?P<top_id>\d+)/(?P<action>[a-z]+)$', 'glabnetman.top.views.action'),
	(r'^host/$', 'glabnetman.host.views.index'),
	(r'^host/add$', 'glabnetman.host.views.add'),
	(r'^host/remove$', 'glabnetman.host.views.remove'),
)

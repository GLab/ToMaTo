# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'glabnetman.main.index'),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^help$', 'glabnetman.main.help'),
	(r'^help/(?P<page>.*)$', 'glabnetman.main.help'),
	(r'^link_stats$', 'glabnetman.main.physical_links'),
	(r'^resource_stats/by_topology$', 'glabnetman.main.resource_usage_by_topology'),
	(r'^resource_stats/by_user$', 'glabnetman.main.resource_usage_by_user'),
	(r'^errors$', 'glabnetman.main.error_list'),
	(r'^errors/remove/(?P<error_id>.*)$', 'glabnetman.main.error_remove'),
	(r'^tasks$', 'glabnetman.main.task_list'),
	(r'^task/(?P<task_id>.*)$', 'glabnetman.main.task_status'),
	(r'^top/$', 'glabnetman.top.index'),
	(r'^top\?host_filter=(?P<host_filter>.*)$', 'glabnetman.top.index'),
	(r'^top/create$', 'glabnetman.top.create'),
	(r'^top/(?P<top_id>\d+)/edit$', 'glabnetman.top.edit'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/upload_image$', 'glabnetman.top.upload_image'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/download_image$', 'glabnetman.top.download_image'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/vncview/$', 'glabnetman.top.vncview'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/start$', 'glabnetman.top.dev_start'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/stop$', 'glabnetman.top.dev_stop'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/prepare$', 'glabnetman.top.dev_prepare'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/destroy$', 'glabnetman.top.dev_destroy'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/start$', 'glabnetman.top.con_start'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/stop$', 'glabnetman.top.con_stop'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/prepare$', 'glabnetman.top.con_prepare'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/destroy$', 'glabnetman.top.con_destroy'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/captures/(?P<device_id>.*)/(?P<interface_id>.*)$', 'glabnetman.top.download_capture'),
	(r'^top/(?P<top_id>\d+)/permissions$', 'glabnetman.top.permission_list'),
	(r'^top/(?P<top_id>\d+)/permission/remove/(?P<user>.*)$', 'glabnetman.top.permission_remove'),
	(r'^top/(?P<top_id>\d+)/permission/add$', 'glabnetman.top.permission_add'),
	(r'^top/(?P<top_id>\d+)/details$', 'glabnetman.top.details'),
	(r'^top/(?P<top_id>\d+)/show$', 'glabnetman.top.show'),
	(r'^top/(?P<top_id>\d+)/prepare$', 'glabnetman.top.prepare'),
	(r'^top/(?P<top_id>\d+)/destroy$', 'glabnetman.top.destroy'),
	(r'^top/(?P<top_id>\d+)/start$', 'glabnetman.top.start'),
	(r'^top/(?P<top_id>\d+)/stop$', 'glabnetman.top.stop'),
	(r'^top/(?P<top_id>\d+)/remove$', 'glabnetman.top.remove'),
	(r'^top/(?P<top_id>\d+)/renew$', 'glabnetman.top.renew'),
	(r'^host/$', 'glabnetman.host.index'),
	(r'^host/(?P<hostname>.*)/detail$', 'glabnetman.host.detail'),
	(r'^host/(?P<hostname>.*)/special_feature_add$', 'glabnetman.host.special_feature_add'),
	(r'^host/(?P<hostname>.*)/special_feature_remove$', 'glabnetman.host.special_feature_remove'),
	(r'^host/(?P<hostname>.*)/remove$', 'glabnetman.host.remove'),
	(r'^host/(?P<hostname>.*)/debug$', 'glabnetman.host.debug'),
	(r'^host/(?P<hostname>.*)/check$', 'glabnetman.host.check'),
	(r'^host/edit$', 'glabnetman.host.edit'),
	(r'^template/$', 'glabnetman.template.index'),
	(r'^template/add$', 'glabnetman.template.add'),
	(r'^template/remove/(?P<name>.*)$', 'glabnetman.template.remove'),
	(r'^template/set_default/(?P<type>.*)/(?P<name>.*)$', 'glabnetman.template.set_default'),
)

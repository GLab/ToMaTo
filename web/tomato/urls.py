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
	(r'^$', 'tomato.main.index'),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^help$', 'tomato.main.help'),
	(r'^help/(?P<page>.*)$', 'tomato.main.help'),
	(r'^ticket$', 'tomato.main.ticket'),
	(r'^link_stats$', 'tomato.main.physical_links'),
	(r'^resource_stats/by_topology$', 'tomato.main.resource_usage_by_topology'),
	(r'^resource_stats/by_user$', 'tomato.main.resource_usage_by_user'),
	(r'^errors$', 'tomato.main.error_list'),
	(r'^errors/remove/(?P<error_id>.*)$', 'tomato.main.error_remove'),
	(r'^tasks$', 'tomato.main.task_list'),
	(r'^task/(?P<task_id>.*)$', 'tomato.main.task_status'),
	(r'^top/$', 'tomato.top.index'),
	(r'^top\?host_filter=(?P<host_filter>.*)$', 'tomato.top.index'),
	(r'^top/create$', 'tomato.top.create'),
	(r'^top/(?P<top_id>\d+)/edit$', 'tomato.top.edit'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/upload_image$', 'tomato.top.upload_image'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/download_image$', 'tomato.top.download_image'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/vncview/$', 'tomato.top.vncview'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/start$', 'tomato.top.dev_start'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/stop$', 'tomato.top.dev_stop'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/prepare$', 'tomato.top.dev_prepare'),
	(r'^top/(?P<top_id>\d+)/devices/(?P<device_id>.*)/destroy$', 'tomato.top.dev_destroy'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/start$', 'tomato.top.con_start'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/stop$', 'tomato.top.con_stop'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/prepare$', 'tomato.top.con_prepare'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/destroy$', 'tomato.top.con_destroy'),
	(r'^top/(?P<top_id>\d+)/connectors/(?P<connector_id>.*)/captures/(?P<device_id>.*)/(?P<interface_id>.*)$', 'tomato.top.download_capture'),
	(r'^top/(?P<top_id>\d+)/permissions$', 'tomato.top.permission_list'),
	(r'^top/(?P<top_id>\d+)/permission/remove/(?P<user>.*)$', 'tomato.top.permission_remove'),
	(r'^top/(?P<top_id>\d+)/permission/add$', 'tomato.top.permission_add'),
	(r'^top/(?P<top_id>\d+)/details$', 'tomato.top.details'),
	(r'^top/(?P<top_id>\d+)/show$', 'tomato.top.show'),
	(r'^top/(?P<top_id>\d+)/prepare$', 'tomato.top.prepare'),
	(r'^top/(?P<top_id>\d+)/destroy$', 'tomato.top.destroy'),
	(r'^top/(?P<top_id>\d+)/start$', 'tomato.top.start'),
	(r'^top/(?P<top_id>\d+)/stop$', 'tomato.top.stop'),
	(r'^top/(?P<top_id>\d+)/remove$', 'tomato.top.remove'),
	(r'^top/(?P<top_id>\d+)/renew$', 'tomato.top.renew'),
	(r'^host/$', 'tomato.host.index'),
	(r'^host/(?P<hostname>.*)/detail$', 'tomato.host.detail'),
	(r'^host/(?P<hostname>.*)/remove$', 'tomato.host.remove'),
	(r'^host/(?P<hostname>.*)/debug$', 'tomato.host.debug'),
	(r'^host/(?P<hostname>.*)/check$', 'tomato.host.check'),
	(r'^host/(?P<hostname>.*)/edit$', 'tomato.host.edit'),
	(r'^host/add$', 'tomato.host.edit', {"hostname": None}),
	(r'^special_features$', 'tomato.special_features.index'),
	(r'^special_features/add$', 'tomato.special_features.add_group'),
	(r'^special_features/(?P<type>.*)/(?P<group>.*)/remove$', 'tomato.special_features.remove_group'),
	(r'^special_features/(?P<type>.*)/(?P<group>.*)/change$', 'tomato.special_features.change_group'),
	(r'^special_features/addhost/(?P<hostname>.*)$', 'tomato.special_features.add_host'),
	(r'^special_features/(?P<type>.*)/(?P<group>.*)/removehost/(?P<hostname>.*)$', 'tomato.special_features.remove_host'),
	(r'^template/$', 'tomato.template.index'),
	(r'^template/add$', 'tomato.template.add'),
	(r'^template/remove/(?P<name>.*)$', 'tomato.template.remove'),
	(r'^template/set_default/(?P<type>.*)/(?P<name>.*)$', 'tomato.template.set_default'),
	(r'^ajax/top/(?P<top_id>\d+)/modify$', 'tomato.ajax.modify'),
)

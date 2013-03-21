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
	(r'^img/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'img'}),
	(r'^js/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'js'}),
	(r'^editor_tutorial/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'editor_tutorial'}),
	(r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'style'}),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^help$', 'tomato.main.help'),
	(r'^help/(?P<page>.*)$', 'tomato.main.help'),
	(r'^ticket$', 'tomato.main.ticket'),
	(r'^project$', 'tomato.main.project'),
	(r'^logout$', 'tomato.main.logout'),
	(r'^account/register$', 'tomato.account.register'),	
	(r'^account$', 'tomato.account.info'),	
	(r'^account/info$', 'tomato.account.info'),	
	(r'^account/info/(?P<id>.*)$', 'tomato.account.info'),	
	(r'^account/index$', 'tomato.account.index'),	
	(r'^topology/$', 'tomato.topology.index'),
	(r'^topology/(?P<id>\d+)$', 'tomato.topology.info'),
	(r'^topology/(?P<id>\d+)/export$', 'tomato.topology.export'),
	(r'^topology/(?P<id>\d+)/usage$', 'tomato.topology.usage'),
	(r'^topology/create$', 'tomato.topology.create'),
	(r'^topology/import$', 'tomato.topology.import_form'),
	(r'^topology/tutorial$', 'tomato.editor_tutorial.index'),
	(r'^topology/tutorial/start/(?P<tut_id>\w+)$', 'tomato.editor_tutorial.loadTutorial'),
	(r'^connection/(?P<id>\d+)/usage$', 'tomato.connection.usage'),
	(r'^element/(?P<id>\d+)/usage$', 'tomato.element.usage'),
	(r'^element/(?P<id>\d+)/console$', 'tomato.element.console'),
	(r'^element/(?P<id>\d+)/console_novnc$', 'tomato.element.console_novnc'),
	(r'^link_stats/$', 'tomato.physical_link_stats.index'),
	(r'^link_stats/(?P<site>\w+)$', 'tomato.physical_link_stats.details_site'),
	(r'^link_stats/(?P<src>\w+)/(?P<dst>\w+)$', 'tomato.physical_link_stats.details_link'),
	(r'^host/$', 'tomato.host.index'),
	(r'^host/add$', 'tomato.host.add'),
	(r'^host/edit$', 'tomato.host.edit'),
	(r'^host/remove$', 'tomato.host.remove'),
	(r'^site/$', 'tomato.site.index'),
	(r'^site/add$', 'tomato.site.add'),
	(r'^site/edit$', 'tomato.site.edit'),
	(r'^site/remove$', 'tomato.site.remove'),
	(r'^templates/$', 'tomato.device_templates.index'),
	(r'^templates/add$', 'tomato.device_templates.add'),
	(r'^templates/edit$', 'tomato.device_templates.edit'),
	(r'^templates/edit/data$', 'tomato.device_templates.edit_data'),
	(r'^templates/edit/torrent$', 'tomato.device_templates.edit_torrent'),
	(r'^templates/remove$', 'tomato.device_templates.remove'),
	(r'^profiles/$', 'tomato.device_profile.index'),
	(r'^profiles/add/$', 'tomato.device_profile.add'),
	(r'^profiles/edit/$', 'tomato.device_profile.edit'),
	(r'^profiles/remove$', 'tomato.device_profile.remove'),
	(r'^external_networks/$', 'tomato.external_networks.index'),
	(r'^external_networks/add/$', 'tomato.external_networks.add'),
	(r'^external_networks/edit/$', 'tomato.external_networks.edit'),
	(r'^external_networks/remove$', 'tomato.external_networks.remove'),
	(r'^external_network_instances/$', 'tomato.external_network_instances.index'),
	(r'^external_network_instances/add/$', 'tomato.external_network_instances.add'),
	(r'^external_network_instances/edit/$', 'tomato.external_network_instances.edit'),
	(r'^external_network_instances/remove$', 'tomato.external_network_instances.remove'),
	(r'^ajax/topology/(?P<id>\d+)/info$', 'tomato.ajax.topology_info'),
	(r'^ajax/topology/(?P<id>\d+)/action$', 'tomato.ajax.topology_action'),
	(r'^ajax/topology/(?P<id>\d+)/modify$', 'tomato.ajax.topology_modify'),
	(r'^ajax/topology/(?P<id>\d+)/remove$', 'tomato.ajax.topology_remove'),
	(r'^ajax/element/(?P<id>\d+)/info$', 'tomato.ajax.element_info'),
	(r'^ajax/topology/(?P<topid>\d+)/create_element$', 'tomato.ajax.element_create'),
	(r'^ajax/element/(?P<id>\d+)/action$', 'tomato.ajax.element_action'),
	(r'^ajax/element/(?P<id>\d+)/modify$', 'tomato.ajax.element_modify'),
	(r'^ajax/element/(?P<id>\d+)/remove$', 'tomato.ajax.element_remove'),
	(r'^ajax/connection/(?P<id>\d+)/info$', 'tomato.ajax.connection_info'),
	(r'^ajax/connection/create$', 'tomato.ajax.connection_create'),
	(r'^ajax/connection/(?P<id>\d+)/action$', 'tomato.ajax.connection_action'),
	(r'^ajax/connection/(?P<id>\d+)/modify$', 'tomato.ajax.connection_modify'),
	(r'^ajax/connection/(?P<id>\d+)/remove$', 'tomato.ajax.connection_remove'),
	(r'^ajax/account/(?P<name>.*)/info', 'tomato.ajax.account_info'),
)

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
	(r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'style'}),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^help$', 'tomato.main.help'),
	(r'^help/(?P<page>.*)$', 'tomato.main.help'),
	(r'^ticket$', 'tomato.main.ticket'),
	(r'^project$', 'tomato.main.project'),
	(r'^logout$', 'tomato.main.logout'),
	(r'^topology/$', 'tomato.topology.index'),
	(r'^topology/(?P<id>\d+)$', 'tomato.topology.info'),
	(r'^topology/(?P<id>\d+)/usage$', 'tomato.topology.usage'),
	(r'^topology/create$', 'tomato.topology.create'),
	(r'^topology/import$', 'tomato.topology.import_form'),
	(r'^host/$', 'tomato.host.index'),
)

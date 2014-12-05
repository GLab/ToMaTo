# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2012 Integrated Communication Systems Lab, University of Kaiserslautern
#
# This file is part of the ToMaTo project
#
# ToMaTo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.shortcuts import render
import math

from lib import wrap_rpc

def get_site_location(site_name,api):
	geoloc = api.site_info(site_name)['geolocation']
	return {'longitude':geoloc.get('longitude',0),
			'latitude':geoloc.get('latitude',0)}

def site_list(api):
	r = []
	for i in api.site_list():
		r.append(i['name'])
	return r

def site_location_list(api):
	r = []
	l = api.site_list()
	organizations = api.organization_list()
	orgas = {}
	for o in organizations:
		orgas[o['name']] = o
	for i in l:
		r.append({'name':i['name'],
				  'geolocation':get_site_location(i['name'],api),
				  'displayName':i['description'],
				  'location':i['location'],
				  'organization':orgas[i['organization']],
				  'description':i['description_text']
				  })
	return r

def site_site_pairs(api,allow_self=True): # allow_self: allow self-referencing pairs like ('ukl','ukl')
	r = []
	l = site_list(api)
	for i in range(len(l)):
		i_mod = i
		if not (allow_self):
			i_mod = i_mod+1
		for j in range(i_mod,len(l)):
			r.append((l[i],l[j]))
	return r


class Site_site_stats:
	delay_avg = 0.0
	loss_avg = 0.0
	delay_stddev = 0.0
	loss_stddev = 0.0
	
	cache_site_site_pairs = []
	pairs = []
	
	def __init__(self, api):
		self.cache_site_site_pairs = site_site_pairs(api,False)
		for p in self.cache_site_site_pairs:
			src = p[0]
			dst = p[1]
			stats = api.link_statistics(src,dst,"5minutes")
			
			#find last entry
			last = {'end':0}
			for entry in stats:
				if entry['end']>last['end']:
					last = entry
					
			self.pairs.append({'src':src,'dst':dst,'laststat':last})
			
		self.calc_avg()

	def calc_avg(self):
		links = self.pairs
			
		#calculate average
		delay_sum = 0.0
		loss_sum = 0.0
		len_links = 0 #since some elements may not be counted (if in for loop), the length must be calculated regarding this fact.
		for l in links:
			if l['laststat'].has_key('delay_avg') and l['laststat'].has_key('loss'):
				delay_sum += l['laststat']["delay_avg"]
				loss_sum += l['laststat']["loss"]
				len_links += 1
		self.delay_avg = delay_sum / (len_links or 1.0)
		self.loss_avg = loss_sum / (len_links or 1.0)
		
		#calculate stddev
		delay_stddev = 0.0
		loss_stddev = 0.0
		for l in links:
			if l['laststat'].has_key('delay_avg') and l['laststat'].has_key('loss'):
				delay_stddev += (self.delay_avg - l['laststat']["delay_avg"]) * (self.delay_avg - l['laststat']["delay_avg"])
				loss_stddev += (self.loss_avg - l['laststat']["loss"]) * (self.loss_avg - l['laststat']["loss"])
		if len_links > 1:
			delay_stddev /= len_links -1
			loss_stddev /= len_links -1
		self.delay_stddev = math.sqrt(delay_stddev)
		self.loss_stddev = math.sqrt(loss_stddev)

		
	def get_delay_avg(self):
		return self.delay_avg
	
	def get_loss_avg(self):
		return self.loss_avg
		
	def get_delay_stddev(self):
		return self.delay_stddev
	
	def get_loss_stddev(self):
		return self.loss_stddev
	
	def get_color(self,src,dst): # returns a html-formatted color
		
		#find loss/delay for particular link in cache
		p = None
		for pa in self.pairs:
			if (pa['src'] == src and pa['dst'] == dst) or (pa['src'] == dst and pa['dst'] == src):
				p = pa
		if p == None or not (p['laststat'].has_key('delay_avg') and p['laststat'].has_key('loss')): #in case nothing was found
			return (0.2, 0.2, 0.7)
		
		delay = p['laststat']['delay_avg']
		loss  = p['laststat']['loss']
		
		#calculate color
		delay_avg_factor = 0.0
		loss_factor = 0.0
		if self.get_delay_stddev() != 0.0:
			delay_avg_factor = (delay - self.get_delay_avg()) / self.get_delay_stddev()
		if self.get_loss_stddev() != 0.0:
			loss_factor = (loss - self.get_loss_avg()) / self.get_loss_stddev() if loss > 0.001 else -2

		factor = max(delay_avg_factor, loss_factor)
		factor = max(min((factor+2.0)/5.0, 1.0), 0.0); #normalize -2..3 -> 0..1
		import colorsys
		return colorsys.hsv_to_rgb((1.0-factor)/3.0,1.0,0.7)
		

def site_site_connections(api):
	r = []
	sstats = Site_site_stats(api)
	l = sstats.cache_site_site_pairs
	
	for i in l:
		src = i[0]
		dst = i[1]
		
		color = sstats.get_color(src, dst)
		
		r.append({
			"src":src,
			"dst":dst,
			"color":color
			})
	return r

@wrap_rpc
def map(api, request):
	sites = site_location_list(api)
	links = site_site_connections(api)
	return render(request, "map/index.html",{'sites': sites,'links': links})

@wrap_rpc
def map_kml(api, request):
	sites = site_location_list(api)
	sitemap = {}
	for site in sites:
		sitemap[site["name"]] = site
	links = site_site_connections(api)
	for link in links:
		link["src_data"] = sitemap[link["src"]]
		link["dst_data"] = sitemap[link["dst"]]
		link["color"] = "ff%02x%02x%02x" % tuple(reversed([r * 256 for r in link["color"]]))
	return render(request, "map/kml.html",{'sites': sites,'links': links,'user':api.user})

@wrap_rpc
def details_link(api, request, src, dst):
	return render(request, "map/usage.html",{'usage':api.link_statistics(src,dst),'name': api.site_info(src)['description'] + " <-> " + api.site_info(dst)['description'],'user':api.user});

@wrap_rpc
def details_site(api, request, site):
	return render(request, "map/usage.html",{'usage':api.link_statistics(site,site),'name':"inside "+api.site_info(site)['description'],'user':api.user});

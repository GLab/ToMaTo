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
from django import forms
import math, socket

from lib import wrap_rpc
from admin_common import organization_name_list

from admin_common import BootstrapForm
from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import FormActions, StrictButton
from django.core.urlresolvers import reverse

class SiteForm(BootstrapForm):
	name = forms.CharField(max_length=50, help_text="The name of the site. Must be unique to all sites. e.g.: ukl")
	description = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
	description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
	organization = forms.CharField(max_length=50)
	location = forms.CharField(max_length=255, help_text="e.g.: Germany")
	geolocation_longitude = forms.FloatField(help_text="Float Number. >0 if East, <0 if West",label="Geolocation: Longitude")
	geolocation_latitude = forms.FloatField(help_text="Float Number. >0 if North, <0 if South",label="Geolocation: Latitude")
	okbutton_text = "Add"
	def __init__(self, api, *args, **kwargs):
		super(SiteForm, self).__init__(*args, **kwargs)
		self.fields["organization"].widget = forms.widgets.Select(choices=organization_name_list(api))
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
			'name',
			'description',
			'description_text',
			'organization',
			'location',
			'geolocation_longitude',
			'geolocation_latitude',
			FormActions(
				StrictButton(self.okbutton_text, css_class='btn-primary', type="submit"),
				StrictButton('Cancel', css_class='btn-default backbutton')
			)
		)
	
class EditSiteForm(SiteForm):
	okbutton_text = "Save"
	def __init__(self, api, *args, **kwargs):
		super(EditSiteForm, self).__init__(api, *args, **kwargs)
		self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
		self.fields["name"].help_text=None
		self.helper.form_action = reverse(edit)
	
class RemoveSiteForm(BootstrapForm):
	name = forms.CharField(max_length=50, widget=forms.HiddenInput)
	def __init__(self, *args, **kwargs):
		super(RemoveSiteForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(remove)
		self.helper.layout = Layout(
			'name',
			FormActions(
				StrictButton('Confirm', css_class='btn-primary', type="submit"),
				StrictButton('Cancel', css_class='btn-default backbutton')
			)
		)
	
@wrap_rpc
def list(api, request):
	return render(request, "admin/site/index.html", {'site_list': api.site_list()})

@wrap_rpc
def add(api, request):
	if request.method == 'POST':
		form = SiteForm(api, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.site_create(formData["name"],formData['organization'],formData["description"])
			api.site_modify(formData["name"],{"location": formData["location"],
											  'geolocation':{'longitude':formData['geolocation_longitude'],
															 'latitude':formData['geolocation_latitude']},
											  'organization':formData['organization'],
											  'description_text':formData['description_text']})
			return render(request, "admin/site/add_success.html", {'name': formData["name"]})
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Site"})
	else:
		form = SiteForm(api)
		return render(request, "form.html", {'form': form, "heading":"Add Site"})
	
@wrap_rpc
def remove(api, request, name=None):
	if request.method == 'POST':
		form = RemoveSiteForm(request.POST)
		if form.is_valid():
			name = form.cleaned_data["name"]
			api.site_remove(name)
			return render(request, "admin/site/remove_success.html", {'name': name})
		else:
			if not name:
				name = request.POST['name']
			if name:
				form = RemoveSiteForm()
				form.fields["name"].initial = name
				return render(request, "form.html", {"heading": "Remove Site", "message_before": "Are you sure you want to remove the site '"+name+"'?", 'form': form})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	
	else:
		if name:
			form = RemoveSiteForm()
			form.fields["name"].initial = name
			return render(request, "form.html", {"heading": "Remove Site", "message_before": "Are you sure you want to remove the site '"+name+"'?", 'form': form})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No site specified. Have you followed a valid link?'})
	
@wrap_rpc
def edit(api, request, name=None):
	if request.method=='POST':
		form = EditSiteForm(api, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			api.site_modify(formData["name"],{'description':formData["description"],
											  'location':formData["location"],
											  'geolocation':{'longitude':formData['geolocation_longitude'],
															 'latitude':formData['geolocation_latitude']},
											  'organization':formData['organization'],
											  'description_text':formData['description_text']})
			return render(request, "admin/site/edit_success.html", {'name': formData["name"]})
		else:
			if not name:
				name=request.POST["name"]
			if name:
				form.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
				form.fields["name"].help_text=None
				return render(request, "form.html", {"heading": "Editing Site '"+name+"'", 'form': form})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
			
	else:
		if name:
			siteInfo = api.site_info(name)
			siteInfo['geolocation_longitude'] = siteInfo['geolocation'].get('longitude',0)
			siteInfo['geolocation_latitude'] = siteInfo['geolocation'].get('latitude',0)
			del siteInfo['geolocation']
			form = EditSiteForm(api, siteInfo)
			return render(request, "form.html", {"heading": "Editing Site '"+name+"'", 'form': form})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No site specified. Have you followed a valid link?'})

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
	for i in l:
		r.append({'name':i['name'],
				  'geolocation':get_site_location(i['name'],api),
				  'displayName':i['description'],
				  'location':i['location']
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
	_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	_socket.connect(("8.8.8.8",80))
	PUBLIC_ADDRESS = _socket.getsockname()[0]
	_socket.close()
	return render(request, "admin/physical_link_stats/index.html",{'site_location_list':site_location_list(api),'connections': site_site_connections(api),'user':api.user,'public_address':PUBLIC_ADDRESS})

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
	return render(request, "admin/physical_link_stats/kml.html",{'sites': sites,'links': links,'user':api.user})

@wrap_rpc
def details_link(api, request, src, dst):
	return render(request, "admin/physical_link_stats/usage.html",{'usage':api.link_statistics(src,dst),'name': api.site_info(src)['description'] + " <-> " + api.site_info(dst)['description'],'user':api.user});

@wrap_rpc
def details_site(api, request, site):
	return render(request, "admin/physical_link_stats/usage.html",{'usage':api.link_statistics(site,site),'name':"inside "+api.site_info(site)['description'],'user':api.user});

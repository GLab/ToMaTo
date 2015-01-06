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

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django import forms
import base64, re
from lib import wrap_rpc, serverInfo
from admin_common import RemoveConfirmForm, help_url, BootstrapForm, Buttons, append_empty_choice
import datetime

from tomato.crispy_forms.layout import Layout
from django.core.urlresolvers import reverse

from lib.error import UserError #@UnresolvedImport

techs=[
		{"name": "kvmqm", "label": "KVM"},
		{"name": "openvz", "label": "OpenVZ"},
		{"name": "repy", "label": "Repy"}
	  ]
techs_dict=dict([(t["name"], t["label"]) for t in techs])
def techs_choices():
	tdict = [(t["name"], t["label"]) for t in techs]
	return append_empty_choice(tdict)

kblang_options = [("en-us", "English (US)"), 
					("en-gb", "English (GB)"), 
					("de", "German"), 
					("fr", "French"), 
					("ja", "Japanese")
					]

class TemplateForm(BootstrapForm):
	label = forms.CharField(max_length=255, help_text="The displayed label for this profile")
	subtype = forms.CharField(max_length=255, required=False)
	description = forms.CharField(widget = forms.Textarea, required=False)
	preference = forms.IntegerField(label="Preference", help_text="Sort templates in the editor (higher preference first). The template with highest preference will be the default. Must be an integer number.")
	restricted = forms.BooleanField(label="Restricted", help_text="Restrict usage of this template to administrators", required=False)
	nlXTP_installed = forms.BooleanField(label="nlXTP Guest Modules installed", help_text="Ignore this for Repy devices.", required=False)
	creation_date = forms.DateField(required=False,widget=forms.TextInput(attrs={'class': 'datepicker'}));
	show_as_common = forms.BooleanField(label="Show in Common Elements", help_text="Show this template in the common elements section in the editor", required=False)
	icon = forms.URLField(label="Icon", help_text="URL of a 32x32 icon to use for elements of this template, leave empty to use the default icon", required=False)
	kblang = forms.CharField(max_length=50,label="Keyboard Layout",widget = forms.widgets.Select(choices=kblang_options))
	def __init__(self, *args, **kwargs):
		super(TemplateForm, self).__init__(*args, **kwargs)
		self.fields['creation_date'].initial=datetime.date.today()
		self.fields['kblang'].initial="en_US"
	
class AddTemplateForm(TemplateForm):
	torrentfile  = forms.FileField(label="Torrent:", help_text='<a href="http://tomato.readthedocs.org/en/latest/docs/templates" target="_blank">Help</a>')
	name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all profiles. Cannot be changed. Not displayed.")
	tech = forms.CharField(max_length=255,widget = forms.widgets.Select(choices=techs_choices()))
	def __init__(self, *args, **kwargs):
		super(AddTemplateForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
            'name',
            'label',
            'subtype',
            'description',
            'tech',
            'preference',
            'show_as_common',
            'restricted',
            'nlXTP_installed',
            'icon',
            'creation_date',
            'torrentfile',
            Buttons.cancel_add
        )
	
class EditTemplateForm(TemplateForm):
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	def __init__(self, res_id, showKblang=False, *args, **kwargs):
		super(EditTemplateForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(edit, kwargs={"res_id": res_id})
		if showKblang:
			self.helper.layout = Layout(
	            'res_id',
	            'label',
	            'subtype',
	            'description',
	            'preference',
	            'show_as_common',
	            'restricted',
	            'nlXTP_installed',
				'icon',
	            'creation_date',
	            'kblang',
	            Buttons.cancel_save
	        )
		else:
			del self.fields['kblang']
			self.helper.layout = Layout(
	            'res_id',
	            'label',
	            'subtype',
	            'description',
	            'preference',
	            'show_as_common',
	            'restricted',
	            'nlXTP_installed',
				'icon',
	            'creation_date',
	            Buttons.cancel_save
	        )
	
class ChangeTemplateTorrentForm(BootstrapForm):
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	creation_date = forms.DateField(required=False,widget=forms.TextInput(attrs={'class': 'datepicker'}))
	torrentfile  = forms.FileField(label="Torrent containing image:", help_text='See the <a href="https://tomato.readthedocs.org/en/latest/docs/templates/" target="_blank">template documentation about the torrent file.</a> for more information')	
	def __init__(self, res_id, *args, **kwargs):
		super(ChangeTemplateTorrentForm, self).__init__(*args, **kwargs)
		self.fields['creation_date'].initial=datetime.date.today()
		self.helper.form_action = reverse(edit_torrent, kwargs={"res_id": res_id})
		self.helper.layout = Layout(
            'res_id',
            'creation_date',
            'torrentfile',
            Buttons.cancel_save
        )

@wrap_rpc
def list(api, request, tech):
	templ_list = api.resource_list('template')
	def _cmp(ta, tb):
		a = ta["attrs"]
		b = tb["attrs"]
		c = cmp(a["tech"], b["tech"])
		if c:
			return c
		c = -cmp(a["preference"], b["preference"])
		if c:
			return c
		return cmp(a["name"], b["name"])
	templ_list.sort(_cmp)
	if tech:
		templ_list = filter(lambda t: t["attrs"]["tech"] == tech, templ_list)
	return render(request, "templates/list.html", {'templ_list': templ_list, "tech": tech, "techs_dict": techs_dict})

@wrap_rpc
def info(api, request, res_id):
	template = api.resource_info(res_id)
	return render(request, "templates/info.html", {"template": template, "techs_dict": techs_dict})

@wrap_rpc
def add(api, request, tech=None):
	message_after = '<h2>Tracker URL</h2>	The torrent tracker of this backend is:	<pre><tt>'+serverInfo()["TEMPLATE_TRACKER_URL"]+'</tt></pre>'
	if request.method == 'POST':
		form = AddTemplateForm(request.POST, request.FILES)
		if form.is_valid():
			formData = form.cleaned_data
			creation_date = str(formData['creation_date'])
			f = request.FILES['torrentfile']
			torrent_data = base64.b64encode(f.read())
			attrs = {'name':formData['name'],
						'label':formData['label'],
						'subtype':formData['subtype'],
						'preference':formData['preference'],
						'tech': formData['tech'],
						'restricted': formData['restricted'],
						'torrent_data':torrent_data,
						'description':formData['description'],
						'nlXTP_installed':formData['nlXTP_installed'],
						'creation_date':creation_date,
						'icon':formData['icon'],
						'show_as_common':formData['show_as_common']}
			if formData['tech'] == "kvmqm":
				attrs['kblang'] = formData['kblang']
			res = api.resource_create('template',attrs)
			return HttpResponseRedirect(reverse("tomato.template.info", kwargs={"res_id": res["id"]}))
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Template", 'message_after':message_after})
	else:
		form = AddTemplateForm()
		if tech:
			form.fields['tech'].initial = tech
		return render(request, "form.html", {'form': form, "heading":"Add Template", 'hide_errors':True, 'message_after':message_after})

@wrap_rpc
def remove(api, request, res_id=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.resource_remove(res_id)
			return HttpResponseRedirect(reverse("template_list"))
	form = RemoveConfirmForm.build(reverse("tomato.template.remove", kwargs={"res_id": res_id}))
	res = api.resource_info(res_id)
	return render(request, "form.html", {"heading": "Remove Template", "message_before": "Are you sure you want to remove the template '"+res["attrs"]["name"]+"'?", 'form': form})	

@wrap_rpc
def edit_torrent(api, request, res_id=None):
	if request.method=='POST':
		form = ChangeTemplateTorrentForm(res_id, request.POST,request.FILES)
		if form.is_valid():
			formData = form.cleaned_data
			f = request.FILES['torrentfile']
			torrent_data = base64.b64encode(f.read())
			res_info = api.resource_info(formData['res_id'])
			creation_date = str(formData['creation_date'])
			UserError.check(res_info['type'] == 'template',UserError.INVALID_RESOURCE_TYPE,"This resource is not a template", data={'id':formData['res_id']})
			api.resource_modify(formData["res_id"],{'torrent_data':torrent_data,
													'creation_date':creation_date})
			return HttpResponseRedirect(reverse("tomato.template.info", kwargs={"res_id": res_id}))
		label = request.POST["label"]
		UserError.check(label, UserError.INVALID_DATA, "Form transmission failed.")
		return render(request, "form.html", {'form': form, "heading":"Edit Template Torrent for '"+label+"' ("+request.POST["tech"]+")"})
	else:
		UserError.check(res_id, UserError.INVALID_DATA, "No resource specified.")
		res_info = api.resource_info(res_id)
		form = ChangeTemplateTorrentForm(res_id, {'res_id': res_id})
		return render(request, "form.html", {'form': form, "heading":"Edit Template Torrent for '"+res_info['attrs']['label']+"' ("+res_info['attrs']['tech']+")"})
		

@wrap_rpc
def edit(api, request, res_id=None):
	if request.method=='POST':
		form = EditTemplateForm(res_id, (api.resource_info(res_id)['attrs']['tech']=="kvmqm"), request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			creation_date = str(formData['creation_date'])
			res_inf = api.resource_info(res_id)
			UserError.check(res_inf['type'] == 'template',UserError.INVALID_RESOURCE_TYPE,"This resource is not a template", data={'id':formData['res_id']})
			attrs = {'label':formData['label'],
						'restricted': formData['restricted'],
						'subtype':formData['subtype'],
						'preference':formData['preference'],
						'description':formData['description'],
						'creation_date':creation_date,
						'nlXTP_installed':formData['nlXTP_installed'],
						'icon':formData['icon'],
						'show_as_common':formData['show_as_common']}
			if res_inf['attrs']['tech'] == "kvmqm":
				attrs['kblang'] = formData['kblang']
			api.resource_modify(res_id,attrs)
			return HttpResponseRedirect(reverse("tomato.template.info", kwargs={"res_id": res_id}))
		label = request.POST["label"]
		UserError.check(label, UserError.INVALID_DATA, "Form transmission failed.")
		return render(request, "form.html", {'label': label, 'form': form, "heading":"Edit Template Data for '"+label+"' ("+request.POST['tech']+")"})
	else:
		UserError.check(res_id, UserError.INVALID_DATA, "No resource specified.")
		res_info = api.resource_info(res_id)
		origData = res_info['attrs']
		origData['res_id'] = res_id
		form = EditTemplateForm(res_id, (origData['tech']=="kvmqm"), origData)
		return render(request, "form.html", {'label': res_info['attrs']['label'], 'form': form, "heading":"Edit Template Data for '"+res_info['attrs']['label']+"' ("+res_info['attrs']['tech']+")"})
		
@wrap_rpc
def download_torrent(api, request, res_id):
	res_inf = api.resource_info(res_id, include_torrent_data=True)
	UserError.check(res_inf['type'] == 'template',UserError.INVALID_RESOURCE_TYPE,"This resource is not a template", data={'id':res_inf['id']})
	UserError.check('torrent_data' in res_inf['attrs'],UserError.NO_DATA_AVAILABLE,"This template does not have a torrent file", data={'id':res_inf['id']})
	tdata = base64.b64decode(res_inf['attrs']['torrent_data'])
	filename = re.sub('[^\w\-_\. :]', '_', res_inf['attrs']['name'] ) + ".torrent"
	response = HttpResponse(tdata, content_type="application/json")
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response
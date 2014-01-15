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
import base64
from lib import wrap_rpc
from admin_common import RemoveResourceForm, help_url, BootstrapForm
import datetime

from tomato.crispy_forms.helper import FormHelper
from tomato.crispy_forms.layout import Layout, Fieldset
from tomato.crispy_forms.bootstrap import StrictButton, FormActions
from django.core.urlresolvers import reverse


class TemplateForm(BootstrapForm):
	label = forms.CharField(max_length=255, help_text="The displayed label for this profile")
	subtype = forms.CharField(max_length=255, required=False)
	description = forms.CharField(widget = forms.Textarea, required=False)
	preference = forms.IntegerField(label="Preference", help_text="The profile with the highest preference will be the default profile. An integer number.")
	restricted = forms.BooleanField(label="Restricted", help_text="Restrict usage of this template to administrators", required=False)
	nlXTP_installed = forms.BooleanField(label="nlXTP Guest Modules installed", help_text="Ignore this for Repy devices.", required=False)
	creation_date = forms.DateField(required=False,widget=forms.TextInput(attrs={'class': 'datepicker'}));
	def __init__(self, *args, **kwargs):
		super(TemplateForm, self).__init__(*args, **kwargs)
		self.fields['creation_date'].initial=datetime.date.today()
	
class AddTemplateForm(TemplateForm):
	torrentfile  = forms.FileField(label="Torrent:", help_text='<a href="'+help_url()+'/admin/torrents" target="_blank">Help</a>')
	name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all profiles. Cannot be changed. Not displayed.")
	tech = forms.CharField(max_length=255,widget = forms.widgets.Select(choices=[('kvmqm','kvmqm'),('openvz','openvz'),('repy','repy')]))
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
            'restricted',
            'nlXTP_installed',
            'creation_date',
            'torrentfile',
            FormActions(
                StrictButton('Add', css_class='btn-primary', type="submit"),
                StrictButton('Cancel', css_class='btn-default backbutton')
            )
        )
	
class EditTemplateForm(TemplateForm):
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	def __init__(self, *args, **kwargs):
		super(EditTemplateForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(edit_data)
		self.helper.layout = Layout(
            'res_id',
            'label',
            'subtype',
            'description',
            'preference',
            'restricted',
            'nlXTP_installed',
            'creation_date',
            FormActions(
                StrictButton('Save', css_class='btn-primary', type="submit"),
                StrictButton('Cancel', css_class='btn-default backbutton')
            )
        )
	
class ChangeTemplateTorrentForm(BootstrapForm):
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	creation_date = forms.DateField(required=False,widget=forms.TextInput(attrs={'class': 'datepicker'}))
	torrentfile  = forms.FileField(label="Torrent containing image:", help_text='See the <a href="https://tomato.readthedocs.org/en/latest/docs/templates/" target="_blank">template documentation about the torrent file.</a> for more information')	
	def __init__(self, *args, **kwargs):
		super(EditTemplateForm, self).__init__(*args, **kwargs)
		self.fields['creation_date'].initial=datetime.date.today()
		self.helper.form_action = reverse(edit_torrent)
		self.helper.layout = Layout(
            'res_id',
            'creation_date',
            'torrentfile',
            FormActions(
                StrictButton('Save', css_class='btn-primary', type="submit"),
                StrictButton('Cancel', css_class='btn-default backbutton')
            )
        )

@wrap_rpc
def list(api, request):
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
	return render(request, "admin/device_templates/index.html", {'templ_list': templ_list})


@wrap_rpc
def add(api, request):
	message_after = '<h2>Tracker URL</h2>	The torrent tracker of this backend is:	<pre><tt>'+api.server_info()["TEMPLATE_TRACKER_URL"]+'</tt></pre>'
	if request.method == 'POST':
		form = AddTemplateForm(request.POST, request.FILES)
		if form.is_valid():
			formData = form.cleaned_data
			creation_date = str(formData['creation_date'])
			f = request.FILES['torrentfile']
			torrent_data = base64.b64encode(f.read())
			api.resource_create('template',{'name':formData['name'],
											'label':formData['label'],
											'subtype':formData['subtype'],
											'preference':formData['preference'],
											'tech': formData['tech'],
											'restricted': formData['restricted'],
											'torrent_data':torrent_data,
											'description':formData['description'],
											'nlXTP_installed':formData['nlXTP_installed'],
											'creation_date':creation_date})
			return render(request, "admin/device_templates/add_success.html", {'label': formData['label']})
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Template", 'message_after':message_after})
	else:
		form = AddTemplateForm()
		return render(request, "form.html", {'form': form, "heading":"Add Template", 'hide_errors':True, 'message_after':message_after})


@wrap_rpc
def remove(api, request, res_id=None):
	if request.method == 'POST':
		form = RemoveResourceForm(remove,request.POST)
		if form.is_valid():
			res_id = form.cleaned_data["res_id"]
			if api.resource_info(res_id) and api.resource_info(res_id)['type'] == 'template':
				label = api.resource_info(res_id)['attrs']['label']
				api.resource_remove(res_id)
				return render(request, "admin/device_templates/remove_success.html", {'label':label})
			else:
				return render(request, "main/error.html",{'type':'invalid id','text':'There is no template with id '+res_id})
		else:
			if not res_id:
				res_id = request.POST['res_id']
			if res_id:
				form = RemoveResourceForm(remove)
				form.fields["res_id"].initial = res_id
				return render(request, "form.html", {'heading':"Remove Template", "message_before":"Are you sure you want to remove the template" + api.resource_info(res_id)['attrs']['label'] + "?", 'form': form})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	else:
		if res_id:
			form = RemoveResourceForm(remove)
			form.fields["res_id"].initial = res_id
			return render(request, "form.html", {'heading':"Remove Template", "message_before":"Are you sure you want to remove the template" + api.resource_info(res_id)['attrs']['label'] + "?", 'form': form})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})
	

@wrap_rpc
def edit(api, request, res_id=None):
	if res_id:
		return render(request, "admin/device_templates/edit_unspecified.html",{'res_id':res_id,'label':api.resource_info(request.GET['id'])['attrs']['label']})
	else:
		return render(request, "main/error.html",{'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})

@wrap_rpc
def edit_torrent(api, request, res_id=None):
	if request.method=='POST':
		form = ChangeTemplateTorrentForm(request.POST,request.FILES)
		if form.is_valid():
			formData = form.cleaned_data
			f = request.FILES['torrentfile']
			torrent_data = base64.b64encode(f.read())
			res_info = api.resource_info(formData['res_id'])
			creation_date = str(formData['creation_date'])
			if res_info['type'] == 'template':
				api.resource_modify(formData["res_id"],{'torrent_data':torrent_data,
														'creation_date':creation_date})
				return render(request, "admin/device_templates/edit_success.html", {'label': res_info['attrs']['label'], 'res_id': formData['res_id'], 'edited_data': True})
			else:
				return render(request, "main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no template.'})
		else:
			label = request.POST["label"]
			if label:
				return render(request, "form.html", {'form': form, "heading":"Edit Template Torrent for '"+label+"' ("+request.POST["tech"]+")"})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	else:
		if res_id:
			res_info = api.resource_info(res_id)
			form = ChangeTemplateTorrentForm({'res_id': res_id})
			return render(request, "form.html", {'form': form, "heading":"Edit Template Torrent for '"+res_info['attrs']['label']+"' ("+res_info['attrs']['tech']+")"})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})


@wrap_rpc
def edit_data(api, request, res_id=None):
	if request.method=='POST':
		form = EditTemplateForm(request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			creation_date = str(formData['creation_date'])
			if api.resource_info(formData['res_id'])['type'] == 'template':
				api.resource_modify(formData["res_id"],{'label':formData['label'],
														'restricted': formData['restricted'],
														'subtype':formData['subtype'],
														'preference':formData['preference'],
														'description':formData['description'],
														'creation_date':creation_date,
														'nlXTP_installed':formData['nlXTP_installed']})
				return render(request, "admin/device_templates/edit_success.html", {'label': formData["label"], 'res_id': formData['res_id'], 'edited_data': True})
			else:
				return render(request, "main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no template.'})
		else:
			label = request.POST["label"]
			if label:
				return render(request, "form.html", {'label': label, 'form': form, "heading":"Edit Template Data for '"+label+"' ("+request.POST['tech']+")"})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	else:
		if res_id:
			res_info = api.resource_info(res_id)
			origData = res_info['attrs']
			origData['res_id'] = res_id
			form = EditTemplateForm(origData)
			return render(request, "form.html", {'label': res_info['attrs']['label'], 'form': form, "heading":"Edit Template Data for '"+res_info['attrs']['label']+"' ("+res_info['attrs']['tech']+")"})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No address specified. Have you followed a valid link?'})


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

from django.http import HttpResponseRedirect
from django import forms
from django.shortcuts import render
from django.core.urlresolvers import reverse

from lib import wrap_rpc
from admin_common import RemoveConfirmForm, BootstrapForm, Buttons
from template import techs_dict,techs_choices

from tomato.crispy_forms.layout import Layout

class ProfileForm(BootstrapForm):
	label = forms.CharField(max_length=255, help_text="The displayed label for this template")
	ram = forms.IntegerField(label="RAM (MB)")
	preference = forms.IntegerField(label="Preference", help_text="Sort profiles in the editor (higher preference first). The profile with highest preference will be the default. Must be an integer number.")
	restricted = forms.BooleanField(label="Restricted", help_text="Restrict usage of this template to administrators", required=False)
	tech = forms.ChoiceField(label="Tech",choices=techs_choices())
	description = forms.CharField(widget = forms.Textarea, required=False)
	def __init__(self, *args, **kwargs):
		super(ProfileForm, self).__init__(*args, **kwargs)
		
class EditProfileForm(ProfileForm):
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	def __init__(self, res_id, *args, **kwargs):
		super(EditProfileForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(edit, kwargs={"res_id": res_id})


class EditOpenVZForm(EditProfileForm):
	cpus = forms.FloatField(label = "number of CPUs")
	diskspace = forms.IntegerField(label="Disk Space (MB)")
	def __init__(self, res_id, *args, **kwargs):
		super(EditOpenVZForm, self).__init__(res_id, *args, **kwargs)
		self.helper.layout = Layout(
			'res_id',
			'tech',
			'label',
			'cpus',
			'diskspace',
			'ram',
			'restricted',
			'preference',
			'description',
			Buttons.cancel_save
		)

class EditRePyForm(EditProfileForm):
	cpus = forms.FloatField(label = "number of CPUs")
	def __init__(self, res_id, *args, **kwargs):
		super(EditRePyForm, self).__init__(res_id, *args, **kwargs)
		self.helper.layout = Layout(
			'res_id',
			'tech',
			'label',
			'cpus',
			'ram',
			'restricted',
			'preference',
			'description',
			Buttons.cancel_save
		)

class EditKVMqmForm(EditProfileForm):
	diskspace = forms.IntegerField(label="Disk Space (MB)")
	cpus = forms.FloatField(label = "number of CPUs")
	def __init__(self, res_id, *args, **kwargs):
		super(EditKVMqmForm, self).__init__(res_id, *args, **kwargs)
		self.helper.layout = Layout(
			'res_id',
			'tech',
			'label',
			'diskspace',
			'cpus',
			'ram',
			'restricted',
			'preference',
			'description',
			Buttons.cancel_save
		)
	
	
class AddProfileForm(ProfileForm):
	name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all templates of the same tech. Cannot be changed. Not displayed.")
	diskspace = forms.IntegerField(label="Disk Space (MB)", required = False, help_text="only OpenVZ and KVMqm")
	cpus = forms.FloatField(label="number of CPUs", help_text="Repy, OpenVZ: float number; KVMqm: integer number")
	def __init__(self, *args, **kwargs):
		super(AddProfileForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
			'tech',
			'name',
			'label',
			'diskspace',
			'cpus',
			'ram',
			'restricted',
			'preference',
			'description',
			Buttons.cancel_add
		)

@wrap_rpc
def list(api, request, tech):
	profile_list = api.resource_list('profile')
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
	profile_list.sort(_cmp)
	if tech:
		profile_list = filter(lambda t: t["attrs"]["tech"] == tech, profile_list)
	return render(request, "profile/list.html", {'profile_list': profile_list, 'tech': tech, 'techs_dict': techs_dict})

@wrap_rpc
def info(api, request, res_id):
	profile = api.resource_info(res_id)
	return render(request, "profile/info.html", {"profile": profile, "techs_dict": techs_dict})

@wrap_rpc
def add(api, request, tech=None):
	if request.method == 'POST':
		form = AddProfileForm(request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			data={'tech': formData['tech'],
				 'name': formData['name'],
				 'ram':formData['ram'],
				 'label':formData['label'],
				 'preference':formData['preference'],
				 'description':formData['description']}
			if formData.get('diskspace') and (formData['tech'] != 'repy'):
				data['diskspace'] = formData['diskspace']
			if formData.get('cpus'):
				data['cpus'] = formData['cpus'] 
			if formData['restricted']:
				data['restricted'] = formData['restricted']
			else:
				data['restricted'] = False
			res = api.resource_create('profile',data)
			return HttpResponseRedirect(reverse("tomato.profile.info", kwargs={"res_id": res["id"]}))
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Device Profile"})
	else:
		form = AddProfileForm()
		if tech:
			form.fields['tech'].initial = tech
		return render(request, "form.html", {'form': form, "heading":"Add Device Profile"})

@wrap_rpc
def remove(api, request, res_id=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.resource_remove(res_id)
			return HttpResponseRedirect(reverse("profile_list"))
	form = RemoveConfirmForm.build(reverse("tomato.profile.remove", kwargs={"res_id": res_id}))
	res = api.resource_info(res_id)
	return render(request, "form.html", {"heading": "Remove Device Profile", "message_before": "Are you sure you want to remove the device profile '"+res["attrs"]["name"]+"'?", 'form': form})	
	
@wrap_rpc
def edit(api, request, res_id=None):
	if request.method=='POST':
		tech = request.POST['tech']
		if tech == 'repy':
			form = EditRePyForm(res_id, request.POST)
		elif tech == 'openvz':
			form = EditOpenVZForm(res_id, request.POST)
		else:
			form = EditKVMqmForm(res_id, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			data={'cpus':formData['cpus'],
				 'ram':formData['ram'],
				 'label':formData['label'],
				 'preference':formData['preference'],
				 'description':formData['description']}
			if (formData['tech'] != 'repy'):
				data['diskspace'] = formData['diskspace']
			if formData['restricted']:
				data['restricted'] = formData['restricted']
			else:
				data['restricted'] = False
			
			if api.resource_info(formData['res_id'])['type'] == 'profile':
				api.resource_modify(formData["res_id"],data)
				return HttpResponseRedirect(reverse("tomato.profile.info", kwargs={"res_id": res_id}))
			else:
				return render(request, "main/error.html",{'type':'invalid id','text':'The resource with id '+formData['res_id']+' is no repy device profile.'})
		else:
			label = request.POST["label"]
			if label:
				return render(request, "form.html", {'form': form, "heading":"Edit Device Profile '"+label+"'"})
			else:
				return render(request, "main/error.html",{'type':'Transmission Error','text':'There was a problem transmitting your data.'})
	else:
		if res_id:
			res_info = api.resource_info(res_id)
			origData = res_info['attrs']
			origData['res_id'] = res_id
			if origData['tech'] == 'repy':
				form = EditRePyForm(res_id, origData)
			elif origData['tech'] == 'openvz':
				form = EditOpenVZForm(res_id, origData)
			else:
				form = EditKVMqmForm(res_id, origData)
			return render(request, "form.html", {'form': form, "heading":"Edit "+res_info['attrs']['tech']+" Device Profile '"+res_info['attrs']['label']+"'"})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})

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
from admin_common import RemoveConfirmForm, BootstrapForm

from tomato.crispy_forms.helper import FormHelper
from tomato.crispy_forms.layout import Layout, Fieldset
from tomato.crispy_forms.bootstrap import StrictButton, FormActions

class ProfileForm(BootstrapForm):
	label = forms.CharField(max_length=255, help_text="The displayed label for this template")
	ram = forms.IntegerField(label="RAM (MB)")
	preference = forms.IntegerField(label="Preference", help_text="The profile with the highest preference will be the default profile. An integer number.")
	restricted = forms.BooleanField(label="Restricted", help_text="Restrict usage of this template to administrators", required=False)
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	tech = forms.CharField(max_length=50, widget=forms.HiddenInput)
	description = forms.CharField(widget = forms.Textarea, required=False)
	def __init__(self, *args, **kwargs):
		super(ProfileForm, self).__init__(*args, **kwargs)
		
class EditProfileForm(ProfileForm):
	def __init__(self, *args, **kwargs):
		super(EditProfileForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(edit)


class EditOpenVZForm(EditProfileForm):
	diskspace = forms.IntegerField(label="Disk Space (MB)")
	def __init__(self, *args, **kwargs):
		super(EditOpenVZForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(
			'res_id',
			'tech',
			'label',
			'diskspace',
			'ram',
			'restricted',
			'preference',
			'description',
			FormActions(
				StrictButton('Save', css_class='btn-primary', type="submit"),
				StrictButton('Cancel', css_class='btn-default backbutton')
			)
		)

class EditRePyForm(EditProfileForm):
	cpus = forms.FloatField(label = "number of CPUs")
	def __init__(self, *args, **kwargs):
		super(EditRePyForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(
			'res_id',
			'tech',
			'label',
			'cpus',
			'ram',
			'restricted',
			'preference',
			'description',
			FormActions(
				StrictButton('Save', css_class='btn-primary', type="submit"),
				StrictButton('Cancel', css_class='btn-default backbutton')
			)
		)

class EditKVMqmForm(EditProfileForm):
	diskspace = forms.IntegerField(label="Disk Space (MB)")
	cpus = forms.FloatField(label = "number of CPUs")
	def __init__(self, *args, **kwargs):
		super(EditKVMqmForm, self).__init__(*args, **kwargs)
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
			FormActions(
				StrictButton('Save', css_class='btn-primary', type="submit"),
				StrictButton('Cancel', css_class='btn-default backbutton')
			)
		)
	
	
class AddProfileForm(ProfileForm):
	tech = forms.ChoiceField(label="Tech",choices=[('kvmqm','kvmqm'), ('openvz','openvz'), ('repy','repy')])
	name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all templates of the same tech. Cannot be changed. Not displayed.")
	diskspace = forms.IntegerField(label="Disk Space (MB)", required = False, help_text="only OpenVZ and KVMqm")
	cpus = forms.IntegerField(label="number of CPUs", required = False, help_text="Repy, OpenVZ: float number; KVMqm: integer number")
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
			FormActions(
				StrictButton('Save', css_class='btn-primary', type="submit"),
				StrictButton('Cancel', css_class='btn-default backbutton')
			)
		)

@wrap_rpc
def list(api, request):
	profile_list = api.resource_list('profile')
	return render(request, "admin/device_profile/index.html", {'profile_list': profile_list})


@wrap_rpc
def add(api, request):
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
			if formData['diskspace'] and (formData['tech'] != 'repy'):
				data['diskspace'] = formData['diskspace']
			if formData['cpus']:
				data['cpus'] = formData['cpus'] 
			if formData['restricted']:
				data['restricted'] = formData['restricted']
			else:
				data['restricted'] = False
			
			api.resource_create('profile',data)
		   
			return render(request, "admin/device_profile/add_success.html", {'label': formData["label"],'tech':data['tech']})
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Device Profile"})
	else:
		form = AddProfileForm
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
			form = EditRePyForm(request.POST)
		else:
			if tech == 'openvz':
				form = EditOpenVZForm(request.POST)
			else:
				form = EditKVMqmForm(request.POST)
		
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
				return render(request, "admin/device_profile/edit_success.html", {'label': formData["label"],'tech':'repy'})
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
				form = EditRePyForm(origData)
			else:
				if origData['tech'] == 'openvz':
					form = EditOpenVZForm(origData)
				else:
					form = EditKVMqmForm(origData)
			return render(request, "form.html", {'form': form, "heading":"Edit "+res_info['attrs']['tech']+" Device Profile '"+res_info['attrs']['label']+"'"})
		else:
			return render(request, "main/error.html",{'type':'not enough parameters','text':'No resource specified. Have you followed a valid link?'})

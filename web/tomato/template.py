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
from lib.constants import TypeName

from tomato.crispy_forms.layout import Layout
from django.core.urlresolvers import reverse

from lib.error import UserError #@UnresolvedImport

types = [{"name": t, "label": TypeName.ONSCREEN.get(t, t)} for t in [TypeName.FULL_VIRTUALIZATION, TypeName.CONTAINER_VIRTUALIZATION, TypeName.REPY]]

types_dict = dict([(t["name"], t["label"]) for t in types])

def types_choices():
	tlist = [(t["name"], t["label"]) for t in types]
	return append_empty_choice(tlist)

kblang_options = [
	("en-us", "English (US)"),
	("en-gb", "English (GB)"),
	("de", "German"),
	("fr", "French"),
	("ja", "Japanese")
]

def dateToTimestamp(date):
	td = date - datetime.date(1970, 1, 1)
	return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

class TemplateForm(BootstrapForm):
	label = forms.CharField(max_length=255, help_text="The displayed label for this template")
	subtype = forms.CharField(max_length=255, required=False)
	description = forms.CharField(widget = forms.Textarea, required=False)
	preference = forms.IntegerField(label="Preference", help_text="Sort templates in the editor (higher preference first). The template with highest preference will be the default. Must be an integer number.")
	restricted = forms.BooleanField(label="Restricted", help_text="Restrict usage of this template to administrators", required=False)
	nlXTP_installed = forms.BooleanField(label="nlXTP Guest Modules installed", help_text="Ignore this for Repy devices.", required=False)
	creation_date = forms.DateField(required=False,widget=forms.TextInput(attrs={'class': 'datepicker'}))
	show_as_common = forms.BooleanField(label="Show in Common Elements", help_text="Show this template in the common elements section in the editor", required=False)
	icon = forms.URLField(label="Icon", help_text="URL of a 32x32 icon to use for elements of this template, leave empty to use the default icon", required=False)
	kblang = forms.CharField(max_length=50,label="Keyboard Layout",widget = forms.widgets.Select(choices=kblang_options), help_text="Only for full-virtualization templates", required=False)
	urls = forms.CharField(widget = forms.Textarea, required=True, help_text="URLs that point to the template's image file. Enter one or more URLs; one URL per line.")
	def __init__(self, *args, **kwargs):
		super(TemplateForm, self).__init__(*args, **kwargs)
		self.fields['creation_date'].initial=datetime.date.today()
		self.fields['kblang'].initial="en_US"
	
class AddTemplateForm(TemplateForm):
	name = forms.CharField(max_length=50,label="Internal Name", help_text="Must be unique for all profiles. Cannot be changed. Not displayed.")
	type = forms.CharField(max_length=255,widget = forms.widgets.Select(choices=types_choices()))
	def __init__(self, *args, **kwargs):
		super(AddTemplateForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(add)
		self.helper.layout = Layout(
            'name',
            'label',
            'subtype',
            'description',
            'type',
            'preference',
            'show_as_common',
            'restricted',
            'nlXTP_installed',
            'kblang',
            'icon',
            'creation_date',
			'urls',
            Buttons.cancel_add
        )
	def is_valid(self):
		valid = super(AddTemplateForm, self).is_valid()
		if not valid:
			return valid
		if self.cleaned_data['type'] == TypeName.FULL_VIRTUALIZATION:
			valid = (self.cleaned_data['kblang'] is not None)
		return valid
	
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
				'urls',
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
				'urls',
				Buttons.cancel_save
	        )
	
@wrap_rpc
def list(api, request, type):
	templ_list = api.template_list()
	def _cmp(a, b):
		c = cmp(a["type"], b["type"])
		if c:
			return c
		c = -cmp(a["preference"], b["preference"])
		if c:
			return c
		return cmp(a["name"], b["name"])
	templ_list.sort(_cmp)
	if type:
		templ_list = filter(lambda t: t["type"] == type, templ_list)
	return render(request, "templates/list.html", {'templ_list': templ_list, "type": type, "types_dict": types_dict})

@wrap_rpc
def info(api, request, res_id):
	template = api.template_info(res_id)
	return render(request, "templates/info.html", {"template": template, "types_dict": types_dict})

@wrap_rpc
def add(api, request, type=None):
	if request.method == 'POST':
		form = AddTemplateForm(request.POST, request.FILES)
		if form.is_valid():
			formData = form.cleaned_data
			creation_date = formData['creation_date']
			attrs = {	'label':formData['label'],
						'subtype':formData['subtype'],
						'preference':formData['preference'],
						'restricted': formData['restricted'],
						'description':formData['description'],
						'nlXTP_installed':formData['nlXTP_installed'],
						'creation_date':dateToTimestamp(creation_date) if creation_date else None,
						'icon':formData['icon'],
						'show_as_common':formData['show_as_common'],
						'urls': filter(lambda x: x, formData['urls'].splitlines())}
			if formData['type'] == TypeName.FULL_VIRTUALIZATION:
				attrs['kblang'] = formData['kblang']
			res = api.template_create(formData['type'], formData['name'], attrs)
			return HttpResponseRedirect(reverse("tomato.template.info", kwargs={"res_id": res["id"]}))
		else:
			return render(request, "form.html", {'form': form, "heading":"Add Template"})
	else:
		form = AddTemplateForm()
		if type:
			form.fields['type'].initial = type
		return render(request, "form.html", {'form': form, "heading":"Add Template", 'hide_errors':True})

@wrap_rpc
def remove(api, request, res_id=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.template_remove(res_id)
			return HttpResponseRedirect(reverse("template_list"))
	form = RemoveConfirmForm.build(reverse("tomato.template.remove", kwargs={"res_id": res_id}))
	res = api.template_info(res_id)
	return render(request, "form.html", {"heading": "Remove Template", "message_before": "Are you sure you want to remove the template '"+res["name"]+"'?", 'form': form})

@wrap_rpc
def edit(api, request, res_id=None):
	res_inf = api.template_info(res_id)
	if request.method=='POST':
		form = EditTemplateForm(res_id, res_inf['type']== TypeName.FULL_VIRTUALIZATION, request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			creation_date = formData['creation_date']
			attrs = {'label':formData['label'],
						'restricted': formData['restricted'],
						'subtype':formData['subtype'],
						'preference':formData['preference'],
						'description':formData['description'],
						'creation_date':dateToTimestamp(creation_date) if creation_date else None,
						'nlXTP_installed':formData['nlXTP_installed'],
						'icon':formData['icon'],
						'show_as_common':formData['show_as_common'],
						'urls': filter(lambda x: x, formData['urls'].splitlines())}
			if res_inf['type'] == TypeName.FULL_VIRTUALIZATION:
				attrs['kblang'] = formData['kblang']
			api.template_modify(res_id,attrs)
			return HttpResponseRedirect(reverse("tomato.template.info", kwargs={"res_id": res_id}))
		label = request.POST["label"]
		UserError.check(label, UserError.INVALID_DATA, "Form transmission failed.")
		return render(request, "form.html", {'label': label, 'form': form, "heading":"Edit Template Data for '"+label+"' ("+res_inf['type']+")"})
	else:
		UserError.check(res_id, UserError.INVALID_DATA, "No resource specified.")
		res_inf['res_id'] = res_id
		res_inf['creation_date'] = datetime.date.fromtimestamp(float(res_inf['creation_date'] or "0.0"))
		res_inf['urls'] = "\n".join(res_inf['urls'])
		form = EditTemplateForm(res_id, (res_inf['type']==TypeName.FULL_VIRTUALIZATION), res_inf)
		return render(request, "form.html", {'label': res_inf['label'], 'form': form, "heading":"Edit Template Data for '"+str(res_inf['label'])+"' ("+res_inf['type']+")"})
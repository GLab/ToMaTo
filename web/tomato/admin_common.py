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

from django import forms
from lib import getapi

from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import FormActions, StrictButton
from django.core.urlresolvers import reverse

from tomato.crispy_forms.helper import FormHelper
	
class BootstrapForm(forms.Form):
	def __init__(self, *args, **kwargs):
		super(BootstrapForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_class = 'form-horizontal'
		self.helper.form_method = "post"
		self.helper.label_class = 'col-lg-4 col-sm-4'
		self.helper.field_class = 'col-lg-6 col-sm-8'

class RemoveResourceForm(BootstrapForm):
	res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
	def __init__(self, remove_fn, *args, **kwargs):
		super(RemoveResourceForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(remove_fn)
		self.helper.layout = Layout(
			'res_id',
			FormActions(
				StrictButton('Confirm', css_class='btn-primary', type="submit"),
				StrictButton('Cancel', css_class='btn-default backbutton')
			)
		)

class RemoveConfirmForm(BootstrapForm):
	def __init__(self, *args, **kwargs):
		super(RemoveConfirmForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(
			FormActions(
				StrictButton('<span class="glyphicon glyphicon-remove"></span> Cancel', css_class='btn-danger backbutton'),
				StrictButton('<span class="glyphicon glyphicon-trash"></span> Remove', css_class='btn-warning', type="submit")
			)
		)
	@classmethod
	def build(cls, action):
		obj = cls()
		obj.helper.form_action = action
		return obj
		

def organization_name_list(api):
	l = api.organization_list()
	res = []
	for organization in l:
		res.append((organization["name"],organization["description"] or organization["name"]))
	res.sort()
	return res

def help_url():
	return getapi().server_info()["external_urls"]['help']
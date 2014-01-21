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
from lib import serverInfo

from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import FormActions, StrictButton

from tomato.crispy_forms.helper import FormHelper

class FixedText(forms.HiddenInput):
	is_hidden = False
	def render(self, name, value, attrs=None):
		return forms.HiddenInput.render(self, name, value) + value

class FixedList(forms.MultipleHiddenInput):
	is_hidden = False
	def render(self, name, value, attrs=None):
		return forms.MultipleHiddenInput.render(self, name, value) + ", ".join(value)
	def value_from_datadict(self, data, files, name):
		value = forms.MultipleHiddenInput.value_from_datadict(self, data, files, name)
		# fix django bug
		if isinstance(value, list):
			return value
		else:
			return [value]
	
class BootstrapForm(forms.Form):
	def __init__(self, *args, **kwargs):
		super(BootstrapForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_class = 'form-horizontal'
		self.helper.form_method = "post"
		self.helper.label_class = 'col-lg-4 col-sm-4'
		self.helper.field_class = 'col-lg-6 col-sm-8'

def createButtons(back_icon="remove", back_label="Cancel", back_class="btn-danger backbutton", icon="ok", label="Save", class_="btn-success"):
	return FormActions(
		StrictButton('<span class="glyphicon glyphicon-%s"></span> %s' % (back_icon, back_label), css_class=back_class),
		StrictButton('<span class="glyphicon glyphicon-%s"></span> %s' % (icon, label), css_class=class_, type="submit"),
		css_class="col-sm-offset-4"
	)
	
class Buttons:
	@staticmethod
	def default(**kwargs):
		return createButtons(**kwargs)
	cancel_save = createButtons()
	cancel_add = createButtons(label="Add")
	cancel_remove =	createButtons(icon="trash", label="Remove", class_="btn-warning")

class RemoveConfirmForm(BootstrapForm):
	def __init__(self, *args, **kwargs):
		super(RemoveConfirmForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(Buttons.cancel_remove)
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
	return serverInfo()["external_urls"]['help']

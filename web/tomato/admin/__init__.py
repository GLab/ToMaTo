# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2014 Integrated Communication Systems Lab, University of Kaiserslautern
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

import copy

from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render

from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import FormActions, StrictButton
from tomato.crispy_forms.helper import FormHelper

from ..lib.error import UserError  # @UnresolvedImport
from django.template.defaultfilters import title


# helper functions
def append_empty_choice(choicelist):
	res = list(choicelist)
	res.insert(0, ("", "Please Select:"))
	return res


def organization_name_list(api):
	l = api.organization_list()
	res = []
	for organization in l:
		res.append((organization["name"], organization["label"] or organization["name"]))
	res.sort()
	return res


def site_name_list(api):
	l = api.site_list()
	res = []
	for site in l:
		res.append((site["name"], site["label"] or site["name"]))
	res.sort()
	return res


# form classes

def createButtons(back_icon="remove", back_label="Cancel", back_class="btn-danger backbutton", icon="ok", label="Save",
		class_="btn-success"):
	return FormActions(
		StrictButton('<span class="glyphicon glyphicon-%s"></span> %s' % (back_icon, back_label), css_class=back_class),
		StrictButton('<span class="glyphicon glyphicon-%s"></span> %s' % (icon, label), css_class=class_,
			type="submit"),
		css_class="col-sm-offset-4"
	)


class Buttons:
	@staticmethod
	def default(**kwargs):
		return createButtons(**kwargs)

	cancel_save = createButtons()
	cancel_add = createButtons(label="Add")
	cancel_continue = createButtons(label="Continue")
	cancel_remove = createButtons(icon="trash", label="Remove", class_="btn-warning")


class BootstrapForm(forms.Form):
	helper = FormHelper()

	def __init__(self, *args, **kwargs):
		super(BootstrapForm, self).__init__(*args, **kwargs)
		self.helper.form_class = 'form-horizontal'
		self.helper.form_method = "post"
		self.helper.label_class = 'col-lg-4 col-sm-4'
		self.helper.field_class = 'col-lg-6 col-sm-8'


class RenderableForm(BootstrapForm):
	title = "Untitled Form"
	message = None
	message_after = None

	def __init__(self, *args, **kwargs):
		super(RenderableForm, self).__init__(*args, **kwargs)

	def create_response(self, request):
		args = {'form': self, "heading": self.title}
		if self.message is not None:
			args['message_before'] = self.message
		if self.message_after is not None:
			args['message_after'] = self.message_after
		return render(request, "form.html", args)

class AddEditForm(RenderableForm):
	def __init__(self, data=None, *args, **kwargs):
		super(AddEditForm, self).__init__(data=data, *args, **kwargs)
		if data is not None:
			self.title = self.title % data
			if self.message is not None:
				self.message = self.message % data
			if self.message_after is not None:
				self.message_after = self.message_after % data

	def get_optimized_data(self):
		res = self.cleaned_data
		for k, v in res.iteritems():
			if v == "":
				res[k] = None
		return res

class ConfirmForm(RenderableForm):
	buttons = Buttons.cancel_continue
	formaction_haskeys = True

	def __init__(self, name, *args, **kwargs):
		super(ConfirmForm, self).__init__(*args, **kwargs)
		self.helper.layout = Layout(self.buttons)
		self.message = self.message % {'name': name}
		self.title = self.title % {'name': name}

class RemoveConfirmForm(ConfirmForm):
	buttons = Buttons.cancel_remove


# functions

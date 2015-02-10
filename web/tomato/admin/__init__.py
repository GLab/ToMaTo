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

from ..lib.error import UserError #@UnresolvedImport
from django.template.defaultfilters import title


# helper functions
def append_empty_choice(choicelist):
    res = list(choicelist)
    res.insert(0,("","Please Select:"))
    return res

def organization_name_list(api):
    l = api.organization_list()
    res = []
    for organization in l:
        res.append((organization["name"],organization["description"] or organization["name"]))
    res.sort()
    return res

def site_name_list(api):
    l = api.site_list()
    res = []
    for site in l:
        res.append((site["name"],site["description"] or site["name"]))
    res.sort()
    return res







#form classes

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
    cancel_continue = createButtons(label="Continue")
    cancel_remove =    createButtons(icon="trash", label="Remove", class_="btn-warning")

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
        args = {'form': self, "heading":self.title}
        if self.message is not None:
            args['message_before'] = self.message
        if self.message_after is not None:
            args['message_after'] = self.message_after
        return render(request, "form.html", args)
    
class RedirectAfterForm(RenderableForm):
    primary_key = "id"
    redirect_after = None
    redirect_after_key = None
    redirect_after_useargs = True
    redirect_after_targetkey = None
    redirect_after_targetvalue = None
    def __init__(self, *args, **kwargs):
        super(RedirectAfterForm, self).__init__(*args, **kwargs)
        if self.redirect_after_key is None:
            self.redirect_after_key = self.primary_key
        if self.redirect_after_targetkey is None:
            self.redirect_after_targetkey = self.redirect_after_key
    def get_redirect_after(self, redirect_value = None):
        if redirect_value is None:
            if self.redirect_after_targetvalue is not None:
                redirect_value = self.redirect_after_targetvalue
            else:
                redirect_value = self.cleaned_data[self.redirect_after_key]
        kwargs = {}
        if self.redirect_after_useargs:
            kwargs = {self.redirect_after_targetkey:redirect_value}
        return HttpResponseRedirect(reverse(self.redirect_after, kwargs=kwargs))
    
class ActionForm(RedirectAfterForm):
    formaction = None
    formaction_haskeys = True
    formaction_key = None
    formaction_targetkey = None
    formaction_targetvalue = None
    def __init__(self, *args, **kwargs):
        print self.formaction_targetvalue
        super(ActionForm, self).__init__(*args, **kwargs)
        found_form_action = False
        if self.formaction_key is None:
            self.formaction_key = self.primary_key
        if self.formaction_targetkey is None:
            self.formaction_targetkey = self.formaction_key
        if len(args)>0:
            self.title = self.title % args[0]
            if self.message is not None:
                self.message = self.message % args[0]
            if self.message_after is not None:
                self.message_after = self.message_after % args[0]
            if self.primary_key in args[0]:
                if self.formaction_haskeys:
                    target_value = self.formaction_targetvalue
                    if target_value is None:
                        target_value = args[0][self.primary_key]
                    self.helper.form_action = reverse(self.formaction, kwargs={self.formaction_targetkey: target_value})
                else:
                    self.helper.form_action = reverse(self.formaction)
                found_form_action = True
        if (not found_form_action) and self.formaction_haskeys and self.formaction_targetvalue is not None:
            self.helper.form_action = reverse(self.formaction, kwargs={self.formaction_targetkey: self.formaction_targetvalue})
            found_form_action = True
        if not found_form_action:
            if self.is_valid() and self.formaction_haskeys:
                self.helper.form_action = reverse(self.formaction, kwargs={self.formaction_targetkey: self.cleaned_data[self.primary_key]})
            else:
                self.helper.form_action = reverse(self.formaction)
        
            
class InputTransformerForm(ActionForm):
    def __init__(self, data=None, *args, **kwargs):
        data = self.input_values(copy.deepcopy(data))
        super(InputTransformerForm, self).__init__(*args, data=data, **kwargs)
    def input_values(self, formData):
        return formData
    def get_values(self):
        return copy.deepcopy(self.cleaned_data)
    
class AddEditForm(InputTransformerForm):
    def __init__(self, data=None, *args, **kwargs):
        super(AddEditForm, self).__init__(data=data, *args, **kwargs)
        if data is not None:
            self.title = self.title % data
            if self.message is not None:
                self.message = self.message % data
            if self.message_after is not None:
                self.message_after = self.message_after % data

class ConfirmForm(ActionForm):
    buttons = Buttons.cancel_continue
    formaction_haskeys = True
    def __init__(self, name, *args, **kwargs):
        self.formaction_targetvalue = name
        self.redirect_after_targetvalue = name
        super(ConfirmForm, self).__init__(*args, **kwargs)
        self.helper.layout = Layout(self.buttons)
        self.message = self.message % {'name': name}
        self.title = self.title % {'name': name}

class RemoveConfirmForm(ConfirmForm):
    buttons = Buttons.cancel_remove













#functions

def add_function(request, 
                 Form,
                 create_function,
                 formargs=[], formkwargs={},
                 clean_formargs=[], clean_formkwargs={}):
    if request.method == 'POST':
        form = Form(*formargs, data=request.POST, **formkwargs)
        if form.is_valid():
            formData = form.get_values()
            create_values = []
            primary_value = formData[form.primary_key]
            for key in form.create_keys:
                create_values.append(formData[key])
                del formData[key]
            create_function(*create_values,**{'attrs':formData})
            return form.get_redirect_after()
        else:
            return form.create_response(request)
    else:
        clean_formkwargs.update(formkwargs)
        form = Form(*(formargs + clean_formargs), **(clean_formkwargs) )
        return form.create_response(request)



def edit_function(request,
                  Form,
                  modify_function,
                  formargs=[], formkwargs={},
                  clean_formargs=[], clean_formkwargs={},
                  primary_value = None):
    if request.method=='POST':
        form = Form(*formargs, data=request.POST, **formkwargs)
        if form.is_valid():
            formData = form.get_values()
            primary_value = formData[form.primary_key]
            del formData[form.primary_key]
            modify_function(primary_value,formData)
            return form.get_redirect_after()
        if not primary_value:
            primary_value=request.POST[form.primary_key]
        UserError.check(primary_value, UserError.INVALID_DATA, "Form transmission failed.")
        return form.create_response(request)
    else:
        clean_formkwargs.update(formkwargs)
        form = Form(*(formargs + clean_formargs), **(clean_formkwargs) )
        return form.create_response(request)
        


def remove_function(request,
                    Form,
                    delete_function,
                    primary_value,
                    formargs=[], formkwargs={},
                    clean_formargs=[], clean_formkwargs={}):
    if request.method == 'POST':
        form = Form(*formargs, name=primary_value, data=request.POST, **formkwargs)
        if form.is_valid():
            delete_function(primary_value)
            return form.get_redirect_after()
    form = Form(primary_value)
    return form.create_response(request)



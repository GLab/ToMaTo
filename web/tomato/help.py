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

from lib import wrap_rpc

from django import forms
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.template.response import TemplateResponse

from admin_common import BootstrapForm
from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import FormActions, StrictButton
from django.core.urlresolvers import reverse

available_issues = [
                    ('admin', "User Priviliges or General Assistance"),
                    ('host', "Testbed Misbehavior")
                    ]

available_admin_classes = [
                         ('organization', 'Administrators of my organization (use this if you are unsure)'),
                         ('global', 'Global administrators')
                         ]

def help(request, page=""):
    try:
        if page=="":
            return render(request, "help/index.html")
        else:
            return render(request, "help/pages/"+page+".html")
    except TemplateDoesNotExist:
        return TemplateResponse(request,"help/page_not_exist.html", status=404)

class HelpForm(BootstrapForm):
    admin_class = forms.CharField(max_length=50, required=True, widget = forms.widgets.Select(choices=available_admin_classes), initial="organization", label="Who to Contact")
    issue = forms.CharField(max_length=50, required=True, widget = forms.widgets.Select(choices=available_issues), initial="admin")
    subject = forms.CharField(max_length=255, required=True)
    message = forms.CharField(widget = forms.Textarea, label="Description", required=True)
    def __init__(self, *args, **kwargs):
        super(HelpForm, self).__init__(*args, **kwargs)
        self.helper.form_action = reverse(contact_form)
        self.helper.layout = Layout(
            'admin_class',
            'issue',
            'subject',
            'message',
            FormActions(
                StrictButton('Send e-mail', css_class='btn-primary', type="submit"),
                StrictButton('Cancel', css_class='btn-default backbutton')
            )
        )

@wrap_rpc
def contact_form(api, request, subject=None, message=None, global_contact=False, issue=None):
    if request.method == 'POST':
        form = HelpForm( request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            if formData['admin_class'] == 'global':
                formData['global_contact'] = True
            else:
                formData['global_contact'] = False
            api.mailAdmins(formData["subject"],
                           formData['message'],
                           global_contact = formData['global_contact'],
                           issue=formData['issue'])
            return render(request, "help/contact_form_success.html")
        else:
            return render(request, "form.html", {'form': form,"heading":"Contact Administrators"})
    else:
        form = HelpForm()
        if subject:
            form.fields['subject'].initial=subject
        if message:
            form.fields['message'].initial=message
        if global_contact:
            form.fields['admin_class'].initial = "global"
        if issue:
            form.fields['issue'].initial = issue
        return render(request, "form.html", {'form': form,"heading":"Contact Administrators"})
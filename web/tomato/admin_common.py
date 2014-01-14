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

from tomato.crispy_forms.helper import FormHelper

class RemoveResourceForm(forms.Form):
    res_id = forms.CharField(max_length=50, widget=forms.HiddenInput)
    
class BootstrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = "post"
        self.helper.label_class = 'col-lg-4 col-sm-4'
        self.helper.field_class = 'col-lg-6 col-sm-8'
    
def organization_name_list(api):
    l = api.organization_list()
    res = []
    for organization in l:
        res.append((organization["name"],organization["description"] or organization["name"]))
    res.sort()
    return res

def help_url():
    return getapi().external_urls()['help']
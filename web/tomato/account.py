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

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.http import Http404
from django import forms
from django.core.urlresolvers import reverse

from lib import wrap_rpc, getapi, getGuestApi
import xmlrpclib

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
    
class AccountForm(forms.Form):
    name = forms.CharField(label="Account name", max_length=50)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    origin = forms.CharField(label="Origin", widget=forms.HiddenInput, required=False)
    realname = forms.CharField(label="Full name")
    affiliation = forms.CharField()
    email = forms.EmailField()
    flags = forms.MultipleChoiceField(required=False)

class AccountChangeForm(AccountForm):
    def __init__(self, api, data=None):
        AccountForm.__init__(self, data)
        flags = [(f, f) for f in api.account_flags()]
        self.fields["name"].widget = FixedText()
        del self.fields["password"]
        del self.fields["origin"]
        self.fields["flags"].choices = flags
        if "admin" in api.user.get("flags", []):
            self.fields["flags"].widget = forms.widgets.CheckboxSelectMultiple(choices=flags)
        else:
            self.fields["flags"].widget = FixedList()

class AccountRegisterForm(AccountForm):
    def __init__(self, data=None):
        AccountForm.__init__(self, data)
        del self.fields["flags"]
        del self.fields["origin"]

@wrap_rpc
def index(api, request):
    return render_to_response("account/index.html", {'accounts': api.account_list()})

@wrap_rpc
def info(api, request, id=None):
    user = api.user
    if id:
        user = api.account_info(id)
    else:
        id = user["id"]            
    if request.method=='POST':
        form = AccountChangeForm(api, request.REQUEST)
        if form.is_valid():
            data = form.cleaned_data
            if not "admin" in api.user["flags"]:
                del data["flags"]
            del data["name"]
            api.account_modify(id, attrs=data)
            return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": id}))
    else:
        form = AccountChangeForm(api, user)
    return render_to_response("account/info.html", {"account": user, "form": form})
    
def register(request):
    if request.method=='POST':
        form = AccountRegisterForm(request.REQUEST)
        if form.is_valid():
            data = form.cleaned_data
            username = data["name"]
            password = data["password"]
            del data["password"]
            del data["name"]
            api = getGuestApi()
            try:
                api.account_create(username, password, attrs=data)
                request.session["auth"] = "%s:%s" % (username, password)
                return HttpResponseRedirect(reverse("tomato.account.info"))
            except:
                form._errors["name"] = form.error_class(["This name is already taken"])
    else:
        form = AccountRegisterForm() 
    return render_to_response("account/register.html", {"form": form})
    
def info_or_register(request):
    try:
        api = getapi(request)
        if api:
            return HttpResponseRedirect(reverse("tomato.account.info"))
    except:
        import traceback
        traceback.print_exc
        pass
    return HttpResponseRedirect(reverse("tomato.account.register"))
        
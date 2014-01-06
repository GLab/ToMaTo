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
from admin_common import organization_name_list

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
            
class AccountFlagList(FixedList):
    api = None
    def render(self, name, value, attrs=None):
        
        print value
        
        FlagTranslationDict = self.api.account_flags()
        CategoryTranslationDict = {
                                   'manager_user_global':'Global User Management',
                                   'manager_user_orga':'Organization-Internal User Management',
                                   'manager_host_global':'Global Host Management',
                                   'manager_host_orga':'Organization-Internal Host Management',
                                   'user':'User',
                                   'other':'Other'
        }
        categories = self.api.account_flag_categories()
        
        final_string = ""
        isFirst = True
        for cat in categories.keys():
            foundOne = False
            for v in categories[cat]:
                if v in value:
                    if not foundOne:
                        if not isFirst:
                            final_string = final_string + '</ul>'
                        else:
                            isFirst = False
                        final_string = final_string + '<ul><b>' + CategoryTranslationDict.get(cat,cat) + '</b>'
                        foundOne = True
                    final_string = final_string + '<li style="margin-left:20px;">' + FlagTranslationDict.get(v,v) + '</li>'
        if final_string == "":
            final_string = "None"
            
            
        return forms.MultipleHiddenInput.render(self, name, value) + final_string
    
    def __init__(self, api, *args, **kwargs):
        super(AccountFlagList, self).__init__(*args, **kwargs)
        self.api = api
    
class AccountForm(forms.Form):
    name = forms.CharField(label="Account name", max_length=50)
    password = forms.CharField(label="Password", widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label="Password (repeated)", widget=forms.PasswordInput, required=False)
    organization = forms.CharField(max_length=50)
    origin = forms.CharField(label="Origin", widget=forms.HiddenInput, required=False)
    realname = forms.CharField(label="Full name")
    email = forms.EmailField()
    flags = forms.MultipleChoiceField(required=False)
    def __init__(self, api, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.fields["organization"].widget = forms.widgets.Select(choices=organization_name_list(api))
        
    def clean_password(self):
        if self.data.get('password') != self.data.get('password2'):
            raise forms.ValidationError('Passwords are not the same')
        return self.data.get('password')
    
    def clean(self, *args, **kwargs):
        self.clean_password()
        return forms.Form.clean(self, *args, **kwargs)

class AccountChangeForm(AccountForm):
    def __init__(self, api, data=None):
        AccountForm.__init__(self, api, data)
        flags = api.account_flags().items()
        self.fields["name"].widget = FixedText()
        del self.fields["origin"]
        self.fields["flags"].choices = flags
        if api.user.isAdmin(data["organization"]):
            self.fields["flags"].widget = forms.widgets.CheckboxSelectMultiple(choices=flags)
        else:
            self.fields["flags"].widget = AccountFlagList(api)
            

class AccountRegisterForm(AccountForm):
    aup = forms.BooleanField(label="", required=True)
    
    def __init__(self, api, data=None):
        AccountForm.__init__(self, api, data)
        self.fields["password"].required = True
        del self.fields["flags"]
        del self.fields["origin"]
        self.fields['aup'].help_text = 'I accept the <a href="'+ api.aup_url() +'" target="_blank">terms and conditions</a>'
        

class AccountRemoveForm(forms.Form):
    username = forms.CharField(max_length=250, widget=forms.HiddenInput)

@wrap_rpc
def index(api, request):
    accs = api.account_list()
    account_flags = api.account_flags()
    for acc in accs:
        acc['flags_name'] = []
        for flag in acc['flags']:
            acc['flags_name'].append(account_flags[flag])
    return render_to_response("account/index.html", {'user': api.user, 'accounts': accs})

@wrap_rpc
def info(api, request, id=None):
    user = api.user.data
    if id:
        user = api.account_info(id)
    else:
        id = user["id"]     
               
    if request.method=='POST':
        form = AccountChangeForm(api, request.REQUEST)
        if form.is_valid():
            data = form.cleaned_data
            if not api.user.isAdmin(data["organization"]):
                del data["flags"]
            del data["name"]
            del data["password2"]
            if not data["password"]:
                del data["password"]
            api.account_modify(id, attrs=data)
            return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": id}))
    else:
        form = AccountChangeForm(api, user)
    return render_to_response("account/info.html", {'user': api.user, "account": user, "form": form})
    
@wrap_rpc
def register(api, request):
    if request.method=='POST':
        form = AccountRegisterForm(api, request.REQUEST)
        if form.is_valid():
            data = form.cleaned_data
            username = data["name"]
            password = data["password"]
            organization=data["organization"]
            del data["password"]
            del data["password2"]
            del data["name"]
            del data["aup"]
            del data["organization"]
            api = getGuestApi()
            try:
                api.account_create(username, password=password, organization=organization, attrs=data)
                request.session["auth"] = "%s:%s" % (username, password)
                return HttpResponseRedirect(reverse("tomato.account.info"))
            except:
                form._errors["name"] = form.error_class(["This name is already taken"])
    else:
        form = AccountRegisterForm(api) 
    return render_to_response("account/register.html", {"form": form})

@wrap_rpc
def remove(api, request, username=None):
    if request.method == 'POST':
        form = AccountRemoveForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            api.account_remove(username)
            return HttpResponseRedirect(reverse("tomato.account.index"))
        else:
            if not username:
                username=request.POST['username']
            if username:
                form.fields["username"].initial = username
                return render_to_response("account/remove_confirm.html", {'user': api.user, 'username': username, 'form': form})
            else:
                return render_to_response("main/error.html",{'user': api.user, 'type':'Transmission Error','text':'There was a problem transmitting your data.'})
    else:
        if username:
            form = AccountRemoveForm()
            form.fields["username"].initial = username
            return render_to_response("account/remove_confirm.html", {'user': api.user, 'username': username, 'form': form})
        else:
            return render_to_response("main/error.html",{'user': api.user, 'type':'not enough parameters','text':'No username specified. Have you followed a valid link?'})

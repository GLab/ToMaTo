# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django import forms
from tomato.crispy_forms.helper import FormHelper
from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import StrictButton, FormActions

from lib import getapi
import settings

import json, urllib2, re
from urlparse import urljoin

def index(request):
	try:
		api = getapi()
		url = api.server_info()["external_urls"]["news_feed"]
		news = json.load(urllib2.urlopen(url))
		pattern = re.compile("<[^>]+((?:src|href)=(?:[\"']([^\"']+)[\"']))[^>]*>")
		for item in news["items"]:
			desc = item["description"]
			for term, url in pattern.findall(desc):
				if url.startswith("mailto:") or url.startswith("&#109;&#097;&#105;&#108;&#116;&#111;:"):
					continue
				nurl = urljoin(item["link"], url)
				nterm = term.replace(url, nurl)
				desc = desc.replace(term, nterm)
			item["description"] = desc
		news["items"] = news["items"][:3]
	except:
		import traceback
		traceback.print_exc()
		news = {}
	return render(request, "main/start.html", {"news": news})

def ticket(request, page=""):
	return HttpResponseRedirect(settings.ticket_url % page)

def project(request, page=""):
	return HttpResponseRedirect(settings.project_url % page)

class LoginForm(forms.Form):
	username = forms.CharField(max_length=255)
	password = forms.CharField(max_length=255, widget=forms.PasswordInput)
	long_session = forms.BooleanField(required=False, label="Remember me")
	def __init__(self, *args, **kwargs):
		super(LoginForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_class = 'form-horizontal'
		self.helper.form_action = reverse(login)
		self.helper.form_method = "post"
		self.helper.label_class = 'col-lg-2'
		self.helper.field_class = 'col-lg-4'
		self.helper.layout = Layout(
		    'username',
		    'password',
		    'long_session',
		    FormActions(
		    	StrictButton('Log in', css_class='btn-primary', type="submit")
		    	)
		    )

def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if not form.is_valid():
			return render(request, "main/login.html", {'form': form})
		formData = form.cleaned_data
		request.session["auth"] = formData["username"] + ":" + formData["password"]
		api = getapi(request)
		if not api.user: #login failed
			del request.session["auth"]
			return render(request, "main/login.html", {'form': form, 'message': 'login failed'})
		request.session["user"] = api.user
		request.session.set_expiry(3600*24*14 if formData["long_session"] else 3600)
		forward = reverse("tomato.main.index")
		if "forward_url" in request.session:
			forward = request.session["forward_url"]
			del request.session["forward_url"]
		return HttpResponseRedirect(forward)
	else:
		form = LoginForm()
		return render(request, "main/login.html", {'form': form})

def logout(request):
	if "auth" in request.session:
		del request.session["auth"]
	if "user" in request.session:
		del request.session["user"]
	return redirect("tomato.main.index")

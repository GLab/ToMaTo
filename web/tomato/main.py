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

from lib import getapi, getNews, wrap_rpc

def index(request):
	try:
		news = getNews()
	except:
		news = {}
	return render(request, "main/start.html", {"news": news})

@wrap_rpc
def statistics(api, request):
	return render(request, "main/statistics.html", {"stats": api.statistics()})

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
		self.helper.label_class = 'col-lg-2 col-md-2 col-sm-2'
		self.helper.field_class = 'col-lg-4 col-md-5 col-sm-6'
		self.helper.layout = Layout(
		    'username',
		    'password',
		    'long_session',
		    FormActions(
		    	StrictButton('Log in', css_class='col-sm-offset-2 btn-primary', type="submit")
		    )
		)

def login(request):
	if request.method == 'POST' and "username" in request.POST:
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
		if "forward_url" in request.POST:
			request.session["forward_url"] = request.POST['forward_url']
		return render(request, "main/login.html", {'form': form})

def logout(request):
	if "auth" in request.session:
		del request.session["auth"]
	if "user" in request.session:
		del request.session["user"]
	return redirect("tomato.main.index")

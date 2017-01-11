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

import random, string

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from admin_common import organization_name_list
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape

from tomato.crispy_forms.bootstrap import FormActions, StrictButton

from lib import wrap_rpc, getapi, AuthError, serverInfo, wrap_json, userflags

from lib.error import UserError #@UnresolvedImport

from lib.references_web import resolve_reference, reference_config, entity_to_label

from admin_common import BootstrapForm, ConfirmForm, RemoveConfirmForm, FixedList, FixedText, Buttons, append_empty_choice
from tomato.crispy_forms.layout import Layout
from django.core.urlresolvers import reverse

from lib.settings import get_settings
from . import settings as config_module
settings = get_settings(config_module)



# value: flags of account to display
# flags: all flags
def render_account_flag_fixedlist(api, value):
	output = []
	isFirst = True #is first category (set to Flase after first category has been found)
	
	for cat in userflags.categories:
		foundOne = False #found a match in current category
		for v in cat['flags']:
			if v in value:
				if not foundOne:
					if not isFirst:
						output.append('</ul>') #first to.display entry of current category. close other category first, if this is not the first category.
					else:
						isFirst = False
					output.append('<ul>')
					output.append('<b>' + cat['onscreentitle'] + '</b>')
					foundOne = True
				output.append('<li style="margin-left:20px;">' + userflags.flags.get(v, v) + '</li>')
		
	return output
			
			
			
class AccountFlagFixedList(FixedList):
	api = None
	def render(self, name, value, attrs=None):
		output = render_account_flag_fixedlist(self.api, value)
		return forms.MultipleHiddenInput.render(self, name, value) + mark_safe(u'\n'.join(output))
	
	def __init__(self, api, *args, **kwargs):
		super(AccountFlagFixedList, self).__init__(*args, **kwargs)
		self.api = api
		

class AccountFlagCheckboxList(forms.widgets.CheckboxSelectMultiple):
	inline_class=""
	api = None
	def render(self, name, value, attrs=None):
		if value is None: value = []
		has_id = attrs and 'id' in attrs
		final_attrs = self.build_attrs(attrs, name=name)
		str_values = set([force_unicode(v) for v in value])
		
		#algorithm similar to render_account_flag_fixedlist
		output = []
		isFirst = True
		
		for cat in userflags.categories:
			foundOne = False
			for v in cat['flags']:
				if not foundOne:
					if not isFirst:
						output.append('<br />')
					else:
						isFirst = False
					output.append('<b>' + cat['onscreentitle'] + '</b>')
					foundOne = True
					
				if has_id:
					final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], self.choices.index((v, userflags.flags.get(v,v)))))
					label_for = u' for="%s"' % final_attrs['id']
				else:
					label_for = ''
					
				cb = forms.widgets.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
				option_value = force_unicode(v)
				rendered_cb = cb.render(name, option_value)
				option_label = conditional_escape(force_unicode(userflags.flags.get(v, v)))
				output.append(u'<label style="font-weight:normal;" class="checkbox%s">' % (self.inline_class))
				output.append(rendered_cb.replace("form-control", "") + option_label)
				output.append('</label>')
		output.append('</ul>')
		return mark_safe(u'\n'.join(output))
	
	def __init__(self, api, *args, **kwargs):
		super(AccountFlagCheckboxList, self).__init__(*args, **kwargs)
		self.api = api
		self.choices = userflags.flags.items()
	
class AccountForm(BootstrapForm):
	name = forms.CharField(label="Account name", max_length=50)
	password = forms.CharField(label="Password", widget=forms.PasswordInput, required=False)
	password2 = forms.CharField(label="Password (repeated)", widget=forms.PasswordInput, required=False)
	organization = forms.CharField(max_length=50)
	origin = forms.CharField(label="Origin", widget=forms.HiddenInput, required=False)
	realname = forms.CharField(label="Full name")
	email = forms.EmailField()
	flags = forms.MultipleChoiceField(required=False)
	_reason = forms.CharField(widget = forms.Textarea, required=False, label="Reason for Registering")
	send_mail = forms.BooleanField(label="Inform user", required=False, initial=True)
	def __init__(self, api, *args, **kwargs):
		super(AccountForm, self).__init__(*args, **kwargs)
		self.fields["organization"].widget = forms.widgets.Select(choices=append_empty_choice(organization_name_list(api)))
		
	def clean_password(self):
		if self.data.get('password') != self.data.get('password2'):
			raise forms.ValidationError('Passwords are not the same')
		return self.data.get('password')
	
	def clean(self, *args, **kwargs):
		self.clean_password()
		return forms.Form.clean(self, *args, **kwargs)

class AccountChangeForm(AccountForm):
	def __init__(self, api, data):
		AccountForm.__init__(self, api, data)
		flags = userflags.flags.items()
		self.fields["name"].widget = FixedText()
		del self.fields["origin"]
		del self.fields["_reason"]
		self.fields["flags"].choices = flags
		if api.user.isAdmin(data["organization"]):
			self.fields["flags"].widget = AccountFlagCheckboxList(api)
		else:
			self.fields["flags"].widget = AccountFlagFixedList(api)

		is_self = data['name'] == api.account_info()['name']
		if is_self:
			self.fields['organization'].widget = FixedText()

		self.helper.form_action = reverse(edit, kwargs={'id':data['name']})
		self.helper.layout = Layout(*(
			(
				'name',
				'password',
				'password2',
				'organization',
				'realname',
				'email',
				'flags'
			) +
			(() if is_self else (
				'send_mail',
			)) +
			(
				Buttons.cancel_save,
			)
		))


class AccountRegisterForm(AccountForm):
	aup = forms.BooleanField(label="", required=True)
	
	def __init__(self, api, data=None):
		AccountForm.__init__(self, api, data)
		self.fields["password"].required = True
		del self.fields["flags"]
		del self.fields["origin"]
		del self.fields["send_mail"]
		self.fields['aup'].label = 'I accept the <a href="'+ settings.get_external_url('aup') +'" target="_blank">acceptable use policy</a>'
		self.helper.form_action = reverse(register)
		self.helper.layout = Layout(
			'name',
			'password',
			'password2',
			'organization',
			'realname',
			'email',
			'_reason',
			'aup',
			Buttons.cancel_save
		)

class AdminAccountRegisterForm(AccountForm):
	aup = forms.BooleanField(label="", required=True)
	
	def __init__(self, api, data=None):
		AccountForm.__init__(self, api, data)
		self.fields["password"].required = True
		del self.fields["flags"]
		del self.fields["origin"]
		del self.fields["aup"]
		del self.fields["password"]
		del self.fields["password2"]
		del self.fields["send_mail"]
		self.helper.form_action = reverse(register)
		self.helper.layout = Layout(
			'name',
			'organization',
			'realname',
			'email',
			Buttons.cancel_save
		)

class AnnouncementForm(BootstrapForm):
	title = forms.CharField(required=True)
	message = forms.CharField(widget=forms.Textarea, required=True)
	ref_type = forms.CharField(required=False, label="Include Reference to:")
	ref_id = forms.CharField(required=False, label="Referenced Object ID", help_text="Usually ID or name of the entity to be referenced.")
	show_sender = forms.BooleanField(required=False, initial=False, help_text="Show your name as sender in the notification")
	def __init__(self, *args, **kwargs):
		super(AnnouncementForm, self).__init__(*args, **kwargs)
		self.helper.form_action = reverse(announcement_form)
		ref_conf = [(k, entity_to_label(k)) for k in reference_config().iterkeys()]
		ref_conf.insert(0, ("", "--No Reference--"))
		self.fields['ref_type'].widget = forms.widgets.Select(choices=ref_conf)
		self.helper.layout = Layout(
			'title',
			'message',
			'show_sender',
			'ref_type',
			'ref_id',
			FormActions(
				StrictButton('<span class="glyphicon glyphicon-remove"></span> Cancel', css_class='btn-default backbutton'),
				StrictButton('<span class="glyphicon glyphicon-send"></span> Publish', css_class='btn-primary', type="submit"),
				css_class="col-sm-offset-4"
			)
		)

@wrap_rpc
def list(api, request, with_flag=None, organization=True):
	if not api.user:
		raise AuthError()
	organization_label = None
	if organization is True:
		organization = api.user.organization
	else:
		organization = None
	if organization:
		organization_label = api.organization_info(organization)['label']
	accs = api.account_list(organization=organization, with_flag=with_flag)
	orgas = api.organization_list()
	for acc in accs:
		acc['flags_name'] = mark_safe(u'\n'.join(render_account_flag_fixedlist(api, acc['flags'])))
	return render(request, "account/list.html", {'accounts': accs, 'orgas': orgas, 'with_flag': with_flag, 'organization':organization, 'organization_label':organization_label})

@wrap_rpc
def info(api, request, id=None):
	if not api.user:
		raise AuthError()
	user = api.account_info(id) if id else api.user.data
	organization = api.organization_info(user["organization"])
	user["reason"] = user.get("_reason")
	flags = []
	for flag in user["flags"] or []:
		if flag in userflags.flags:
			flags.append(userflags.flags[flag])
		else:
			flags.append(flag+" (unknown flag)")
	flaglist = mark_safe(u'\n'.join(render_account_flag_fixedlist(api, user['flags'] or [])))
	return render(request, "account/info.html", {"account": user, "organization": organization, "flags": flags, 'flaglist': flaglist})                   

@wrap_rpc
def accept(api, request, id):
	if not api.user:
		raise AuthError()
	user = api.account_info(id)
	flags = user["flags"]
	for flag in ["new_account", "over_quota"]:
		if flag in flags:
			flags.remove(flag)
	api.account_modify(id, attrs={"flags": flags})
	api.account_send_notification(id, subject="Account activated", message="Your account has been activated by an administrator. Now you are ready to start your first topology. Please see the tutorials to learn how to use ToMaTo.", from_support=True)
	return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": id}))

@wrap_rpc
def edit(api, request, id):
	if not api.user:
		raise AuthError()
	user = api.account_info(id)
	if request.method == 'POST':
		form = AccountChangeForm(api, request.REQUEST)
		if form.is_valid():
			data = form.cleaned_data
			if not api.user.isAdmin(data["organization"]):
				del data["flags"]
				del data["organization"]
			del data["name"]
			del data["password2"]
			if not data["password"]:
				del data["password"]
			send_mail = data.get("send_mail", False)
			if "send_mail" in data:
				del data["send_mail"]

			if 'flags' in data:
				old_flags = api.account_info(id)['flags']
				newflags = {}
				for flag in userflags.flags.iterkeys():
					if flag in data['flags']:
						if flag not in old_flags:
							newflags[flag] = True
					else:
						if flag in old_flags:
							newflags[flag] = False
				data['flags'] = newflags

			api.account_modify(id, attrs=data)
			if send_mail:
				api.account_send_notification(id, subject="Account modified", message="Your account has been modified by an administrator. Please check your account details for the changes.", from_support=True)
			request.session["user"].updateData(api)
			return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": id}))
	else:
		data = user.copy()
		data["send_mail"] = user["id"] != api.user.id
		form = AccountChangeForm(api, data)
	return render(request, "form.html", {"account": user, "form": form, "heading":"Edit Account "+user["id"]})
	
@wrap_rpc
def register(api, request):
	if request.method=='POST':
		form = AdminAccountRegisterForm(api, request.REQUEST) if api.user else AccountRegisterForm(api, request.REQUEST)
		if form.is_valid():
			data = form.cleaned_data
			username = data["name"]
			organization=data["organization"]
			del data["name"]
			del data["organization"]
			if api.user:
				password = ''.join(random.choice(2 * string.ascii_lowercase + string.ascii_uppercase + 2 * string.digits) for x in range(12))
			else:
				password = data["password"]
				del data["password"]
				del data["password2"]
				del data["aup"]
			try:
				if "_reason" in data:
					del data["_reason"]  # fixme: enable _reason when user data is working again
				account = api.account_create(username, password=password, organization=organization, attrs=data)
				if api.user:
					api.account_send_notification(username,
						subject="Account creation", 
						message="A new ToMaTo account has been created for you by an administrator with the username\n\n\t%s\n\n and the password\n\n\t%s\n\nPlease login using that username and password and change it to something you can remember." % (username, password),
						from_support=True)
				else:
					request.session["auth"] = "%s:%s" % (username, password)
					api = getapi(request)
					request.session["user"] = api.user  
				return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": account["name"]}))
			except UserError, e:
				if e.code == UserError.ALREADY_EXISTS:
					import traceback
					print traceback.print_exc()
					form._errors["name"] = form.error_class(["This name is already taken"])
				else:
					raise
	else:
		form = AdminAccountRegisterForm(api) if api.user else AccountRegisterForm(api) 
	return render(request, "form.html", {"form": form, "heading":"Register New Account"})

@wrap_rpc
def reset_password(api, request, id):
	if request.method == 'POST':
		form = ConfirmForm(request.POST)
		if form.is_valid():
			passwd = ''.join(random.choice(2 * string.ascii_lowercase + string.ascii_uppercase + 2 * string.digits) for x in range(12))
			api.account_modify(id, {"password": passwd})
			api.account_send_notification(id, subject="Password reset", message="Your password has been reset by an administrator to\n\n\t%s\n\nPlease login using that password and change it to something you can remember." % passwd, from_support=True)
			return HttpResponseRedirect(reverse("tomato.account.info", kwargs={"id": id}))
	form = ConfirmForm.build(reverse("tomato.account.reset_password", kwargs={"id": id}))
	return render(request, "form.html", {"heading": "Reset Password", "message_before": "Are you sure you want to reset the password of the account '"+id+"'?", 'form': form})	

@wrap_rpc
def remove(api, request, id=None):
	if request.method == 'POST':
		form = RemoveConfirmForm(request.POST)
		if form.is_valid():
			api.account_remove(id)
			return HttpResponseRedirect(reverse("account_list"))
	form = RemoveConfirmForm.build(reverse("tomato.account.remove", kwargs={"id": id}))
	return render(request, "form.html", {"heading": "Remove Account", "message_before": "Are you sure you want to remove the account '"+id+"'?", 'form': form})


@wrap_rpc
def _own_notifications(api, request, show_read, ref_filter=None, subject_group=None):
	notifications = api.account_notifications(show_read)

	for notification in notifications:
		if notification.get("ref", None):

			notification['ref_link'], notification['ref_text'] = resolve_reference(api, notification['ref'])

		if notification.get("sender", None):
			try:
				acc_inf = api.account_info(notification["sender"])
				notification['sender_realname'] = acc_inf["realname"]
			except:
				notification['sender_realname'] = notification["sender"]

	is_filtered = ref_filter or subject_group
	if is_filtered:
		notifications_old = notifications
		notifications = []
		for notification in notifications_old:
			to_add = True

			if ref_filter is not None:
				notification_ref = notification.get('ref', None)
				if notification_ref:
					to_add = (notification_ref[0] == ref_filter[0]) and (notification_ref[1] == ref_filter[1])
				else:
					to_add = False

			if to_add and (subject_group is not None):
				if notification['subject_group'] != subject_group:
					to_add = False

			if to_add:
				notifications.append(notification)

	notifications = sorted(notifications, key=lambda n: n['timestamp'], reverse=True)

	show_mark_all_read_button = len(notifications) > 1

	return render(request, "account/notifications.html", {"notifications": notifications, "include_read": show_read, 'is_filtered': is_filtered, "show_mark_all_read_button": show_mark_all_read_button})

def unread_notifications(request):
	return _own_notifications(request, False)

def all_notifications(request):
	return _own_notifications(request, True)

def filtered_unread_notifications(request, ref_entity, ref_id, subject_group):
	return _own_notifications(request, False, (ref_entity, ref_id), subject_group)

@wrap_json
def notification_mark_read(api, request, notification_id, read):
	api.account_notification_set_read(notification_id, read)
	request.session["user"].updateData(api)
	return True

@wrap_json
def notification_mark_all_read(api, request, read):
	api.account_notification_set_all_read(read)
	request.session["user"].updateData(api)
	return True

@wrap_rpc
def announcement_form(api, request):
	if request.method == 'POST':
		form = AnnouncementForm(request.POST)
		if form.is_valid():
			formData = form.cleaned_data
			if formData["ref_type"]:
				ref = [formData["ref_type"], formData["ref_id"]]
			else:
				ref = None
			api.broadcast_announcement(formData['title'], formData['message'], ref, formData["show_sender"])
			request.session["user"].updateData(api)
			return HttpResponseRedirect(reverse("tomato.account.unread_notifications"))
	form = AnnouncementForm()
	return render(request, "form.html", {'form': form, "heading": "Broadcast Announcement"})

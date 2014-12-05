'''
Created on Dec 4, 2014

@author: t-gerhard
'''
import json

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django import forms
from django.core.urlresolvers import reverse

from tomato.crispy_forms.layout import Layout
from ..admin_common import Buttons
from ..lib import wrap_rpc, AuthError
from . import identical, add_function, edit_function, InputTransformerForm, RemoveConfirmForm



class OrganizationForm(InputTransformerForm):
    
    name = forms.CharField(max_length=50, help_text="The name of the organization. Must be unique to all organizations. e.g.: ukl")
    description = forms.CharField(max_length=255, label="Label", help_text="e.g.: Technische Universit&auml;t Kaiserslautern")
    homepage_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org")
    image_url = forms.CharField(max_length=255, required=False, help_text="must start with protocol, i.e. http://www.tomato-testbed.org/logo.png")
    description_text = forms.CharField(widget = forms.Textarea, label="Description", required=False)
    
    buttons = Buttons.cancel_add
    
    primary_key = "name"
    create_keys = ['name', 'description']
    redirect_after = "tomato.admin.organization.info"
    
    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        self.helper.layout = Layout(
            'name',
            'description',
            'homepage_url',
            'image_url',
            'description_text',
            self.buttons
        )
        if self.is_valid():
            self.helper.form_action = reverse(edit, kwargs={"name": self.cleaned_data["name"]})
        
class AddOrganizationForm(OrganizationForm):
    title = "Add Organization"
    def __init__(self, *args, **kwargs):
        super(AddOrganizationForm, self).__init__(*args, **kwargs)
    
class EditOrganizationForm(OrganizationForm):
    buttons = Buttons.cancel_save
    title = "Editing Organization '%(name)s'"
    def __init__(self, *args, **kwargs):
        super(EditOrganizationForm, self).__init__(*args, **kwargs)
        self.fields["name"].widget=forms.TextInput(attrs={'readonly':'readonly'})
        self.fields["name"].help_text=None
        
    
class RemoveOrganizationForm(RemoveConfirmForm):
    pass
    

@wrap_rpc
def list(api, request):
    organizations = api.organization_list()
    sites = api.site_list()
    hosts = api.host_list()
    omap = {}
    for o in organizations:
        o["hosts"] = {"count": 0, "avg_load": 0.0, "avg_availability": 0.0}
        omap[o["name"]] = o
    for h in hosts:
        o = omap[h["organization"]]
        o["hosts"]["count"] += 1
        o["hosts"]["avg_load"] += h["load"] if "host_info" in h else 0.0
        o["hosts"]["avg_availability"] += h["availability"] if "host_info" in h else 0.0
    for o in organizations:
        o["hosts"]["avg_load"] = (o["hosts"]["avg_load"] / o["hosts"]["count"]) if o["hosts"]["count"] else None  
        o["hosts"]["avg_availability"] = (o["hosts"]["avg_availability"] / o["hosts"]["count"]) if o["hosts"]["count"] else None
    organizations.sort(key=lambda o: o["hosts"]["count"], reverse=True)  
    return render(request, "organization/list.html", {'organizations': organizations, 'sites': sites})


@wrap_rpc
def info(api, request, name):
    orga = api.organization_info(name)
    sites = api.site_list(organization=name)
    return render(request, "organization/info.html", {'organization': orga, 'sites': sites})


@wrap_rpc
def add(api, request):
    return add_function(request,
                        Form=AddOrganizationForm,
                        clean_formargs=[],
                        clean_formkwargs={},
                        create_function=api.organization_create,
                        modify_function=api.organization_modify
                        )

@wrap_rpc
def edit(api, request, name=None):
    return edit_function(request,
                         Form=EditOrganizationForm,
                         clean_formargs=[api.organization_info(name)],
                         clean_formkwargs={},
                         modify_function=api.organization_modify,
                         primary_value=name
                         )
    
    
    
    
#still TODO
    
@wrap_rpc
def remove(api, request, name=None):
    if request.method == 'POST':
        form = RemoveConfirmForm(request.POST)
        if form.is_valid():
            api.organization_remove(name)
            return HttpResponseRedirect(reverse("tomato.organization.list"))
    form = RemoveConfirmForm.build(reverse("tomato.organization.remove", kwargs={"name": name}))
    return render(request, "form.html", {"heading": "Remove Organization", "message_before": "Are you sure you want to remove the organization '"+name+"'?", 'form': form})

@wrap_rpc
def usage(api, request, name): #@ReservedAssignment
    if not api.user:
        raise AuthError()
    usage=api.organization_usage(name)
    return render(request, "main/usage.html", {'usage': json.dumps(usage), 'name': 'Organization %s' % name})

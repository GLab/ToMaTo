from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render

from tomato.crispy_forms.layout import Layout
from tomato.crispy_forms.bootstrap import FormActions, StrictButton
from tomato.crispy_forms.helper import FormHelper

from ..lib.error import UserError #@UnresolvedImport




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
    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = "post"
        self.helper.label_class = 'col-lg-4 col-sm-4'
        self.helper.field_class = 'col-lg-6 col-sm-8'

class RenderableForm(BootstrapForm):
    title = "Untitled"
    message = None
    def __init__(self, *args, **kwargs):
        super(RenderableForm, self).__init__(*args, **kwargs)
        self.title = self.title % args[0]
        if self.message is not None:
            self.message = self.message % args[0]
    def create_response(self, request):
        args = {'form': self, "heading":self.title}
        if self.message is not None:
            args['message'] = self.message
        return render(request, "form.html", args)
    
class InputTransformerForm(RenderableForm):
    def get_values(self):
        return self.cleaned_data

class ConfirmForm(RenderableForm):
    @classmethod
    def build(cls, action, buttons=Buttons.cancel_continue):
        obj = cls()
        obj.helper.form_action = action
        obj.helper.layout = Layout(buttons)
        return obj

class RemoveConfirmForm(ConfirmForm):
    @classmethod
    def build(cls, action):
        return ConfirmForm.build(action, Buttons.cancel_remove)




#helper functions

def identical(arg):
    return arg









#functions

def add_function(request, 
                 Form,
                 clean_formargs, clean_formkwargs,
                 create_function, modify_function):
    if request.method == 'POST':
        print request.POST
        form = Form(request.POST)
        if form.is_valid():
            formData = form.get_values()
            create_values = []
            primary_value = formData[form.primary_key]
            for key in form.create_keys:
                create_values.append(formData[key])
                del formData[key]
            create_function(*create_values)
            modify_function(primary_value,formData)
            return HttpResponseRedirect(reverse(form.redirect_after, kwargs={form.primary_key: primary_value}))
        else:
            return form.create_response(request)
    else:
        form = Form(*clean_formargs, **clean_formkwargs)
        return form.create_response(request)



def edit_function(request,
                  Form,
                  clean_formargs, clean_formkwargs,
                  modify_function, 
                  primary_value = None):
    if request.method=='POST':
        form = Form(request.POST)
        if form.is_valid():
            formData = form.get_values()
            primary_value = formData[form.primary_key]
            del formData[form.primary_key]
            modify_function(primary_value,formData)
            return HttpResponseRedirect(reverse(form.redirect_after, kwargs={form.primary_key: primary_value}))
        if not primary_value:
            primary_value=request.POST[form.primary_key]
        UserError.check(primary_value, UserError.INVALID_DATA, "Form transmission failed.")
        return form.create_response(request)
    else:
        form = Form(*clean_formargs,**clean_formkwargs)
        return form.create_response(request)
        






'''
Created on Nov 20, 2014

@author: Tim Gerhard
'''
import json
from lib.error import Error, UserError, InternalError #@UnresolvedImport
from django.shortcuts import render 
from django.http import HttpResponse


def renderError(request, error):
    return render(request, "error/fault.html", {'type': error.type, 'code': error.code, 'text': "Message: "+error.message+" | Module: "+error.module+' | Data: '+str(error.data)}, status=500)

def ajaxError(error):
    return HttpResponse(json.dumps({"success": False, "error": error.raw()}))
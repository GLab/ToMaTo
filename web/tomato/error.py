'''
Created on Nov 20, 2014

@author: sylar
'''

from lib.error import Error, UserError, InternalError #@UnresolvedImport
from django.shortcuts import render 

def renderError(request, error):
    return render(request, "error/fault.html", {'type': error.type, 'code': error.code, 'text': "Message: "+error.message+" | Module: "+error.module+' | Data: '+str(error.data)}, status=500)

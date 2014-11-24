'''
Created on Nov 20, 2014

@author: Tim Gerhard
'''
from error import Error, UserError, InternalError #@UnresolvedImport
from django.shortcuts import render, redirect
import xmlrpclib, json, socket
from django.http import HttpResponse

def interpretError(error):
    debuginfos_dict = {} # list of key-value pairs, where the key and value must be strings to be shown to humans
    errormsg = "Message: "+error.message+" | Module: "+error.module # message to show to the user
    typemsg = error.code+" ("+error.type +" error)" # message to use as heading on error page
    ajaxinfos = {} # information which the editor can use to handle the exception
    responsecode = 500 # which HTTP response status code to use
    
    data = error.data
    
    #TODO: insert some magic here. The following line is just a workaround / catch-all solution.
    debuginfos_dict = data
    
    #now, return everything.
    debuginfos = []
    for inf in debuginfos_dict.keys():
        debuginfos.append({'th':inf,'td':debuginfos_dict[inf]})
    return (typemsg, errormsg, debuginfos, ajaxinfos, responsecode)







def renderError(request, error):
    typemsg, errormsg, debuginfos, _, responsecode = interpretError(error)
    return render(request, "error/error.html", {'typemsg': typemsg, 'errormsg': errormsg, 'debuginfos': debuginfos}, status=responsecode)

def renderFault (request, fault):
    import traceback
    from . import AuthError
    traceback.print_exc()
    if isinstance(fault, Error):
        return renderError(request, fault)
    elif isinstance(fault, socket.error):
        import os
        etype = "Socket error"
        ecode = fault.errno
        etext = os.strerror(fault.errno)
    elif isinstance(fault, AuthError):
        request.session['forward_url'] = request.build_absolute_uri()
        return redirect("tomato.main.login")
    elif isinstance(fault, xmlrpclib.ProtocolError):
        etype = "RPC protocol error"
        ecode = fault.errcode
        etext = fault.errmsg
        if ecode in [401, 403]:
            request.session['forward_url'] = request.build_absolute_uri()
            return redirect("tomato.main.login")
    elif isinstance(fault, xmlrpclib.Fault):
        etype = "RPC call error"
        ecode = fault.faultCode
        etext = fault.faultString
    else:
        etype = fault.__class__.__name__
        ecode = ""
        etext = fault.message
    return render(request, "error/fault.html", {'type': etype, 'code': ecode, 'text': etext}, status=500)
        



def ajaxError(error):
    typemsg, errormsg, debuginfos, ajaxinfos = interpretError(error)
    return HttpResponse(
                        json.dumps(
                                   {"success": False, 
                                    "error": {'raw': error.raw(), 
                                              'typemsg': typemsg, 
                                              'errormsg': errormsg, 
                                              'debuginfos': debuginfos, 
                                              'ajaxinfos': ajaxinfos}
                                    }
                                   )
                        )
    

def ajaxFault (fault): # stuff that happens in the actual function call
    if isinstance(fault, Error):
        return ajaxError(fault)
    elif isinstance(fault, xmlrpclib.Fault):
        return HttpResponse(json.dumps({"success": False, "error": fault.faultString}))
    elif isinstance(fault, xmlrpclib.ProtocolError):
        return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (fault.errcode, fault.errmsg)}), status=fault.errcode if fault.errcode in [401, 403] else 200)                
    elif isinstance(fault, Exception):
        return HttpResponse(json.dumps({"success": False, "error": '%s:%s' % (fault.__class__.__name__, fault)}))

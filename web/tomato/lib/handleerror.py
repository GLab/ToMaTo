'''
Created on Nov 20, 2014

@author: Tim Gerhard
'''
from error import Error, UserError, InternalError, getCodeMsg #@UnresolvedImport
from django.shortcuts import render, redirect
import xmlrpclib, socket, sys
from . import anyjson as json
from django.http import HttpResponse

def interpretError(error):
    debuginfos_dict = {} # list of key-value pairs, where the key and value must be strings to be shown to humans
    errormsg = error.onscreenmessage # message to show to the user
    
    entity_name = error.data['entity'] if 'entity' in error.data else "Entity"
    typemsg = getCodeMsg(error.code, entity_name.title()) # message to use as heading on error page
    
    ajaxinfos = {} # information which the editor can use to handle the exception
    responsecode = error.httpcode # which HTTP response status code to use
    
    data = error.data
    
    #TODO: insert some magic here. The following two lines is just a workaround / catch-all solution.
    debuginfos_dict = data
    debuginfos_dict['Module'] = error.module
    ajaxinfos = data
    
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
    _, _, etraceback =sys.exc_info()
    return render(request, "error/exception.html", {'type': etype, 'text': etext, 'traceback': traceback.extract_tb(etraceback)}, status=500)
        
def renderMessage(request, message, heading=None, data={}, responsecode=500):
    debuginfos = []
    if heading is None:
        heading = message
    for k in data.keys():
        debuginfos.append({'th':k,'td':data[k]})
    return render(request, 
                  "error/error.html", 
                  {'typemsg': heading, 
                   'errormsg': message, 
                   'debuginfos': debuginfos
                   }, 
                  status=responsecode)



def ajaxError(error):
    typemsg, errormsg, debuginfos, ajaxinfos, responsecode = interpretError(error)
    return HttpResponse(
                        json.dumps(
                                   {"success": False, 
                                    "error": {'raw': error.raw, 
                                              'typemsg': typemsg, 
                                              'errormsg': errormsg, 
                                              'debuginfos': debuginfos, 
                                              'ajaxinfos': ajaxinfos}
                                    }
                                   ),
                        status = responsecode
                        )
    

def ajaxFault (fault): # stuff that happens in the actual function call
    import traceback
    traceback.print_exc()
    if isinstance(fault, Error):
        return ajaxError(fault)
    elif isinstance(fault, xmlrpclib.Fault):
        return HttpResponse(json.dumps({"success": False, "error": fault.faultString}))
    elif isinstance(fault, xmlrpclib.ProtocolError):
        return HttpResponse(json.dumps({"success": False, "error": 'Error %s: %s' % (fault.errcode, fault.errmsg)}), status=fault.errcode if fault.errcode in [401, 403] else 200)                
    elif isinstance(fault, Exception):
        return HttpResponse(json.dumps({"success": False, "error": '%s:%s' % (fault.__class__.__name__, fault)}))

'''
catch errors, wrap them, and forward them to dump manager.

@author: Tim Gerhard
'''
from error import Error, UserError, InternalError, NetworkError, getCodeMsg, generate_inspect_trace #@UnresolvedImport
from django.shortcuts import render, redirect
import xmlrpclib, socket, sys, inspect
from . import anyjson as json
from django.http import HttpResponse
import dump as dump_lib

from settings import get_settings, Config
from .. import settings as config_module
settings = get_settings(config_module)

from versioninfo import getVersionStr

def dumpException(dump_on_error=True):
    errorgroup_id = None
    try:
      if settings.get_dump_config()[Config.DUMPS_ENABLED]:

        (type_, exc, _) = sys.exc_info()

        # web-specific error checks and wrapping
        from . import AuthError
        if type_ == AuthError:
          return
        if type_ == xmlrpclib.ProtocolError:
          if exc.errcode == 401:
            return

        # prepare backend dumplib for web context
        dump_lib.tomato_component = Config.TOMATO_MODULE_WEB
        dump_lib.tomato_version = getVersionStr()
        dump_lib.settings = settings

        # dump
        dump_id = dump_lib.dumpException()
        if dump_id is None:

          # try to reconstruct exception group id
          if isinstance(exc, Error):
            errorgroup_id = "Error__"+exc.group_id()
            #fixme: add a second boolean field that indicates whether an error has been dumped

        else:
          errorgroup_id = dump_lib.load_dump(dump_id, False)["group_id"]

        push_all_dumps()

    except:
      # avoid endless recursion
      if dump_on_error:
        dumpException(dump_on_error=False)

    return errorgroup_id


def push_all_dumps():
      from . import getapi
      api = getapi()
      dump_lib.settings = settings

      with dump_lib.dumps_lock:
        for dump_id in dump_lib.list_all_dumps_ids():
          dump = dump_lib.load_dump(dump_id, True)
          api.errordump_store(Config.TOMATO_MODULE_WEB, dump, store_key=settings.get_dumpmanager_api_key())
          dump_lib.remove_dump(dump_id)

def interpretError(error):
    debuginfos_dict = {} # list of key-value pairs, where the key and value must be strings to be shown to humans
    errormsg = error.onscreenmessage # message to show to the user
    
    entity_name = error.data['entity'] if 'entity' in error.data else "Entity"
    typemsg = getCodeMsg(error.code, entity_name.title()) # message to use as heading on error page
    
    ajaxinfos = {}  # information which the editor can use to handle the exception
    responsecode = error.httpcode  # which HTTP response status code to use
    
    data = error.data
    
    #TODO: insert some magic here. The following two lines is just a workaround / catch-all solution.
    debuginfos_dict = data
    debuginfos_dict['module'] = error.module
    ajaxinfos = data

    frame_trace = json.dumps(error.frame_trace)

    if 'function' in debuginfos_dict:
      need_comma = False
      debuginfos_dict['function'] = debuginfos_dict['function']+'('
      if 'args' in debuginfos_dict:
        if debuginfos_dict['args']:
          need_comma = True
          debuginfos_dict['function'] = debuginfos_dict['function'] + ", ".join([json.dumps(arg) for arg in debuginfos_dict['args']])
        del debuginfos_dict['args']
      if 'kwargs' in debuginfos_dict:
        if debuginfos_dict['kwargs']:
          if need_comma:
            debuginfos_dict['function'] = debuginfos_dict['function']+', '
          debuginfos_dict['function'] = debuginfos_dict['function'] + ", ".join(["%s=%s" % (k, json.dumps(v)) for k, v in debuginfos_dict['kwargs'].iteritems()])
        del debuginfos_dict['kwargs']
      debuginfos_dict['function'] = debuginfos_dict['function']+')'




    debuginfos = []
    for name, val in debuginfos_dict.items():
        if '\n' in str(val):
            val = "<pre>%s</pre>" % val
        debuginfos.append({'th':name, 'td': val})
    return (typemsg, errormsg, debuginfos, ajaxinfos, responsecode, frame_trace)







def renderError(request, error, errorgroup_id=None):

    if isinstance(error, NetworkError):
      return render(request, "error/backend_trouble.html", {'tomato_module': error.data.get("tomato_module"), 'code': error.code, 'text': error.onscreenmessage})

    typemsg, errormsg, debuginfos, _, responsecode, frame_trace = interpretError(error)
    return render(request, "error/error.html", {'typemsg': typemsg, 'errormsg': errormsg, 'debuginfos': debuginfos, 'frame_trace': frame_trace, "errorgroup_id": errorgroup_id}, status=responsecode)

def renderFault (request, fault, errorgroup_id=None):
    import traceback
    from . import AuthError
    traceback.print_exc()
    if isinstance(fault, Error):
        return renderError(request, fault, errorgroup_id=errorgroup_id)
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
    elif isinstance(fault, NetworkError):
        etype = "Backend Trouble"
        ecode = fault.code
        etext = fault.onscreenmessage
    else:
        etype = fault.__class__.__name__
        ecode = ""
        etext = fault.message
    _, _, etraceback =sys.exc_info()
    return render(request, "error/exception.html", {'type': etype, 'text': etext, 'traceback': traceback.extract_tb(etraceback), 'frame_trace': None, "errorgroup_id": errorgroup_id}, status=500)
        
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
    typemsg, errormsg, debuginfos, ajaxinfos, responsecode, _ = interpretError(error)
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

#!/usr/bin/env python

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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.    If not, see <http://www.gnu.org/licenses/>

"""
Grants
------
For security reasons, the fileserver uses so called *grants* to verify that
an upload or download request is authorized by the hostmanager. The grants are
pseudo-random strings that are very unlikely to be guessed.
Note that grants have an internal timeout and loose their validity after that.


Uploading files
---------------
The filemanager accepts file uploads for valid grants under the URL 
``http://SERVER:PORT/GRANT/upload``. Uploads have to be sent via POST with
*multipart/form-data* encoding. After sucessfully uploading a file, a successs
message is shown. A redirect to a different URL can be requested by appending
``?redirect=URL_BASE64`` to the upload URL where *URL_BASE64* is the 
base64-encoded destination URL.
A simple upload form can be accessed under the URL 
``http://SERVER:PORT/GRANT/upload_form``. 


Downloading files
-----------------
The filemanager accepts file download requests for valid grants under the URL
``http://SERVER:PORT/GRANT/download``. Downloads have to be requested via GET
requests. The filemanager accepts the following parameters for downloads:

  ``name``
    The name of the file that is being sent to the client
  ``mimetype``
    The content-type of the file that is being sent to the client

The fileserver will also honor the ``If-modified-since`` header.
"""


import SocketServer, BaseHTTPServer, hashlib, cgi, urlparse, urllib, shutil, base64, time, os.path, datetime, sys
try:    #python >=2.6
    from urlparse import parse_qsl #@UnusedImport
except: #python <2.6
    from cgi import parse_qsl #@Reimport

from .. import util #@UnresolvedImport
from ... import config

import urllib

ACTION_UPLOAD = "upload"
ACTION_DOWNLOAD = "download"

_httpd = None
_seed = os.urandom(8)
_grants = {}

def deleteGrantFile(grant):
    if os.path.exists(grant.path):
        os.remove(grant.path)

def _code(path):
    return hashlib.md5(_seed+path).hexdigest()

def addGrant(path, *args, **kwargs):
    code = _code(path)
    _grants[code] = Grant(path, *args, **kwargs)
    return code

def delGrant(code):
    if code in _grants:
        del _grants[code]

def getGrant(code):
    return _grants.get(code)

def timeout():
    for grant in _grants.values():
        if grant.until < time.time():
            grant.remove()

class Grant:
    def __init__(self, path, action, until=None, triggerFn=None, repeated=False, timeout=None, removeFn=None):
        self.path = path
        self.action = action
        if until:
            self.until = until
        else:
            if not timeout:
                timeout = {"upload": 3600, "download": 12*3600}[action]
            self.until = time.time() + timeout
        self.triggerFn = triggerFn
        self.removeFn = removeFn
        self.repeated = repeated
    def trigger(self):
        if callable(self.triggerFn):
            self.triggerFn(self)
        if not self.repeated:
            self.remove()
    def check(self, action):
        if not self.until >= time.time():
            self.remove()
            return False
        return action == self.action
    def remove(self):
        if callable(self.removeFn):
            self.removeFn(self)
            delGrant(_code(self.path))

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def process_request(self):
        _, _, path, _, query, _ = urlparse.urlparse(self.path)
        params = dict(parse_qsl(query))
        return (path, params)
    def error(self, code, message):
        self.send_error(code, message)
        self.end_headers()
        self.finish()
    def html(self, html, code=200, redirect=None):
        self.send_response(code)
        self.end_headers()
        self.wfile.write("<html>")
        if redirect:
            self.wfile.write("<head><meta http-equiv=\"refresh\" content=\"0;url=%s\"/></head>" % redirect)
        self.wfile.write("<body>")
        self.wfile.write(html)
        self.wfile.write("</body></html>")
        self.finish()
    def do_POST(self):
        return self._handle()
    def do_HEAD(self):
        return self._handle()
    def do_GET(self):
        return self._handle()
    def _handle(self):
        path, params = self.process_request()
        try:
            parts = path.split("/")
            if len(parts) != 3 or parts[0]:
                return self.error(404, "Not Found")
            (dummy, grant, action) = parts
            if hasattr(self, "_handle_%s" % action):
                return getattr(self, "_handle_%s" % action)(grant, **params)
            else:
                return self.error(404, "Not Found")
        except Exception, exc:
            import traceback
            traceback.print_exc()
            self.error(500, "%s failed: %s" % (path, exc))
    def _handle_download(self, grant, name="download", mimetype="application/octet-stream", **params):
        grant = getGrant(grant)
        if not (grant and grant.check(ACTION_DOWNLOAD)):
            self.error(403, "Invalid grant")
            return
        filename = grant.path
        if not os.path.exists(filename):
            grant.trigger()
            return self.error(404, "File not found")
        if "If-Modified-Since" in self.headers:
            date = datetime.datetime.strptime(self.headers.get("If-Modified-Since"), "%a, %d %b %Y %H:%M:%S %Z")
            fdate = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
            if fdate <= date:
                grant.trigger()
                return self.error(304, "Not modified")
        with open(filename, "rb") as file_:
            self.send_response(200)
            if name:
                self.send_header('Content-Disposition', 'attachment; filename="%s"' % name)
            self.send_header('Content-Type', mimetype)
            self.send_header('Content-Length', os.path.getsize(filename))
            self.end_headers()
            if self.command != "HEAD":
                shutil.copyfileobj(file_, self.wfile)
        grant.trigger()
        self.finish()
    def _handle_upload_form(self, grant, **params):
        params = urllib.urlencode(params)
        return self.html('<form method="POST" enctype="multipart/form-data" action="/%s/upload?%s"><input type="file" name="upload"><input type="submit"></form>' % (grant, params))
    def _handle_upload(self, grant, redirect=None, **params):
        grant = getGrant(grant)
        if not (grant and grant.check(ACTION_UPLOAD)):
            self.error(403, "Invalid grant")
            return
        filename = grant.path
        with open(filename, "wb") as file_:
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':self.command, 'CONTENT_TYPE':self.headers['Content-Type']})
            upload = form["upload"].file
            shutil.copyfileobj(upload, file_)
        grant.trigger()
        if redirect:
            self.html("success, redirecting...", redirect=base64.b64decode(redirect))
        else:
            self.html("upload successful")
    def _handle_from_url_form(self, grant, **params):
        params = urllib.urlencode(params)
        return self.html('<form method="POST" enctype="multipart/form-data" action="/%s/from_url?%s"><input type="text" name="url"><input type="submit"></form>' % (grant, params))
    def _handle_from_url(self, grant, redirect=None, **params):
        grant = getGrant(grant)
        if not (grant and grant.check(ACTION_UPLOAD)):
            self.error(403, "Invalid grant")
            return
        filename = grant.path
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':self.command, 'CONTENT_TYPE':self.headers['Content-Type']})
        url = form["url"].value
        try:
            urllib.urlretrieve(url, filename)
        except:
            self.error(422, "Error retrieving file from URL")
            return
        grant.trigger()
        if redirect:
            self.html("success, redirecting...", redirect=base64.b64decode(redirect))
        else:
            self.html("fetch from URL successful")

    def log_message(self, format, *args): #@ReservedAssignment
        return
        
class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""
    
def start():
    print >>sys.stderr, "Starting fileserver on port %d" % config.FILESERVER["PORT"]
    global _httpd
    _httpd = ThreadedHTTPServer(('', config.FILESERVER["PORT"]), RequestHandler)
    util.start_thread(_httpd.serve_forever)

def stop():
    _httpd.server_close()

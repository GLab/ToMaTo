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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
This server allows remote clients to upload and download files to/from a
dedicated directory. All file operations are secured by hash values called
grants. Grants are calculated using a shared secret called secret key.

Grants are calculated by sorting all key=value pairs of the parameters, except
for the grant and parameters starting with _ (unserscore), alphabetically and
joining them by using the "&" sign like they were in the original request 
(but sorted) and appending the secret key prefixed by the "|" sign.
The sha1 hash of this string is the correct grant value.
If the parameters contain a valid_until field, the grant is only valid until
the given time (seconds since the epoch, in UTC). This parameter is included in
the grant checking process like all others.

The parameters of this file are PORT BASE_DIRECTORY SECRET_KEY
    PORT is the port number this server should run on
    BASE_DIRECTORY is the basic directory for all uploads and downloads
    SECRET_KEY is the secret key used to validate the grants

Path: /download
    Download a file from the hostserver.
Parameters:
    path: the file path to download, the path can be absolute or relative to 
        the basedir.
    path_encoding: the encoding of the filename in path, can be base64 or plain
        (default).
    _name: the name of the downloaded file (default: "download")
    _mimetype: the mime-type of the downloded file 
        (default: "application/octet-stream")

Path: /upload
    Upload a file to the hostserver or display an upload form. The uploaded 
    file must be sent as multipart/form-data named upload.
Parameters:
    path: the file path to store the file in, the path can be absolute or 
        relative to the basedir.
    path_encoding: the encoding of the filename in path, can be base64 or plain
        (default).
    _redirect: is the base64 encoded URL that should be loaded when the upload
        succeeded.
    _form: instead of uploading, display a simple form that allows to select 
        the file to upload. All parameters of this call will be forwarded to 
        the upload call.
    
Path: /delete
    Delete a file from the hostserver.
Parameters:
    path: the file path to delete, the path can be absolute or relative to the
        basedir.
    path_encoding: the encoding of the filename in path, can be base64 or plain
        (default).
    _redirect: is the base64 encoded URL that should be loaded when the delete
        succeeded.

All calls must have an additional parameter "grant" being calculated as
described above.
"""

import sys, SocketServer, BaseHTTPServer, hashlib, cgi, urlparse, urllib, shutil, base64, time
import os.path, configobj, datetime
try:    #python >=2.6
  from urlparse import parse_qsl
except: #python <2.6
  from cgi import parse_qsl

def check_grant(path, params):
  if "valid_until" in params and float(params["valid_until"]) < time.time():
    return False
  return calc_grant(path, params) == params.get("grant", "")

def calc_grant(path, params):
  list = [k+"="+v for k, v in params.iteritems() if not k == "grant" and not k.startswith("_")]
  list.sort()
  return hashlib.sha1(path+"|"+("&".join(list))+"|"+secret_key).hexdigest()

def path_decode(path, encoding):
  if encoding == "base64":
    return base64.b64decode(path)
  return path

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def process_request(self):
    scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.path)
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
      self.wfile.write("<head><meta http-equiv=\"refresh\" content=\"0;url=%s\"/></head>")
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
    if not check_grant(path, params):
      self.error(403, "Invalid grant")
      return
    try:
      if path == "/upload":
        if "_form" in params:
          return self._handle_upload_form(**params)
        else:
          return self._handle_upload(**params)
      elif path == "/download":
        return self._handle_download(**params)
 #     elif path == "/grant":
 #       if "_form" in params:
 #         return self._handle_grant_form(**params)
 #       else:  
 #         return self._handle_grant(**params)
      elif path == "/delete":
        return self._handle_delete(**params)
      else:
        self.error(404, "Not Found")
    except Exception, exc:
      self.error(500, "%s failed: %s" % (path, exc))
#  def _handle_grant_form(self, grant, _form=None, **params):
#    return self.html('<form method="GET" action="/grant"><input name="grant" value="%s" type="hidden"><input name="_path"><input name="" type="submit"></form>' % grant)
#  def _handle_grant(self, _path="", **params):
#      scheme, netloc, path, params, query, fragment = urlparse.urlparse(_path)
#      params = dict(parse_qsl(query))
#      grant = calc_grant(path, params)
#      combined = "%s&grant=%s" % (_path, grant) if "?" in _path else "%s?grant=%s" % (_path, grant)
#      return self.html('Path: %s<br/>Grant: %s<br/><a href="%s">%s</a>' % (_path, grant, combined, combined))
  def _handle_download(self, path, path_encoding=None, _name="download", _mimetype="application/octet-stream", **params):
    filename = path_decode(path, path_encoding)
    filename = os.path.join(basedir,filename)
    if not os.path.exists(filename):
      return self.error(404, "File not found")
    if "If-Modified-Since" in self.headers:
      date = datetime.datetime.strptime(self.headers.get("If-Modified-Since"), "%a, %d %b %Y %H:%M:%S %Z")
      fdate = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
      if fdate <= date:
        return self.error(304, "Not modified")
    file = open(filename, "rb")
    self.send_response(200)
    if _name:
      self.send_header('Content-Disposition', "attachment; filename=%s" % _name)
    self.send_header('Content-Type', _mimetype)
    self.end_headers()
    if self.command != "HEAD":
      shutil.copyfileobj(file, self.wfile)
    file.close()
    self.finish()
  def _handle_upload_form(self, _form=None, **params):
    _params = urllib.urlencode(params)
    return self.html('<form method="POST" enctype="multipart/form-data" action="/upload?%s"><input type="file" name="upload"><input type="submit"></form>' % _params)
  def _handle_upload(self, path, path_encoding=None, _redirect=None, **params):
    filename = path_decode(path, path_encoding)
    filename = os.path.join(basedir,filename)
    file = open(filename, "wb")
    form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':self.command, 'CONTENT_TYPE':self.headers['Content-Type']})
    upload = form["upload"].file
    shutil.copyfileobj(upload, file)
    file.close()
    if _redirect:
      self.html("success, redirecting...", redirect=base64.b64decode(_redirect))
    else:
      self.html("upload successful")
  def _handle_delete(self, path, path_encoding=None, _redirect=None, **params):
    filename = path_decode(path, path_encoding)
    filename = os.path.join(basedir,filename)
    os.remove(filename)
    if _redirect:
      self.html("success, redirecting...", redirect=base64.b64decode(_redirect))
    else:
      self.html("delete successful")
    
class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  """Handle requests in a separate thread."""

if __name__ == '__main__':
  config = configobj.ConfigObj('/etc/tomato-hostserver.conf')
  port = int(config.get('port', "8080"))
  basedir = config.get('basedir', "/tmp")
  secret_key = config['secret_key'] 
  httpd = ThreadedHTTPServer(('', port), RequestHandler)
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    pass
  httpd.server_close()

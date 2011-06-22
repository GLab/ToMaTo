#!/usr/bin/python

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

Grants are calculated by sorting all key=value pairs of the parameters except
for the grant alphabetically and joining them by using the "&" sign like they
were in the original request (but sorted) and appending the secret key prefixed
by the "|" sign. The sha1 hash of this string is the correct grant value.
If the parameters contain a valid_until field, the grant is only valid until
the given time (seconds since the epoch, in UTC). This parameter is included in
the grant checking process like all others.

The parameters of this file are PORT BASE_DIRECTORY SECRET_KEY
	PORT is the port number this server should run on
	BASE_DIRECTORY is the basic directory for all uploads and downloads
	SECRET_KEY is the secret key used to validate the grants

To download a file a request of the following syntax must be issued:
GET /download?file=FILE&grant=GRANT
	FILE is the base64 encoded filename in the given directory to download.
	GRANT is the grant hash as hexadecimal involving all parameters and the
	secret key.

To upload a file a request of the following syntax must be issued:
POST /upload?file=FILE&redirect=REDIRECT&grant=GRANT
	FILE is the base64 encoded filename in the given directory to store the
	 file in.
	REDIRECT is the base64 encoded URL that should be loaded when the upload
	succeeded.
	GRANT is the grant hash as hexadecimal involving all parameters and the
	secret key.
	The uploaded file must be sent as multipart/form-data named upload.
"""

import sys, SocketServer, BaseHTTPServer, hashlib, cgi, urlparse, shutil, base64, time, os.path, configobj
try:    #python >=2.6
        from urlparse import parse_qsl
except: #python <2.6
        from cgi import parse_qsl


def check_grant(params):
	if "valid_until" in params and float(params["valid_until"]) < time.time():
		return False
	list = [k+"="+v for k, v in params.iteritems() if not k == "grant"]
	list.sort()
	return hashlib.sha1("&".join(list)+"|"+secret_key).hexdigest() == params["grant"]

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def process_request(self):
		scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.path)
		params = dict(parse_qsl(query))
		return (path, params)
	def error(self, code, message):
		self.send_error(code, message)
		self.end_headers()
		self.finish()
	def do_POST(self):
		path, params = self.process_request()
		form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':self.command, 'CONTENT_TYPE':self.headers['Content-Type']})
		if path == "/upload":
			if not check_grant(params):
				self.error(403, "Invalid grant")
				return
			try:
				filename = base64.b64decode(params["file"])
				file = open(os.path.join(basedir,filename), "wb")
				upload = form["upload"].file
				shutil.copyfileobj(upload, file)
				file.close()
				self.send_response(200)
				self.end_headers()
				self.wfile.write("<html><head><meta http-equiv=\"refresh\" content=\"0;url=%s\"/></head><body>success, redirecting...</body></html>" % base64.b64decode(params["redirect"]))
				self.finish()
			except:
				self.error(500, "Failed to write file")
		else:
			self.error(404, "Not Found")
	def do_HEAD(self):
		return self._download(True)
	def do_GET(self):
		return self._download(False)
	def _download(self, headOnly=False):
		path, params = self.process_request()
		if path == "/download":
			if not check_grant(params):
				self.error(403, "Invalid grant")
				return
			try:
				filename = base64.b64decode(params["file"])
				file = open(os.path.join(basedir,filename), "rb")
				self.send_response(200)
				if params.has_key("name"):
                                        self.send_header('Content-Disposition', "attachment; filename=%s" % params["name"])
				self.send_header('Content-Type', 'application/octet-stream')
				self.end_headers()
				if not headOnly:
					shutil.copyfileobj(file, self.wfile)
					file.close()
				self.finish()
			except:
				self.error(404, "File not found")
		elif path == "/upload":
			self.send_response(200)
			self.end_headers()
			self.wfile.write('<html><body><form method="POST" enctype="multipart/form-data" action="%s"><input type="file" name="upload"><input type="submit"></form></body></html>' % self.path)
			self.finish()
		else:
			self.error(404, "Not Found")

class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	"""Handle requests in a separate thread."""

if __name__ == '__main__':
	config = configobj.ConfigObj('/etc/tomato-hostserver.conf')
	port = int(config['port'])
	basedir = config['basedir']
	secret_key = config['secret_key']
	httpd = ThreadedHTTPServer(('', port), RequestHandler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()

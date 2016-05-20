import time

def download(url, file):
	"""
	Downloads a network object from an URL to a local file.

	Parameter *url*:
		Url to the network object

	Parameter *file*:
		File to copy the network object to.

	"""
	import urllib
	urllib.urlretrieve(url, file)


def upload(url, file, name="upload"):
	"""

	Uploads a file to the target URL via the HTTP post command using name as content key.

	Parameter *url*:
		Target URL for the upload

	Parameter *file*:
		Path to the file to be uploaded

	Parameter *name*:
		Should always stay "upload". Content key for transmitted file.

	"""
	import httplib, urlparse, os
	parts = urlparse.urlparse(url)
	conn = httplib.HTTPConnection(parts.netloc)
	req = parts.path
	if parts.query:
		req += "?" + parts.query
	conn.putrequest("POST", req)
	filename = os.path.basename(file)
	filesize = os.path.getsize(file)
	BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
	CRLF = '\r\n'
	prepend = "--" + BOUNDARY + CRLF + 'Content-Disposition: form-data; name="%s"; filename="%s"' % (
	name, filename) + CRLF + "Content-Type: application/data" + CRLF + CRLF
	append = CRLF + "--" + BOUNDARY + "--" + CRLF + CRLF
	conn.putheader("Content-Length", len(prepend) + filesize + len(append))
	conn.putheader("Content-Type", 'multipart/form-data; boundary=%s' % BOUNDARY)
	conn.endheaders()
	conn.send(prepend)
	fd = open(file, "r")
	data = fd.read(8192)
	while data:
		conn.send(data)
		data = fd.read(8192)
	fd.close()
	conn.send(append)
	resps = conn.getresponse()
	data = resps.read()



def upload_and_use_rextfv(api, element_id, filename, wait_until_finished=False):
	elinfo = api.element_info(element_id)
	grant = api.element_action(element_id, "rextfv_upload_grant")
	upload_url = "http://%(hostname)s:%(port)s/%(grant)s/upload" % {"hostname":elinfo['host_info']["address"], "port":elinfo['host_info']["fileserver_port"], "grant":grant }
	upload(upload_url,filename)
	api.element_action(element_id, "rextfv_upload_use")
	if wait_until_finished:
		while True:
			time.sleep(1)
			el_info = api.element_info(element_id)
			rextfv_info = el_info.get("rextfv_run_status", None)

			if rextfv_info is None:
				continue

			if rextfv_info.get("done", False):
				return

			if not rextfv_info.get("isAlive", False):
				raise Exception("nlXTP crashed")

			time.sleep(max(0, el_info.get("info_next_sync", 0) - el_info.get("info_last_sync", 0) - 1))  # time.time() is not an option due to timezones. 1 additional second of sleep at beginning of loop

def upload_and_use_image(api, element_id, filename):
	elinfo = api.element_info(element_id)
	grant = api.element_action(element_id, "upload_grant")
	upload_url = "http://%(hostname)s:%(port)s/%(grant)s/upload" % {"hostname":elinfo['host_info']["address"], "port":elinfo['host_info']["fileserver_port"], "grant":grant }
	upload(upload_url,filename)
	api.element_action(element_id, "upload_use")

def download_rextfv(api, element_id, filename):
	elinfo = api.element_info(element_id)
	grant = api.element_action(element_id, "rextfv_download_grant")
	download_url = "http://%(hostname)s:%(port)s/%(grant)s/download" % {"hostname":elinfo['host_info']["address"], "port":elinfo['host_info']["fileserver_port"], "grant":grant }
	download(download_url, filename)

def download_image(api, element_id, filename):
	elinfo = api.element_info(element_id)
	grant = api.element_action(element_id, "download_grant")
	download_url = "http://%(hostname)s:%(port)s/%(grant)s/download" % {"hostname":elinfo['host_info']["address"], "port":elinfo['host_info']["fileserver_port"], "grant":grant }
	download(download_url, filename)

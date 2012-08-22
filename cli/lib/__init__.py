
def tcpPortOpen(host, port):
    from socket import socket, AF_INET, SOCK_STREAM
    s = socket(AF_INET, SOCK_STREAM)
    result = s.connect_ex((host, port))
    s.close()
    return not result

def download(url, file):
    import urllib
    urllib.urlretrieve(url, file)
    
def upload(url, file, name="upload"):
    import httplib, urlparse, os
    parts = urlparse.urlparse(url)
    conn = httplib.HTTPConnection(parts.netloc)
    req = parts.path
    if parts.query:
        req += "?" + parts.query
    conn.putrequest("POST",req)
    filename = os.path.basename(file)
    filesize = os.path.getsize(file)
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    prepend = "--" + BOUNDARY + CRLF + 'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename) + CRLF + "Content-Type: application/data" + CRLF + CRLF 
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
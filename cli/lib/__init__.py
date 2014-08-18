
import xmlrpclib, ssl, urllib

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
    
def link_info(id, ip, samples=10, maxWait=5, oneWayAdapt=False):
    res = element_action(id, "execute", {"cmd": "ping -A -c %d -n -q -w %d %s; true" % (samples, maxWait, ip)})
    if not res:
        return
    import re
    spattern = re.compile("(\d+) packets transmitted, (\d+) received(, \+(\d+) errors)?, (\d+)% packet loss, time (\d+)(m?s)")
    dpattern = re.compile("rtt min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) (m?s)(, pipe \d+)?, ipg/ewma (\d+\.\d+)/(\d+\.\d+) (m?s)")
    summary = False
    details = False
    for line in res.splitlines():
        if spattern.match(line):
            (transmitted, received, dummy, errors, loss, total, unit) = spattern.match(line).groups()
            (transmitted, received, errors, loss, total) = (int(transmitted), int(received), int(errors) if errors else None, float(loss)/100.0, float(total))
            summary = True
        if dpattern.match(line):
            (rttmin, rttavg, rttmax, rttstddev, rttunit, dummy, ipg, ewma, ipg_ewma_unit) = dpattern.match(line).groups()
            (rttmin, avg, rttmax, stddev, ipg, ewma) = (float(rttmin), float(rttavg), float(rttmax), float(rttstddev), float(ipg), float(ewma))
            details = True
    if not summary or not details or errors:
        return
    if oneWayAdapt:
        import math
        loss = 1.0 - math.sqrt(1.0 - loss)
        avg = avg / 2.0
        stddev = stddev / 2.0
    if rttunit == "s":
        avg = avg * 1000.0
        stddev = stddev * 1000.0
    return {"lossratio": loss, "delay": avg, "delay_stddev": stddev}

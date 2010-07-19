# -*- coding: utf-8 -*-

from util import *
import os, subprocess, shutil

class TincConnector:
  
	def deploy(self, connector, dir):
		id = connector.topology.id
		for con in connector.connections:
			host = con.device.host
			path = dir + "/" + host + "/net" + id
			if not os.path.exists(path+"/hosts"):
				os.makedirs(path+"/hosts")
			subprocess.check_call (["openssl",  "genrsa",  "-out",  path + "/rsa_key.priv"])
			self_host_fd = open(path+"/hosts/"+host, "w")
			self_host_fd.write("Address=%s\n" % host)
			subprocess.check_call (["openssl",  "rsa", "-pubout", "-in",  path + "/rsa_key.priv", "-out",  path + "/hosts/" + host + ".pub"])
			self_host_pub_fd = open(path+"/hosts/"+host+".pub", "r")
			shutil.copyfileobj(self_host_pub_fd, self_host_fd)
			self_host_fd.close()
			self_host_pub_fd.close()
			tinc_conf_fd = open(path+"/tinc.conf", "w")
			tinc_conf_fd.write ( "Mode=%s\n" % connector.type )
			tinc_conf_fd.write ( "Name=%s\n" % host )
			for con2 in connector.connections:
				host2 = con2.device.host
				if not host == host2:
					tinc_conf_fd.write ( "ConnectTo=%s\n" % host2 )
			tinc_conf_fd.close()
			startup_fd=open(dir+"/%s/startup.sh" % host, "a")
			startup_fd.write ( "tincd --net=net%s --chroot\n" % id )
			startup_fd.write ( "brctl addif hostnet%s net%s\n" % (id, id ) )
			startup_fd.write ( "ip link set net%s up\n" % id )
			startup_fd.close ()
		for con in connector.connections:
			host = con.device.host
			path = dir + "/" + host + "/net" + id
			for con2 in connector.connections:
				host2 = con2.device.host
				path2 = dir + "/" + host2 + "/net" + id
				if not host == host2:
					shutil.copy(path+"/hosts/"+host, path2+"/hosts/"+host)

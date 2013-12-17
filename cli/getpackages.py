import tomato,lib
import shutil, os, random
import tarfile, json, time
import urllib2
import re

#TODO:
# be a better command-line tool. currently everything is set in last line.
# better output
# internet connection seems broken?
# support more packet managers
# allow upgrade queryer
# check authentication/authorization before starting
# timeout for "waiting for script to finish"
# better error handling than brute-force try-until-success

config={
	'rextfv-archive':'rextfv-getpackages_archive.tar.gz',
	'tmpdir':'/tmp'
}

def progname():
	return "RexTFV Packet Manager for ToMaTo"

def progname_short():
	return "rextfv-packetmanager"
		

def get_topology_json(tech,template,site):
	attrs={'name':"tmp_"+progname_short()}
	file_info={'version':3}
	connections=[{
			"elements": [2314, 2315],
			"type": "fixed_bridge", 
			"attrs": {
				"bandwidth_to": 10000, 
				"bandwidth_from": 10000, 
				"emulation": True
			}, 
			"id": 615
	}]
	elements=[{
	    	"type": "external_network_endpoint", 
    		"attrs": {"name": "external_network_endpoint2315"},
			"parent":2313,
			"id":2315
		},{
			"type": tech+"_interface", 
			"attrs": {
				"use_dhcp": True, 
        	}, 
			"parent": 2312,
			"id": 2314
		},{
			"type": "external_network", 
			"attrs": {
				"kind": "internet", 
				"samenet": False, 
				"name": "internet1", 
				"_pos": {
					"y": 0.14545454545454545, 
					"x": 0.51200000000000001
	          	}
			}, 
			"parent": None, 
			"id": 2313
		},{
			"type": tech, 
			"attrs": {
				"profile": "normal", 
				"_pos": {
					"y": 0.12545454545454546, 
					"x": 0.30399999999999999
				}, 
				"site": site, 
				"template": template, 
				"name": "openvz1"
			}, 
			"parent": None, 
			"id": 2312
		}]
	return {
		"file_information":file_info,
		"topology":{
			"connections":connections,
			"elements":elements,
			"attrs":attrs
		}
	}



def get_upload_url(conn,element,grant):
	elinfo=conn.element_info(element)
	return "http://%(hostname)s:%(port)s/%(grant)s/upload" % \
		{	"hostname":elinfo['attrs']['host'],
			"port":elinfo['attrs']['host_fileserver_port'],
			"grant":grant }
		
def get_download_url(conn,element,grant):
	elinfo=conn.element_info(element)
	return "http://%(hostname)s:%(port)s/%(grant)s/download" % \
		{	"hostname":elinfo['attrs']['host'],
			"port":elinfo['attrs']['host_fileserver_port'],
			"grant":grant }


class packetman_urlgetter:
	conn=None

	target_topology=None
	target_element=None

	def __init__(self,conn,*args,**kwargs):
		self.conn=conn

	def _template_exists(self,tech,template):
		for i in self.conn.resource_list('template'):
			if i['attrs']['tech']==tech and i['attrs']['name']==template:
				return True
		return False

	def create_target_topology(self,tech,template,site):
		if not self._template_exists(tech,template):
			return {"success":False, "message":"template does not exist"}
		res=self.conn.topology_import(get_topology_json(tech,template,site))
		self.target_topology=res[0]
		for i in res:
			if type(i) is list:
				for j in i:
					if type(j) is list:
						if len(j) == 2:
							if j[0]==2312:
								self.target_element=j[1]
		return {"success":True}

	def topology_action(self,action):
		if self.target_topology:
			return self.conn.topology_action(self.target_topology,action)

	def element_action(self,action):
		if self.target_element:
			return self.conn.element_action(self.target_element,action)

	def get_target(self):
		return {
			"element":self.target_element,
			"topology":self.target_topology
		}

	def get_conn():
		return self.conn

	def clean_up(self):
		if self.target_topology:
			self.topology_action('destroy')
			self.conn.topology_remove(self.target_topology)


#conn: a connection to tomato
#templates: target templates to get packages for. This is a list of templates.
#tech: the tech to use when running the query. use 'openvz' if possible.
#filename: output of the final rextfv archive
#packages: packages to be installed by archive
#site: site to host the element on. None to let ToMaTo choose.
def create_package(conn,templates,tech,filename,packages,site=None):
    def get_workingdir():
		tmpdir = config['tmpdir']
		workingdir = str(random.randint(10000,99999))
		while os.path.isdir(os.path.join(tmpdir,progname_short()+'_'+workingdir)):
			workingdir = str(random.randint(10000,99999))
		workingdir = os.path.join(tmpdir,progname_short()+'_'+workingdir)
		os.makedirs(workingdir)
		return workingdir
	
    def create_query_archive(list):
		#create working dir and filenames
		wdir = get_workingdir()
		geturls_archive=os.path.join(wdir,'geturls.tar.gz')
		packetlistfile = os.path.join(wdir,'toinstall')

		#copy unconfigured archive
		with tarfile.open(config['rextfv-archive'],'r:gz') as tar:
			tar.extractall(wdir)
	
		#write config file
		with open(packetlistfile,'w+') as f:
			f.write(" ".join(list))

		#pack archive
		with tarfile.open(geturls_archive,'w:gz') as tar:
			tar.add(wdir,arcname='.')

		return geturls_archive

    def query_packageinfo(conn,template,tech,packages,site):
		res=None
		#first, create the rextfv archive which will fetch the package info
		print 'creating query archive'
		f1=create_query_archive(packages)

		#create the fetcher topology
		t = packetman_urlgetter(conn)
		try:
			print 'creating topology'
			err = t.create_target_topology(tech,template,site)
			if not err['success']:
				print 'Error: '+err['message']
				return
			top = t.get_target()['topology']
			el  = t.get_target()['element']

			#prepare topology
			print 'preparing topology'
			t.topology_action('prepare')

			#upload query archive
			print 'uploading query archive'
			grant = t.element_action('rextfv_upload_grant')
			#with open(f1,"r") as file:
			lib.upload(get_upload_url(conn,el,grant),f1)
			print 'using upload'
			t.element_action('rextfv_upload_use')

			#start topology, wait for rextfv to finish
			print 'starting topology'
			t.topology_action('start')
			print 'waiting for query archive to finish'
			elinfo = conn.element_info(el)
			sleepdelay=1
			while not (elinfo['attrs']['rextfv_run_status']['readable'] and elinfo['attrs']['rextfv_run_status']['done']):
				time.sleep(sleepdelay)
				sleepdelay += 1
				elinfo = conn.element_info(el)

			#download and read result ---- TODO: if this becomes easier by better rextfv integration of json into rextfv_run_status, use this way instead
			print 'fetching query result'
			wdir = get_workingdir()
			targetfile = os.path.join(wdir,'res.tar.gz')
			grant = t.element_action('rextfv_download_grant')
			
			custominfo_splitted = elinfo['attrs']['rextfv_run_status']['custom'].split(".",2)
			ident = custominfo_splitted[0]
			os_id = custominfo_splitted[1]
			lines = custominfo_splitted[2]
			
			def interpret_lines_aptget(lines_string):
				lines = lines_string.splitlines()
				urlList = []
				order = []
				for line in lines:
					l = line.split()
					urlList.append(l[0])
					order.append(l[1])
				return { 'urls':urlList, 'order':order}
			
			if ident == "aptget":
				res = interpret_lines_aptget(lines)
				res['os_id'] = os_id
			

		finally:
			t.clean_up()
		
		return res

	
    def create_result(filename,infos):
		wdir = get_workingdir()
		pacdir = os.path.join(wdir,'packages')
		os.makedirs(pacdir)
		#copy unconfigured archive
		with tarfile.open(config['rextfv-archive'],'r:gz') as tar:
			tar.extractall(wdir)
			
		#fetch all packages
		for info in infos:
			#create dirs and filenames
			installorderfile = os.path.join(wdir,'installorder_'+info['os_id'])
		
			#TODO: load all packages into pacdir
			ordstruct = []
			for i in range(len(info['order'])):
				ordstruct.append({
					'filename':info['order'][i],
					'url':info['urls'][i]
				})
			
			with open(installorderfile,'w+') as installfile:
				for pac in ordstruct:
					pacfilename = os.path.join(pacdir,pac['filename'])
					if not os.path.exists(pacfilename):
						print 'fetching '+pac['filename']
						with open(pacfilename,'w+') as file:
							pac['url'] = re.sub("^'","",pac['url'])
							pac['url'] = re.sub("'$","",pac['url'])
							response = urllib2.urlopen(pac['url'])
							file.write(response.read())
					installfile.write(pac['filename']+'\n')

		with tarfile.open(filename,'w:gz') as tar:
			tar.add(wdir,arcname='.')
            
    infos = []
    
    print templates
    
    for template in templates:
        print "querying packets for template "+template
        finished_current = False
        while not finished_current:
            try:
                infos.append(query_packageinfo(conn,template,tech,packages,site))
                finished_current = True
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                continue

            
    
    
    
                #infos.append(query_packageinfo(conn,template,tech,packages,site))

	#create result package
    create_result(filename,infos)

    return infos




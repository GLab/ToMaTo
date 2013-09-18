import tomato,lib
import shutil, os, random
import tarfile, json, time
import urllib

config={
	'rextfv-archive':'rextfv-getpackages_archive.tar.gz',
	'tmpdir':'/tmp'
}

def progname():
	return "RexTFV Packet Manager for ToMaTo"

def progname_short():
	return "rextfv-packetmanager"
		

def get_topology_json(tech,template):
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
				"site": None, 
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



def get_upload_url(conn,element,grant,filename):
	elinfo=conn.element_info(element)
	return "http://%(hostname)s:%(port)s/%(grant)s/upload" % \
		{	"hostname":elinfo['attrs']['host'],
			"port":elinfo['attrs']['host_fileserver_port'],
			"grant":grant }
		
def get_download_url(conn,element,grant,filename):
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

	def create_target_topology(self,tech,template):
		if not self._template_exists(tech,template):
			return {"success":False, "message":"template does not exist"}
		res=self.conn.topology_import(get_topology_json(tech,template))
		self.target_topology=res[0]
		for i in res:
			if type(i) is list:
				if len(i) == 2:
					if i[0]==2312:
						self.target_element=i[1]
		return {"success":True}

	def topology_action(self,action):
		if self.target_topology:
			self.conn.topology_action(self.target_topology,action)

	def element_action(self,action):
		if self.target_element:
			self.conn.element_action(self.target_element,action)

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
#template, tech: target template and tech the archive shall be created with
#filename: output of the final rextfv archive
#packages: packages to be installed by archive
def create_package(conn,template,tech,filename,packages):
	def get_workingdir():
		tmpdir = config['tmpdir']
		workingdir = str(random.randint(10000,99999))
		while os.path.isdir(os.path.join(tmpdir,progname_short()+'_'+workingdir)):
			workingdir = str(random.randint(10000,99999))
		workingdir = os.path.join(tmpdir,progname_short()+'_'+workingdir)
		os.makedirs(workingdir)
		return workingdir
	
	def create_query_archive(archive_config):
		#create working dir and filenames
		wdir = get_workingdir()
		geturls_archive=os.path.join(wdir,'geturls.tar.gz')
		pacsjsonfile = os.path.join(wdir,'pacs.json')

		#copy unconfigured archive
		with tarfile.open(config['rextfv-archive'],'r:gz') as tar:
			tar.extractall(wdir)
	
		#write config file
		with open(pacsjsonfile,'w+') as json_out:
			json.dump(archive_config,json_out)

		#pack archive
		with tarfile.open(geturls_archive,'w:gz') as tar:
			tar.add(wdir,arcname='.')

		return geturls_archive

	def query_packageinfo(conn,template,tech,packages):
		res=None
		#first, create the rextfv archive which will fetch the package info
		print 'creating query archive...'
		f1=create_query_archive({
			'paclist':packages,
			'mode':'get_urls'
		})

		#create the fetcher topology
		t = packetman_urlgetter(conn)
		try:
			print 'creating topology'
			err = t.create_target_topology(tech,template)
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
			with open(f1,"r") as file:
				lib.upload(get_upload_url(conn,el,grant),file)

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
			print 'downloading query result'
			wdir = get_workingdir()
			targetfile = os.path.join(wdir,'res.tar.gz')
			grant = t.element_action('rextfv_download_grant')
			with open(targetfile,'w+') as file:
				lib.download(get_download_url(conn,el,grant),file)
			with tarfile.open(targetfile,'r:gz') as tar:
				tar.extractall(wdir)
			with open(os.path.join(wdir,'result.json','r')) as f:
				res = json.load(f)

		finally:
			t.clean_up()
		
		return res

	
	def create_result(filename,info):
		#create working dir and filenames
		wdir = get_workingdir()
		pacsjsonfile = os.path.join(wdir,'pacs.json')
		pacdir = os.path.join(wdir,'packages')
		os.makedirs(pacdir)
		
		#copy unconfigured archive
		with tarfile.open(config['rextfv-archive'],'r:gz') as tar:
			tar.extractall(wdir)
	
		#TODO: load all packages into pacdir
		ordstruct = []
		for i in range(len(info['order'])):
			ordstruct.append({
				'filename':info['order'][i],
				'url':info['urls'][i]
			})
		
		for pac in ordstruct:
			print 'fetching '+pac['filename']
			with open(os.path.join(pacdir,pac['filename'])) as file:
				urllib.urlretrieve(pac['url'], file)

		#write config file
		archive_config={
			'mode':'install',
			'order':info['order']
		}
		with open(pacsjsonfile,'w+') as json_out:
			json.dump(archive_config,json_out)

		with tarfile.open(filename,'w:gz') as tar:
			tar.add(wdir,arcname='.')

	#query info about packages
	info = query_packageinfo(conn,template,tech,packages)

	#create result package
	create_result(filename,info)

	return info




def test_conn():
	return tomato.getConnection(username='root',password='test',hostname='131.246.112.102',port='8000',ssl=False)

print create_package(test_conn(),'debian-6.0_x86','openvz','/home/sylar/INSTALLER.rextfv.tar.gz',['apt-rdepends'])

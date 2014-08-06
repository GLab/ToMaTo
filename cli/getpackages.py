import os, random, textwrap,threading, tarfile


def progname_short():
	return "rextfv-packetmanager"


class Debugger:
	def log(self,string):
		print string
debugger = Debugger()





##### Generic Helper Functions

tmplock = threading.RLock()
def get_workingdir():
	with tmplock:
		tmpdir = "/tmp"
		workingdir = str(random.randint(10000,99999))
		while os.path.exists(os.path.join(tmpdir,progname_short()+'_'+workingdir)):
			workingdir = str(random.randint(10000,99999))
		workingdir = os.path.join(tmpdir,progname_short()+'_'+workingdir)
		os.makedirs(workingdir)
		return workingdir
	
	
	
	
	
	
	
class TestTopology:
	top_id = None
	el_id = None
	
	template = None
	site = None
	tech = None
	
	def __init__(self,tech,template,site,*args,**kwargs):
		self.template = template
		self.site = site
		self.tech = tech
	
	# Topology to be used to query
	def _topology_json(tech):
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
				"type": self.tech+"_interface", 
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
				"type": self.tech, 
				"attrs": {
					"profile": "normal", 
					"_pos": {
						"y": 0.12545454545454546, 
						"x": 0.30399999999999999
					}, 
					"site": self.site, 
					"template": self.template, 
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
	
	def create(self):
		return
	
	def prepare(self):
		return
	
	def start(self):
		return
	
	def stop(self):
		return
	
	def destroy(self):
		return
	
	def delete(self):
		return
	
	
	def uploadAndUseArchive(self,filename):
		return #TODO
	
	def getArchiveResult(self):
		return
	
	
	






###### Build the archive

class GetPacketArchive(object):
	directory = None
	archive_filename = None
	
	def __init__(self,*args,**kwargs):
		self.directory = get_workingdir()
	
	def _getScriptContents(self):
		return textwrap.dedent("""#!/bin/bash
					#
					# modes.
					#  assumption: only one mode file.
					#  the modes are: prepare-install, prepare-upgrade, install
					#  mode is selected by presence of mode file. filenames:
					#   toinstall - prepare-install; file contains whitespace-seperated packet list
					#   upgrade - prepare-upgrade; content does not matter.
					#   packages - install; packages is a directory.
					#			there must be a installorder_$os_id file, which is a 
					#			linebreak-seperated file list of files inside the packages directory
					#
					# identifiers
					apt_get_ident="aptget"
					
					get_os_id() {
						DISTRO=""
						ISSUE=$(cat /etc/issue)
						case "$ISSUE" in
						  Debian*5.0*)
						    DISTRO="debian_5"
						    ;;
						  Debian*6.0*)
						    DISTRO="debian_6"
						    ;;
						  Debian*7*)
						    DISTRO="debian_7"
						    ;;
						  Ubuntu*10.04*)
						    DISTRO="ubuntu_1004"
						    ;;
						  Ubuntu*10.10*)
						    DISTRO="ubuntu_1010"
						    ;;
						  Ubuntu*11.04*)
						    DISTRO="ubuntu_1104"
						    ;;
						  Ubuntu*11.10*)
						    DISTRO="ubuntu_1110"
						    ;;
						  Ubuntu*12.04*)
						    DISTRO="ubuntu_1204"
						    ;;
						  Ubuntu*12.10*)
						    DISTRO="ubuntu_1210"
						    ;;
						  Ubuntu*13.04*)
						    DISTRO="ubuntu_1304"
						    ;;
						  Ubuntu*13.10*)
						    DISTRO="ubuntu_1310"
						    ;;
						  *)
						    DISTRO="UNKNOWN"
						esac
						echo "${DISTRO}_$(uname -m)"
					}
					
					os_id=$(get_os_id)
					
					
					
					# handlers for apt-get
					need_apt_get () {
						if which apt-get; then
							return 0;
						else
							return 1;
						fi
					}
					
					update_apt_get () {
						dhclient eth0
						apt-get update
					}
					setstatus_prepare_upgrade_apt_get () {
						archive_setstatus "$apt_get_ident.$os_id.$(apt-get --print-uris -y -qq upgrade)"
					}
					setstatus_prepare_install_apt_get() {
						archive_setstatus "$apt_get_ident.$os_id.$(apt-get --print-uris -y -qq install $@)"
					}
					install_file_apt_get() {
						dpkglist=""
						for i in $(cat $archive_dir/installorder_$os_id); do
							dpkglist="${dpkglist} $archive_dir/packages/$i"
						done#TODO
						dpkg -i $dpkglist
					}
					
					if [ -e $archive_dir/toinstall ]; then
						update_apt_get
						setstatus_prepare_install_apt_get $(cat $archive_dir/toinstall)
					fi
					
					if [ -e $archive_dir/upgrade ]; then
						update_apt_get
						setstatus_prepare_upgrade_apt_get
					fi
					
					
					if [ -d $archive_dir/packages ]; then
						if [ ! -e $archive_dir/installorder_$os_id ]; then
							echo "no installorder for this OS: $os_id"
							exit 1
						fi
						install_file_apt_get $archive_dir/installorder_$os_id
					fi
					""")
	
	def _addFileToArchive(self,filename,content,path=None):
		directory = self.directory
		if path:
			directory = os.path.join(self.directory,path)
			if not os.path.exists(directory):
				os.mkdir(directory)
		with open(os.path.join(self.directory,filename),"w+") as auto_exec:
			auto_exec.write(content)
		
	def _writeMainScript(self):
		self._addFileToArchive("auto_exec.sh", self._getScriptContents())
		
	def _createArchiveFile(self):
		with tarfile.open(self.archive_filename,'w:gz') as tar:
			tar.add(self.directory,arcname='.')
		return self.archive_filename
	
	#to be implemented in a subclass
	def _writeAdditionalContents(self):
		return

	def createArchive(self):
		self._writeMainScript()
		self._writeAdditionalContents()
		return self._createArchiveFile()
	
	def uploadAndRun(self,test_topology):
		if not self.archive_filename:
			return None
		try:
			test_topology.create()
			test_topology.prepare()
			test_topology.uploadAndUseArchive(self.archive_filename)
			test_topology.start()
			result_raw = test_topology.getArchiveResult()
		finally:
			test_topology.stop()
			test_topology.destroy()
			test_topology.delete()
		return result_raw
	
	
class QueryArchive(GetPacketArchive):
	toinstall = []
	upgrade = False
	
	def __init__(self,*args,**kwargs):
		super(QueryArchive, self).__init__(*args, **kwargs)
		self.archive_filename = os.path.join(self.directory,"geturls.tar.gz")
	
	def addToInstall(self,packetname):
		self.toinstall.append(packetname)
		
	def setUpgrade(self,upgrade):
		self.upgrade = upgrade
		
	def _writeAdditionalContents(self):
		if self.upgrade:
			self._addFileToArchive("upgrade", "")
		else:
			toinstall_str = ""
			for pac in self.toinstall:
				toinstall_str = toinstall_str+pac+"\n"
			self._addFileToArchive("toinstall", toinstall_str)
		
	def _interpret_result_aptget(self,lines_string):
		lines = lines_string.splitlines()
		urlList = []
		order = []
		for line in lines:
			l = line.split()
			url = l[0]
			url = re.sub("^'","",url)
			url = re.sub("'$","",url)
			filename = l[1]
			urlList.append(l[0])
			order.append(filename)
		return { 'urls':urlList, 'order':order}
			
	def _interpret_result(self,lines_string,ident):
		if ident == "aptget":
			return self._interpret_result_aptget(lines_string)
		
	def getTemplateDetails(self,tech,template,site):
		custominfo = self.uploadAndRun(TestTopology(tech,template,site))
		custominfo_splitted = custominfo.split(".",2)
		ident = custominfo_splitted[0]
		os_id = custominfo_splitted[1]
		lines = custominfo_splitted[2]
		result = self._interpret_result(lines,ident)
		result['os_id'] = os_id
		return result
	
	
	
class PacketArchive(GetPacketArchive):
	configs = [] #will contain multiple results. format of entries: {'os_id','order','urls'}
	
	def __init__(self,*args,**kwargs):
		super(QueryArchive, self).__init__(*args, **kwargs)
		
	def addOS(self,os_config):
		self.configs.append(os_config)
			
	def _writeAdditionalContents(self):
		dir = os.path.join(self.directory,"packages")
		for conf in self.configs:
			installorder=""
			for i in range(len(info['order'])):
				filename = conf['order'][i]
				absfilename = os.path.join(packetdir,filename)
				url = conf['urls'][i]
				installorder = installorder + filename + "\n"
				if not os.path.exists(absfilename):
					with open(absfilename,'w+') as f:
						debugger.log('Fetching '+filename)
						response = urllib2.urlopen(url)
						f.write(response.read())
			self._addFileToArchive("installorder_"+pac['os_id'], installorder)



#packetlist: list of packets: ['firefox','python-django']   - if empty, this will create an upgrade archive
#template_configs: list of template configs: [{'tech','site','template'}]
def create_archive(template_configs, packetlist):
	#create query archive
	debugger.log('Creating query archive')
	qarch = QueryArchive()
	qarch.setUpgrade(True)
	for pac in packetlist:
		qarch.setUpgrade(False)
		qarch.addToInstall(pac)
	qarch.createArchive()
	
	#get os configs for all templates
	parch = PacketArchive()
	for templ in template_configs:
		debugger.log('querying '+templ['template'])
		conf = qarch.getTemplateDetails(templ['tech'], templ['template'], templ['site'])
		parch.addOS(conf)
	return parch.createArchive()
	
	



template_configs = [{'tech':'openvz','site':'ukl','template':'debian-7.0_x86_64'}]
packetlist = ['openjdk-6-jre']
return create_archive(template_configs, packetlist)
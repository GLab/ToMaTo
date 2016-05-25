import os, random, textwrap, threading, tarfile, re, urllib2, sys, json
import argparse, getpass
from time import sleep
from lib import getConnection, createUrl
from lib.upload_download import upload, upload_and_use_rextfv


def progname_short():
	return "rextfv-packetmanager"


def retryThreeTimes(func):
	def call(*args, **kwargs):
		try:
			res = func(*args, **kwargs)
			assert res is not None
			return res
		except:
			try:
				print "Don't worry, I'll retry."
				res = func(*args, **kwargs)
				assert res is not None
				return res
			except:
				print "Don't worry, I'll retry."
				return func(*args, **kwargs)
	return call


class DefaultDebugger:
	step = ""
	substep = ""

	progress_curr = 0
	progress_total = 1

	verbose = False

	def setVerbose(self):
		self.verbose = True

	def log(self, subStep=None, step=None, showStep=True, showSubStep=True, showProgress=False, indent=0,
	        progress_step=None, progress_total=None):

		if step is not None:
			if self.step != step:
				print ""
			self.step = step

		if self.verbose:
			print ""
		else:
			print "\r",

		if showStep:
			print self.step + ":",

		if progress_step is not None:
			self.progress_curr = progress_step
			self.progress_total = progress_total
		if showProgress:
			print str(self.progress_curr) + "/" + str(self.progress_total),

		if subStep is not None:
			self.substep = subStep
		if showSubStep:
			indentStr = ""
			if self.verbose:
				i = 0
				while i < indent:
					i = i + 1
					indentStr = indentStr + " "
			print indentStr + self.substep,

		print "\033[K",
		sys.stdout.flush()


debugger = DefaultDebugger()

##### Generic Helper Functions
workingdirs = []
tmplock = threading.RLock()


def get_workingdir():
	with tmplock:
		tmpdir = "/tmp"
		workingdir = str(random.randint(10000, 99999))
		while os.path.exists(os.path.join(tmpdir, progname_short() + '_' + workingdir)):
			workingdir = str(random.randint(10000, 99999))
		workingdir = os.path.join(tmpdir, progname_short() + '_' + workingdir)
		os.makedirs(workingdir)
	global workingdirs
	workingdirs.append(workingdir)
	return workingdir


def clear_workingdirs():
	global workingdirs
	for dir in workingdirs:
		os.remove(dir)


class TestTopology:
	top_id = None
	el_id = None

	template = None
	site = None
	tech = None
	api = None

	def __init__(self, api, tech, template, site, *args, **kwargs):
		self.template = template
		self.api = api
		self.site = site
		self.tech = tech

	# Topology to be used to query
	def _topology_json(self):
		attrs = {'name': "tmp_" + progname_short()}
		file_info = {'version': 3}
		connections = [{
			"elements": [11, 12],
			"type": "fixed_bridge",
			"attrs": {
				"bandwidth_to": 10000,
				"bandwidth_from": 10000,
				"emulation": True
			},
			"id": 10
		}]
		elements = [{
			"type": "external_network_endpoint",
			"attrs": {"name": "external_network_endpoint2315"},
			"parent": 2,
			"id": 12
		}, {
			"type": self.tech + "_interface",
			"attrs": {
				"use_dhcp": True,
			},
			"parent": 1,
			"id": 11
		}, {
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
			"id": 2
		}, {
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
			"id": 1
		}]
		return {
			"file_information": file_info,
			"topology": {
				"connections": connections,
				"elements": elements,
				"attrs": attrs
			}
		}

	def create(self):
		import_res = self.api.topology_import(self._topology_json())
		self.top_id = import_res[0]
		for i in import_res[1]:
			if i[0] == 1:
				self.el_id = i[1]

	def prepare(self):
		self.api.topology_action(self.top_id, "prepare")

	def start(self):
		self.api.topology_action(self.top_id, "start")

	def stop(self):
		try:
			self.api.topology_action(self.top_id, "stop")
		except:
			try:
				self.api.topology_action(self.top_id, "stop")
			except:
				self.api.topology_action(self.top_id, "stop")

	def destroy(self):
		try:
			self.api.topology_action(self.top_id, "destroy")
		except:
			try:
				self.api.topology_action(self.top_id, "destroy")
			except:
				self.api.topology_action(self.top_id, "destroy")

	def delete(self):
		self.api.topology_remove(self.top_id)

	def uploadAndUseArchive(self, filename):
		upload_and_use_rextfv(self.api, self.el_id, filename)

	def getArchiveResult(self):
		elinfo = self.api.element_info(self.el_id)
		while not elinfo["rextfv_run_status"]["done"]:
			if not elinfo["rextfv_run_status"]["isAlive"]:
				return None
			sleep(1)
			elinfo = self.api.element_info(self.el_id)
		return elinfo["rextfv_run_status"]["custom"]


###### Build the archive

class GetPacketArchive(object):
	directory = None
	archive_filename = None

	def __init__(self, *args, **kwargs):
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
						    DISTRO="ubuntu_1210"
						    ;;
						  Ubuntu*14.04*)
						    DISTRO="ubuntu_1304"
						    ;;
						  Ubuntu*14.10*)
						    DISTRO="ubuntu_1210"
						    ;;
						  Ubuntu*15.04*)
						    DISTRO="ubuntu_1304"
						    ;;
						  Ubuntu*15.10*)
						    DISTRO="ubuntu_1210"
						    ;;
						  Ubuntu*16.04*)
						    DISTRO="ubuntu_1304"
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
						done
						DEBIAN_FRONTEND=noninteractive DEBCONF_DB_FALLBACK=File{${os_id}.config.dat} dpkg -i $dpkglist
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

	def _addFileToArchive(self, filename, content, path=None):
		directory = self.directory
		if path:
			directory = os.path.join(self.directory, path)
			if not os.path.exists(directory):
				os.mkdir(directory)
		with open(os.path.join(self.directory, filename), "w+") as auto_exec:
			auto_exec.write(content)

	def _writeMainScript(self):
		self._addFileToArchive("auto_exec.sh", self._getScriptContents())

	def _createArchiveFile(self):
		with tarfile.open(self.archive_filename, 'w:gz') as tar:
			tar.add(self.directory, arcname='.')
		return self.archive_filename

	# to be implemented in a subclass
	def _writeAdditionalContents(self):
		return

	def createArchive(self):
		self._writeMainScript()
		self._writeAdditionalContents()
		return self._createArchiveFile()

	@retryThreeTimes
	def uploadAndRun(self, test_topology):
		result_raw = None
		if not self.archive_filename:
			return None
		debugger.log(subStep="creating topology")
		test_topology.create()
		try:
			debugger.log(subStep="preparing topology")
			test_topology.prepare()
			debugger.log(subStep="uploading archive")
			test_topology.uploadAndUseArchive(self.archive_filename)
			debugger.log(subStep="starting topology")
			test_topology.start()
			debugger.log(subStep="waiting for results")
			result_raw = test_topology.getArchiveResult()
		except:
			import traceback
			traceback.print_exc()
		finally:
			debugger.log(subStep="cleaning up.")
			debugger.log(subStep="stopping topology.", indent=1)
			test_topology.stop()
			debugger.log(subStep="destroying topology.", indent=1)
			test_topology.destroy()
			debugger.log(subStep="removing topology.", indent=1)
			#test_topology.delete()
		debugger.log(subStep="done.")
		return result_raw


class QueryArchive(GetPacketArchive):
	toinstall = []
	upgrade = False

	def __init__(self, *args, **kwargs):
		super(QueryArchive, self).__init__(*args, **kwargs)
		self.archive_filename = os.path.join(self.directory, "geturls.tar.gz")

	def addToInstall(self, packetname):
		self.toinstall.append(packetname)

	def setUpgrade(self, upgrade):
		self.upgrade = upgrade

	def _writeAdditionalContents(self):
		if self.upgrade:
			self._addFileToArchive("upgrade", "")
		else:
			toinstall_str = ""
			for pac in self.toinstall:
				toinstall_str = toinstall_str + pac + "\n"
			self._addFileToArchive("toinstall", toinstall_str)

	def _interpret_result_aptget(self, lines_string):
		lines = lines_string.splitlines()
		urlList = []
		order = []
		for line in lines:
			l = line.split()
			url = l[0]
			url = re.sub("^'", "", url)
			url = re.sub("'$", "", url)
			filename = l[1]
			urlList.append(url)
			order.append(filename)
		return {'urls': urlList, 'order': order}

	def _interpret_result(self, lines_string, ident):
		if ident == "aptget":
			return self._interpret_result_aptget(lines_string)

	def getTemplateDetails(self, api, tech, template, site):
		custominfo = self.uploadAndRun(TestTopology(api, tech, template, site))
		custominfo_splitted = custominfo.split(".", 2)
		ident = custominfo_splitted[0]
		os_id = custominfo_splitted[1]
		lines = custominfo_splitted[2]
		result = self._interpret_result(lines, ident)
		result['os_id'] = os_id
		return result


class PacketArchive(GetPacketArchive):
	configs = []  # will contain multiple results. format of entries: {'os_id','order','urls'}

	def __init__(self, filename, *args, **kwargs):
		super(PacketArchive, self).__init__(*args, **kwargs)
		self.archive_filename = filename

	def addOS(self, os_config):
		self.configs.append(os_config)

	def _writeAdditionalContents(self):
		packetdir = os.path.join(self.directory, "packages")
		os.makedirs(packetdir)
		number_of_pacs = 0
		for conf in self.configs:
			number_of_pacs = number_of_pacs + len(conf['order'])
		for conf in self.configs:
			installorder = ""
			for i in range(len(conf['order'])):
				filename = conf['order'][i]
				absfilename = os.path.join(packetdir, filename)
				url = conf['urls'][i]
				installorder = installorder + filename + "\n"
				if not os.path.exists(absfilename):
					with open(absfilename, 'w+') as f:
						debugger.log(subStep=filename, step="Downloading package files", progress_step=i + 1,
						             progress_total=number_of_pacs, showProgress=True)
						response = urllib2.urlopen(url)
						f.write(response.read())
			self._addFileToArchive("installorder_" + conf['os_id'], installorder)
		debugger.log(subStep="done.", step="Downloading package files")


# packetlist: list of packets: ['firefox','python-django']   - if empty, this will create an upgrade archive
# template_configs: list of template configs: [{'tech','site','template','packets':[]}]
def create_archive(api, template_configs, targetfilename):
	# get os configs for all templates
	parch = PacketArchive(targetfilename)
	for templ in template_configs:
		debugger.log(subStep='creating query archive', step='querying ' + templ['template'], showStep=True)
		qarch = QueryArchive()
		qarch.setUpgrade(True)
		for pac in templ['packets']:
			qarch.setUpgrade(False)
			qarch.addToInstall(pac)
		qarch.createArchive()
		conf = qarch.getTemplateDetails(api, templ['tech'], templ['template'], templ['site'])
		parch.addOS(conf)
	filename = parch.createArchive()
	return filename


# get connection
def parseArgs():
	"""
	Defines required and optional arguments for the cli and parses them out of sys.argv.

	Available Arguments are:
			Argument *--help*:
					Prints a help text for the available arguments
			Argument *--hostname*:
					Address of the host of the server
			Argument *--port*:
					Port of the host server
			Argument *--ssl*:
					Whether to use ssl or not
			Argument *--client_cert*:
					Path to the ssl certificate of the client
			Argument *--username*:
					The username to use for login
			Argument *--password*:
					The password to user for login
			Argument *--file*:
					Path to a file to execute
			Argument *arguments*
					Python code to execute directly

	Return value:
			Parsed command-line arguments

	"""
	parser = argparse.ArgumentParser(prog="ToMaTo Package Installer Creator for RexTFV",
	                                 description="This program uses a package configuration and creates an archive which can install the given packages on a ToMaTo VM via Executable Archives.",
	                                 epilog="This program uploads a probing archive to ToMaTo in order to determine package dependencies. You need a ToMaTo account to do this.",
	                                 add_help=False)
	parser.add_argument('--help', action='help')
	parser.add_argument("--hostname", "-h", required=True, help="the host of the server")
	parser.add_argument("--port", "-p", default=8000, help="the port of the server")
	parser.add_argument("--ssl", "-s", action="store_true", default=False, help="whether to use ssl")
	parser.add_argument("--client_cert", required=False, default=None, help="path of the ssl certificate")
	parser.add_argument("--username", "-U", help="the username to use for login")
	parser.add_argument("--password", "-P", help="the password to use for login")
	parser.add_argument("--target", "-t", help="the output filename.", required=True)
	parser.add_argument("--packetconfig", "-c",
	                    help='The archive configuration. This should point to a JSON file of the form [{tech:"string",site:"string",template:"string",packages:["string"]}]. Each entry must refer to a different operating system.',
	                    required=True)
	parser.add_argument("--verbose", "-v", help="verbose output", action="store_true", default=False)
	options = parser.parse_args()
	if not options.username and not options.client_cert:
		options.username = raw_input("Username: ")
	if not options.password and not options.client_cert:
		options.password = getpass.getpass("Password: ")
	if options.verbose:
		debugger.setVerbose()
	return options


options = parseArgs()
api = getConnection(createUrl("http+xmlrpc", options.hostname, options.port, options.username, options.password))
# api = getConnection(options.hostname, options.port, options.ssl, options.username, options.password, options.client_cert)

with open(options.packetconfig) as f:
	template_configs = json.load(f)

res_filename = create_archive(api, template_configs, options.target)
debugger.log(subStep="", step="", showStep=False)
debugger.log(subStep="Saved file as " + res_filename, step="Finished", showSubStep=True)

#!/usr/bin/env python

"""
getpackages script: create installer executable archives for packets, optimized for templates.

The output of this is an archive of the following structure
 |
 -> packages
   |
   -> python-pip_1.5.6-5_all.deb
   -> install packages
   -> ...
   -> including all dependencies
   -> for all templates
 -> installorder_system_a
 -> installorder_system_b
 -> ...
 -> installorder_system_z
 -> auto_exec.sh

The installorder_* files contain a list of packages in the packages directory
The auto_exec.sh script detects the correct system and the respective packet manager,
  and uses the correct installorder_* file to install the respective packets.
This means that this archive can detect the system it is being executed in, and
  install the respective version of the software. One archive to rule them all.


The result is generated in the following steps:

1) getpackages.py receives a config.
2) for each element config:
  a) create and prepare a topology of an element connected to the Internet
  b) upload a query archive to a temporary element of the respective template
  c) start topology and wait for execution to be finished
  d) get a list of packet file names and urls
     plus the system identifier for installorder_* name of the system
  e) download all respective packages locally and save the installorder_* file
3) pack the result archive.



More details


step 1: config

The config is a json file with content like this:
						[
						    {"type":"container",
						     "site":"ukl",
						     "template":"debian-8",
						     "packets":["python", "python-pip"]
						    },
						    {"type":"container",
						     "site":"ukl",
						     "template":"ubuntu-14.04",
						     "packets":["python", "python-pip"]
						    },
						    {"type":"container",
						     "site":"ukl",
						     "template":"ubuntu-16.04",
						     "packets":["python", "python-pip"]
						    }
						]
A list of ToMaTo element configurations (type, site, template),
  and the list of required packets per config (note: getpakcages will automatically add dependencies)
  If the list of packets is empty, the result will contain a system update.


step 2: querying. Done for every element of the configuration
2a) prepare topology
The topology is an element regarding the configuration, connected to an external network with internet access.

2b) query archive
The query archive uses the same auto_exec.sh file as the result archive, but a different mode.
With the prepare-install or prepare-upgrade mode, it will:
  - detect its current system and packet manager
  - update the packet manager's packet source list
  - use the packet manager to retrieve a list of packages and their urls
  - write system identifier and packages+url list to the RexTFV custom status


  FIXME: CURRENTLY, THERE IS NO PACKET MANAGER DETECTION. INSTEAD, apt-get IS ASSUMED.

2c) Start topology and wait for finish of query archive execution.

2d) Retrieve and interpret the RexTFV custom status

2e) save info
getpackages.py will download all packages from their respective URLs and save the installorder_* file

3) pack the result archive.

Here is the content of auto_exec.sh:
"""
AUTO_EXEC = """#!/bin/bash
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
	  Debian*8*)
	    DISTRO="debian_8"
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
	  Ubuntu*14.04*)
	    DISTRO="ubuntu_1404"
	    ;;
	  Ubuntu*14.10*)
	    DISTRO="ubuntu_1410"
	    ;;
	  Ubuntu*15.04*)
	    DISTRO="ubuntu_1504"
	    ;;
	  Ubuntu*15.10*)
	    DISTRO="ubuntu_1510"
	    ;;
	  Ubuntu*16.04*)
	    DISTRO="ubuntu_1604"
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
	archive_setstatus "$apt_get_ident.$os_id.$(apt-get --print-uris -y -qq install --no-install-recommends $@)"
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
"""

import os, random, textwrap, threading, tarfile, re, urllib2, sys, json
import argparse, getpass
from time import sleep
from lib import getConnection, createUrl
from lib.upload_download import upload, upload_and_use_rextfv


PROGNAME_SHORT = "rextfv-packetmanager"


def retryThreeTimes(func):
	"""
	wrapper that retries execution 3 times
	:param func:
	:return:
	"""
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
	"""
	logging
	"""
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


# working dir manager
workingdirs = []
tmplock = threading.RLock()

def get_workingdir():
	"""
	get a new directory in /tmp to work in
	:return: path of an empty temp directory
	:rtype: str
	"""
	with tmplock:
		tmpdir = "/tmp"
		workingdir = str(random.randint(10000, 99999))
		while os.path.exists(os.path.join(tmpdir, PROGNAME_SHORT + '_' + workingdir)):
			workingdir = str(random.randint(10000, 99999))
		workingdir = os.path.join(tmpdir, PROGNAME_SHORT + '_' + workingdir)
		os.makedirs(workingdir)
	global workingdirs
	workingdirs.append(workingdir)
	return workingdir

def clear_workingdirs():
	"""
	remove all working dirs
	:return:
	"""
	global workingdirs
	for dir in workingdirs:
		os.remove(dir)


class TestTopology:
	"""
	topology function wrapper for testing
	"""
	top_id = None  # topology id
	el_id = None  # element id

	template = None  # main element template
	site = None  # main element site
	type_ = None  # main element type

	api = None  # ToMaTo API wrapper

	def __init__(self, api, type_, template, site):
		"""
		create a wrapper for a topology (will be created)
		The topology consists of a main element, connected to the internet.
		:param api: ToMaTo API wrapper
		:param str type_: main element type
		:param str template: main element template
		:param str site: main element site
		"""
		self.template = template
		self.api = api
		self.site = site
		self.type_ = type_


	def _topology_json(self):
		"""
		topology to import
		:return:
		"""
		attrs = {'name': PROGNAME_SHORT+":"+self.template}
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
			"type": self.type_ + "_interface",
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
			"type": self.type_,
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
		"""
		topology_create()
		:return:
		"""
		import_res = self.api.topology_import(self._topology_json())
		self.top_id = import_res[0]
		for i in import_res[1]:
			if i[0] == 1:
				self.el_id = i[1]

	def prepare(self):
		"""
		topology_prepare()
		:return:
		"""
		self.api.topology_action(self.top_id, "prepare")

	def start(self):
		"""
		topology_start()
		:return:
		"""
		self.api.topology_action(self.top_id, "start")

	def stop(self):
		"""
		topology_stop()
		will be retried multiple times on error
		:return:
		"""
		try:
			self.api.topology_action(self.top_id, "stop")
		except:
			try:
				self.api.topology_action(self.top_id, "stop")
			except:
				self.api.topology_action(self.top_id, "stop")

	def destroy(self):
		"""
		topology_destroy()
		will be retried multiple times on error
		"""
		try:
			self.api.topology_action(self.top_id, "destroy")
		except:
			try:
				self.api.topology_action(self.top_id, "destroy")
			except:
				self.api.topology_action(self.top_id, "destroy")

	def delete(self):
		"""
		topology_remove()
		"""
		try:
			self.api.topology_remove(self.top_id)
		except:
			pass


	def uploadAndUseArchive(self, filename):
		"""
		Upload and use an executable archive
		topology actions for rextfv, combined.
		:param str filename: executable archive file
		:return:
		"""
		upload_and_use_rextfv(self.api, self.el_id, filename)

	def getArchiveResult(self):
		"""
		wait for executable archive to be finished executing
		and return custom status

		steps 2c and 2d
		:return: RexTFV custom status
		:rtype: str
		"""
		# step 2c (wait for finish)
		# wait for execution start
		timeout = 60  # timeout for start of execution
		while True:
			sleep(1)
			timeout -= 1
			if timeout == 0:
				return None		
			status = self.api.element_info(self.el_id)["rextfv_run_status"]
			if status.get("isAlive", False) or status.get("done", False):
				break
		# wait for execution finish
		while not status.get("done", False):
			if not status.get("isAlive", False):
				return None
			sleep(1)
			# step 2d: retrieval
			status = self.api.element_info(self.el_id)["rextfv_run_status"]
		return status["custom"]



class GetPacketArchive(object):
	"""
	default archive implementation
	"""
	directory = None  # directory that will be used for packing
	archive_filename = None  # target archive filename

	def __init__(self):
		"""
		create an instance working in a working directory in /tmp
		"""
		self.directory = get_workingdir()

	def _getScriptContents(self):
		"""
		content of auto_exec.sh
		:return: content of auto_exec.sh
		:rtype: str
		"""
		return AUTO_EXEC

	def _addFileToArchive(self, filename, content, path=None):
		"""
		add a file at path/filename, containing content.
		:param filename: filename (without dir)
		:param content: content of the file
		:param path: relative directory in the archive to put the file in
		:return:
		"""
		if path:
			directory = os.path.join(self.directory, path)
			if not os.path.exists(directory):
				os.mkdir(directory)
		with open(os.path.join(self.directory, filename), "w+") as f:
			f.write(content)

	def _writeMainScript(self):
		"""
		automatically called when creating.
		add auto_exec.sh
		:return:
		"""
		self._addFileToArchive("auto_exec.sh", self._getScriptContents())

	def _createArchiveFile(self):
		"""
		automatically called when creating archive.
		pack archive to the target filename.
		:return:
		"""
		with tarfile.open(self.archive_filename, 'w:gz') as tar:
			tar.add(self.directory, arcname='.')
		return self.archive_filename

	# to be implemented in a subclass
	def _writeAdditionalContents(self):
		"""
		should be overwritten by subclasses.
		automatically called when creating archive.
		last possibility to add content.
		:return:
		"""
		return

	def createArchive(self):
		"""
		call to write mainscript, add final content, and pack.
		:return:
		"""
		self._writeMainScript()
		self._writeAdditionalContents()
		return self._createArchiveFile()


class QueryArchive(GetPacketArchive):
	"""
	creator for a query archive.
	"""
	toinstall = []  # packets to install
	upgrade = False  # whether to update software. priority over toinstall.

	def __init__(self):
		super(QueryArchive, self).__init__()
		self.archive_filename = os.path.join(self.directory, "geturls.tar.gz")

	def addToInstall(self, packetname):
		"""
		add a packet to install
		:param packetname:
		:return:
		"""
		self.toinstall.append(packetname)

	def setUpgrade(self, upgrade):
		"""
		decide whether this is about installing additional software
		or updating the system
		when set, no additional software will be installed!
		:param bool upgrade: whether to do an upgrade instead of install additional software
		:return:
		"""
		self.upgrade = upgrade

	def _writeAdditionalContents(self):
		"""
		write config for auto_exec.sh
		automatically called when creating archive
		:return:
		"""
		if self.upgrade:
			self._addFileToArchive("upgrade", "")
		else:
			toinstall_str = ""
			for pac in self.toinstall:
				toinstall_str = toinstall_str + pac + "\n"
			self._addFileToArchive("toinstall", toinstall_str)

	def _interpret_result_aptget(self, lines_string):
		"""
		apt-get handler for _interpret_results
		:param lines_string:
		:return:
		"""
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
		"""
		interpret the list of packages and their urls
		switch interpreter based on packet manager ident
		:param str lines_string: packet manager's result
		:param str ident: packet manager ident
		:return: {"urls": list of urls, "order": list of packet names}
		"""
		if ident == "aptget":
			return self._interpret_result_aptget(lines_string)

	@retryThreeTimes
	def uploadAndRun(self, test_topology):
		"""
		create and prepare topology, upload this archive, start topology.
		wait for result and interpret it.
		completely destroy and remove the topology.
		On errors, retry (up to 3 times)

		steps 2a - 2c
		:param TestTopology test_topology: test topology. must not be created.
		:return: raw result (i.e., rextfv custom status)
		"""

		# see log messages for info on what is happening

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
			test_topology.delete()
		debugger.log(subStep="done.")
		return result_raw

	def getTemplateDetails(self, api, type_, template, site):
		"""
		steps 2a-2d
		:param api: ToMaTo API wrapper
		:param str type_: element type as configured
		:param str template: template  as configured
		:param str site: site as configured
		:return: OS config for PacketArchive.addOS
		"""
		# steps 2a - 2c
		custominfo = self.uploadAndRun(TestTopology(api, type_, template, site))

		# step 2d
		custominfo_splitted = custominfo.split(".", 2)
		ident = custominfo_splitted[0]
		os_id = custominfo_splitted[1]
		lines = custominfo_splitted[2]
		result = self._interpret_result(lines, ident)
		result['os_id'] = os_id

		return result


class PacketArchive(GetPacketArchive):
	"""
	creator for the final archive.

	usage:
	use addOS to add configs generated with QueryArchive.getTemplateDetails
	then create - this will automatically download the respective package files.
	"""
	configs = []  # will contain multiple results. format of entries: {'os_id','order','urls'}

	def __init__(self, filename):
		super(PacketArchive, self).__init__()
		self.archive_filename = filename

	def addOS(self, os_config):
		"""
		add a result of QueryArchive.getTemplateDetails
		:param os_config:
		:return:
		"""
		self.configs.append(os_config)

	def _writeAdditionalContents(self):
		"""
		fetch all packets and write installorder_* files
		automatically called when creating archive.
		step 2e
		:return:
		"""
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



def create_archive(api, template_configs, targetfilename):
	"""
	the main functionality of getpackages.py
	:param api: ToMaTo API wrapper
	:param dict template_configs: parsed config
	:param str targetfilename: target archive filename.
	:return: targetfilename
	"""

	# this will be used to create the target archive later
	parch = PacketArchive(targetfilename)

	# step 1 has been done when creating the template_configs argument

	# step 2
	for templ in template_configs:
		debugger.log(subStep='creating query archive', step='querying ' + templ['template'], showStep=True)
		qarch = QueryArchive()

		# configure query archive (packets or upgrade)
		qarch.setUpgrade(True)
		for pac in templ['packets']:
			qarch.setUpgrade(False)
			qarch.addToInstall(pac)

		# create archive
		qarch.createArchive()

		# 2a to 2d
		conf = qarch.getTemplateDetails(api, templ['type'], templ['template'], templ['site'])
		parch.addOS(conf)

	# step 2e and 3
	filename = parch.createArchive()
	return filename


def parseArgs():
	"""
	parse command-line arguments.
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
	parser.add_argument("--no-keyring", action="store_true", default=False, help="ignore password stored in keyring")
	parser.add_argument("--target", "-t", help="the output filename.", required=True)
	parser.add_argument("--packetconfig", "-c",
	                    help='The archive configuration. This should point to a JSON file of the form [{type:"string",site:"string",template:"string",packages:["string"]}]. Each entry must refer to a different operating system.',
	                    required=True)
	parser.add_argument("--verbose", "-v", help="verbose output", action="store_true", default=False)
	options = parser.parse_args()
	if not options.username and not options.client_cert:
		options.username = raw_input("Username: ")
	if not options.password and not options.client_cert:
		if not options.no_keyring:
			try:
				import keyring
				KEYRING_SERVICE_NAME = "ToMaTo"
				KEYRING_USER_NAME = "%s/%s" % (options.hostname, options.username)
				options.password = keyring.get_password(KEYRING_SERVICE_NAME, KEYRING_USER_NAME)
			except ImportError:
				pass
		if not options.password:
			options.password = getpass.getpass("Password: ")
	if options.verbose:
		debugger.setVerbose()
	return options


# parse arguments, read config, and connect to ToMaTo
options = parseArgs()
api = getConnection(createUrl("http+xmlrpc", options.hostname, options.port, options.username, options.password))
# api = getConnection(options.hostname, options.port, options.ssl, options.username, options.password, options.client_cert)

with open(options.packetconfig) as f:
	template_configs = json.load(f)

# do the actual work
res_filename = create_archive(api, template_configs, options.target)

# final console output
debugger.log(subStep="", step="", showStep=False)
debugger.log(subStep="Saved file as " + res_filename, step="Finished", showSubStep=True)

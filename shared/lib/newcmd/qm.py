from . import Error, dpkg, tcpserver, brctl
from util import run, CommandError, LockMatrix, params, wait, net, cmd
import collections, os, socket, json, re

locks = LockMatrix()
supported = False
initialized = False
qmVersion = None

_parameterTypes = {
	"acpi": {"convert": bool},
	"args": {"convert": str},
	"boot": {"convert": str},
	"cores": {"convert": int, "gte": 1},
	"cpu": {"convert": str, "oneOf": ["486", "Conroe", "Haswell", "Nehalem", "Opteron_G1", "Opteron_G2", "Opteron_G3", "Opteron_G4", "Opteron_G5", "Penryn", "SandyBridge", "Westmere", "athlon", "core2duo", "coreduo", "host", "kvm32", "kvm64", "pentium", "pentium2", "pentium3", "phenom", "qemu32", "qemu64"]},
	"cpuunits": {"convert": int, "gte": 0, "lte": 500000},
	"hotplug": {"convert": bool},
	"ide[0-3]": {"convert": str},
	"keyboard": {"convert": str, "oneOf": ["da", "de", "de-ch", "en-gb", "en-us", "es", "fi", "fr", "fr-be", "fr-ca", "fr-ch", "hu", "is", "it", "ja", "lt", "mk", "nl", "no", "pl", "pt", "pt-br", "sl", "sv", "tr"]},
	"kvm": {"convert": bool},
	"localtime": {"convert": bool},
	"memory": {"convert": int, "gte": 16},
	"name": {"convert": str},
	"net([12]?\d|3[01])": {"convert": str},
	"onboot": {"convert": bool},
	"ostype": {"convert": str, "oneOf": ["l24", "l26", "other", "w2k", "w2k3", "w2k8", "win7", "wvista", "wxp"]},
	"pool": {"convert": str},
	"reboot": {"convert": bool},
	"sata[0-5]": {"convert": str},
	"scsi(\d|1[0-3])": {"convert": str},
	"sockets": {"convert": int, "gte": 1},
	"startdate": {"convert": str},
	"tablet": {"convert": bool},
	"tdf": {"convert": bool},
	"vga": {"convert": str, "oneOf": ["cirrus", "std", "vmware"]}
}

class QMError(Error):
	CATEGORY="cmd_qm"
	TYPE_UNKNOWN="unknown"
	TYPE_UNKNOWN_STATUS="unknown_status"
	TYPE_INVALID_STATUS="invalid_status"
	TYPE_INVALID_PARAMETER="invalid_parameter"
	TYPE_PARAMETER_NOT_SET="parameter_not_set"
	TYPE_PARAMETER_STILL_SET="parameter_still_set"
	TYPE_UNSUPPORTED="unsupported"
	TYPE_NOT_INITIALIZED="not_initialized"
	TYPE_CONTROL="control_socket"
	TYPE_NO_SUCH_NIC="no_such_nic"
	def __init__(self, type, message, data=None):
		Error.__init__(self, category=QMError.CATEGORY, type=type, message=message, data=data)
		
class QMCommandError(QMError):
	def __init__(self, err):
		QMError.__init__(self, QMError.TYPE_UNKNOWN, "Command failed: %s" % err, {"code": err.code, "message": err.message})
	@property
	def code(self):
		return self.data.get("code")
		
def _qm(vmid, cmd, params=[]):
	try:
		with locks[vmid]:
			return run(["qm", cmd, "%d" % vmid] + map(unicode, params))
	except CommandError, err:
		raise QMCommandError(err)

class Status:
	NoSuchVm = "no_such_vm"
	Stopped = "stopped"
	Running = "running"

def _status(vmid):
	with locks[vmid]:
		try:
			res = _qm(vmid, "status").strip()
			if res == "status: stopped":
				return Status.Stopped
			if res == "status: running":
				return Status.Running
			raise QMError(QMError.TYPE_UNKNOWN_STATUS, "Unknown status: %s" % res, {"status": res})
		except QMCommandError, err:
			if err.code == 2: # No such VM
				return Status.NoSuchVm
			raise

def _checkStatus(vmid, statuses):
	if not isinstance(statuses, collections.Iterable):
		statuses = [statuses]
	status = _status(vmid)
	QMError.check(status in statuses, QMError.TYPE_INVALID_STATUS, "VM %d is in invalid status %r, expected %r" % (vmid, status, statuses))
		
def _getConfig(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	config = {}
	for line in _qm(vmid, "config").splitlines():
		key, value = line.split(": ")
		config[key] = value
	return config

def _getKvmCmd(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	return _qm(vmid, "showcmd")

def _set(vmid, **values):
	vmid = params.convert(vmid, convert=int, gte=1)
	values = params.convertMulti(values, _parameterTypes)
	with locks[vmid]:
		_checkStatus(vmid, [Status.Stopped])
		_qm(vmid, "set", sum([["-%s" % key, unicode(value)] for key, value in values.iteritems()], []))
		config = _getConfig(vmid)
		for key in values:
			QMError.check(key in config, QMError.TYPE_PARAMETER_NOT_SET, "Parameter %r has not been set" % key, {"key": key, "value": values[key]})
		
		
def _unset(vmid, keys, force=False):
	vmid = params.convert(vmid, convert=int, gte=1)
	with locks[vmid]:
		_checkStatus(vmid, [Status.Stopped])
		_qm(vmid, "set", ["-delete", " ".join(keys), "-force", str(bool(force))])
		config = _getConfig(vmid)
		for key in keys:
			QMError.check(not key in config, QMError.TYPE_PARAMETER_STILL_SET, "Parameter %r has not been removed" % key, {"key": key, "value": config.get(key)})
	
def _imageFolder(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	return "/var/lib/vz/images/%d" % vmid

def _controlPath(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	return "/var/run/qemu-server/%d.qmp" % vmid

def _checkImageFolder(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	if not os.path.exists(_imageFolder(vmid)):
		os.mkdir(_imageFolder(vmid))

def _configure(vmid, hda=None, fda=None, keyboard="en-us", localtime=False, tablet=True, highres=False, cores=1, memory=512):
	vmid = params.convert(vmid, convert=int, gte=1)
	hda = params.convert(hda, convert=str, null=True, check=os.path.exists)
	fda = params.convert(fda, convert=str, null=True, check=os.path.exists)
	# other parameters will be checked by _set
	with locks[vmid]:
		_checkStatus(vmid, Status.Stopped)
		# Set defaults
		_set(vmid, acpi=True, boot="cd", hotplug=True, name="vm%d" % vmid, ostype="other", sockets=1)
		# Set standard parameters
		_set(vmid, keyboard=keyboard, localtime=localtime, tablet=tablet, cores=cores, memory=memory, vga="std" if highres else "cirrus")
		# Setting KVM arguments not available in QM
		args = {}
		args["vnc"] = "unix:/var/run/qemu-server/%d.vnc,password" % vmid
		if fda:
			args["fda"] = fda
		if hda:
			args["hda"] = hda 
		if qmVersion < [1, 1]:
			args["chardev"] = "socket,id=qmp,path=%s,server,nowait" % _controlPath(vmid)
			args["mon"] = "chardev=qmp,mode=control"
		if args:
			argstr = " ".join(["-%s %s" % (key, value) for key, value in args.iteritems()])
			_set(vmid, args=argstr)
		
def _control(vmid, execute, timeout=10, more_args={}, **arguments):
	vmid = params.convert(vmid, convert=int, gte=1)
	timeout = params.convert(timeout, convert=float, gt=0.0)
	execute = params.convert(execute, convert=str)
	if more_args:
		arguments.update(more_args)
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		controlPath = _controlPath(vmid)
		QMError.check(os.path.exists(controlPath), QMError.TYPE_CONTROL, "Control socket does not exist", {"socket": controlPath})
		try:
			sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			sock.settimeout(timeout)
			sock.connect(controlPath)
			header = sock.recv(4096)
			try:
				header = json.loads(header)
			except Exception, exc:
				raise QMError(QMError.TYPE_CONTROL, "Received invalid header", {"socket": controlPath, "header": header})
			cmd = json.dumps({'execute': 'qmp_capabilities'})
			sock.send(cmd+"\n")
			res = sock.recv(4096)
			try:
				res = json.loads(res)
			except Exception, exc:
				raise QMError(QMError.TYPE_CONTROL, "Received invalid response", {"socket": controlPath, "response": res, "command": cmd})
			cmd = json.dumps({'execute': execute, 'arguments': arguments})
			sock.send(cmd+"\n")
			res = sock.recv(4096)
			try:
				res = json.loads(res)
				res = res["return"]
			except Exception, exc:
				raise QMError(QMError.TYPE_CONTROL, "Received invalid response", {"socket": controlPath, "response": res, "command": cmd})
			return res
		except QMError:
			raise
		except Exception, exc:
			raise QMError(QMError.TYPE_CONTROL, "Failed to connect to control socket", {"socket": controlPath})
		finally:
			sock.close()
		
def _setVncPassword(vmid, vncpassword):
	_control(vmid, 'set_password', protocol="vnc", password=vncpassword)

def _getNicNames(vmid):
	cmd = _getKvmCmd(vmid)
	names = re.findall("type=tap,id=net(\d+),ifname=([^,]+),", cmd)
	return dict((int(num), name) for num, name in names)
		
def _checkSupport():
	QMError.check(os.path.exists("/dev/kvm"), QMError.TYPE_UNSUPPORTED, "No KVM support on host")
	QMError.check(os.access("/dev/kvm", os.W_OK), QMError.TYPE_UNSUPPORTED, "No permission to use KVM")
	QMError.check(os.geteuid() == 0, QMError.TYPE_UNSUPPORTED, "Not running as root")
	QMError.check(cmd.exists("qm"), QMError.TYPE_UNSUPPORTED, "Binary qm does not exist")
	dpkg.checkSupport()
	QMError.check(dpkg.isInstalled("pve-qemu-kvm"), QMError.TYPE_UNSUPPORTED, "Package pve-qemu-kvm not installed")
	global qmVersion
	qmVersion = dpkg.getVersion("pve-qemu-kvm")
	QMError.check(([0, 15, 0] <= qmVersion < [1, 8]), QMError.TYPE_UNSUPPORTED, "Unsupported version of pve-qemu-kvm", {"version": qmVersion})
	brctl.checkSupport()
	tcpserver.checkSupport()
	return True

def _check():
	global supported, initialized
	if not initialized:
		try:
			_checkSupport()
			supported = True
			initialized = True
		except:
			supported = False
			initialized = True
			raise
	QMError.check(supported, QMError.TYPE_UNSUPPORTED, "QM is not supported")

def _public(method):
	def call(*args, **kwargs):
		_check()
		return method(*args, **kwargs)
	call.__name__ = method.__name__
	call.__doc__ = method.__doc__
	return call

######################
### Public methods ###
######################

def checkSupport():
	return _checkSupport()

@_public	
def getStatus(vmid):
	return _status(vmid)
	
@_public	
def create(vmid, **config):
	vmid = params.convert(vmid, convert=int, gte=1)
	with locks[vmid]:
		_checkStatus(vmid, Status.NoSuchVm)
		_qm(vmid, "create")
		_checkStatus(vmid, Status.Stopped)
		_checkImageFolder(vmid)
		_configure(vmid, **config)
			
@_public
def configure(vmid, **config):
	vmid = params.convert(vmid, convert=int, gte=1)
	_configure(vmid, **config)
	
@_public	
def destroy(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	with locks[vmid]:
		_checkStatus(vmid, Status.Stopped)
		_qm(vmid, "destroy")
		_checkStatus(vmid, Status.NoSuchVm) 
	
@_public	
def reset(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		_qm(vmid, "reset")
		_checkStatus(vmid, Status.Running) 

@_public	
def stop(vmid, force=True, timeout=30):
	vmid = params.convert(vmid, convert=int, gte=1)
	force = params.convert(force, convert=bool)
	timeout = params.convert(timeout, convert=int, gte=0)
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		_qm(vmid, "shutdown", ["-forceStop", str(force), "-timeout", str(timeout)])
		_checkStatus(vmid, Status.Stopped)

@_public	
def start(vmid):
	vmid = params.convert(vmid, convert=int, gte=1)
	with locks[vmid]:
		_checkStatus(vmid, Status.Stopped)
		_qm(vmid, "start")
		_checkStatus(vmid, Status.Running)
		try:
			for ifname in _getNicNames(vmid).values():
				wait.waitFor(lambda :net.ifaceExists(ifname), failCond=lambda :_status() != Status.Running)
				bridge = net.ifaceBridge(ifname)
				if bridge:
					brctl.detach(bridge, ifname)
		except:
			stop(vmid)
			raise
		
@_public
def startVnc(vmid, vncpassword, vncport):
	vmid = params.convert(vmid, convert=int, gte=1)
	vncpassword = params.convert(vncpassword, convert=unicode)
	vncport = params.convert(vncport, convert=int, gte=1, lt=2**16)
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		_setVncPassword(vmid, vncpassword)
		return tcpserver.start(vncport, ["qm", "vncproxy", str(vmid)])
	
@_public
def stopVnc(pid):
	tcpserver.stop(pid)
	
@_public
def addNic(vmid, num, bridge, model="e1000", mac=None):
	vmid = params.convert(vmid, convert=int, gte=1)
	num = params.convert(num, convert=int, gte=0, lte=31)
	bridge = params.convert(bridge, convert=str)
	model = params.convert(model, convert=str, oneOf=["e1000", "i82551", "rtl8139"])
	mac = params.convert(mac, convert=str, regExp="^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", null=True)
	_set(vmid, **{("net%d" % num): "%s%s,bridge=%s" % (model, ("=%s" % mac) if mac else "", bridge)})
	
@_public
def delNic(vmid, num):
	_unset(vmid, ["net%d" % num])
	
@_public
def getNicList(vmid):
	return _getNicNames(vmid).keys()

@_public
def getNicName(vmid, num):
	names = _getNicNames(vmid)
	QMError.check(num in names, QMError.TYPE_NO_SUCH_NIC, "No such nic: %d" % num, {"vmid": vmid, "num": num})
	return names[num]

@_public
def sendKey(vmid, key, hold=10):
	_control(vmid, "send-key", keys=[{"type": "qcode", "data": k} for k in key.split("-")], more_args={"hold-time": hold})

@_public
def createScreenshot(vmid, filename):
	_control(vmid, "screendump", filename=filename)
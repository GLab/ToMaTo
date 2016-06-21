from . import Error, dpkg, brctl, websockify, qemu_img, SUPPORT_CHECK_PERIOD
from util import spawnDaemon, run, CommandError, LockMatrix, params, wait, net, cmd, proc, cache
import collections, os, socket, json, re

locks = LockMatrix()
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
	CODE_UNKNOWN="qm.unknown"
	CODE_UNKNOWN_STATUS="qm.unknown_status"
	CODE_INVALID_STATUS="qm.invalid_status"
	CODE_INVALID_PARAMETER="qm.invalid_parameter"
	CODE_PARAMETER_NOT_SET="qm.parameter_not_set"
	CODE_PARAMETER_STILL_SET="qm.parameter_still_set"
	CODE_UNSUPPORTED="qm.unsupported"
	CODE_NOT_INITIALIZED="qm.not_initialized"
	CODE_CONTROL="qm.control_socket"
	CODE_NO_SUCH_NIC="qm.no_such_nic"
	CODE_NIC_ALREADY_EXISTS="qm.nix_already_exists"
	CODE_COMMAND="qm.command"
	CODE_STILL_RUNNING="qm.still_running"

def _qm(vmid, cmd, params=None):
	if not params: params = []
	try:
		return run(["qm", cmd, "%d" % vmid] + map(unicode, params))
	except CommandError, err:
		raise QMError(QMError.CODE_COMMAND, "Failed to execute command", err.data)

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
			raise QMError(QMError.CODE_UNKNOWN_STATUS, "Unknown status: %s" % res, {"status": res})
		except QMError, err:
			if err.code == QMError.CODE_COMMAND and err.data.get('error') == 2: # No such VM
				return Status.NoSuchVm
			raise

def _checkStatus(vmid, statuses):
	if not isinstance(statuses, collections.Iterable):
		statuses = [statuses]
	status = _status(vmid)
	QMError.check(status in statuses, QMError.CODE_INVALID_STATUS, "VM is in invalid status", {"vmid": vmid, "status": status, "expected": statuses})


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

def _getPid(vmid):
	try:
		with open("/var/run/qemu-server/%d.pid" % vmid) as fp:
			pid = int(fp.readline().strip())
		return pid
	except IOError:
		raise QMError(QMError.INVALID_STATE, "Pid file does not exist", {"vmid": vmid})

def _set(vmid, **values):
	vmid = params.convert(vmid, convert=int, gte=1)
	values = params.convertMulti(values, _parameterTypes)
	_qm(vmid, "set", sum([["-%s" % key, unicode(value)] for key, value in values.iteritems()], []))
	config = _getConfig(vmid)
	for key in values:
		QMError.check(key in config, QMError.CODE_PARAMETER_NOT_SET, "Parameter %r has not been set" % key, {"key": key, "value": values[key]})
		
		
def _unset(vmid, keys, force=False):
	vmid = params.convert(vmid, convert=int, gte=1)
	_qm(vmid, "set", ["-delete", " ".join(keys), "-force", str(bool(force))])
	config = _getConfig(vmid)
	for key in keys:
		QMError.check(not key in config, QMError.CODE_PARAMETER_STILL_SET, "Parameter %r has not been removed" % key, {"key": key, "value": config.get(key)})
	
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

def _configure(vmid, hda=None, hdb=None, fda=None, keyboard="en-us", localtime=False, tablet=True, highres=False, cores=1, memory=512):
	vmid = params.convert(vmid, convert=int, gte=1)
	hda = params.convert(hda, convert=str, null=True, check=qemu_img.check)
	hdb = params.convert(hdb, convert=str, null=True, check=qemu_img.check)
	fda = params.convert(fda, convert=str, null=True, check=qemu_img.check)
	# other parameters will be checked by _set
	options = {}
	# Set defaults
	options.update(acpi=True, boot="cd", hotplug=True, name="vm%d" % vmid, ostype="other", sockets=1)
	# Set standard parameters
	options.update(keyboard=keyboard, localtime=localtime, tablet=tablet, cores=cores, memory=memory, vga="std" if highres else "cirrus")
	# Setting KVM arguments not available in QM
	args = {}
	args["vnc"] = "unix:/var/run/qemu-server/%d.vnc,password" % vmid
	if fda:
		args['drive'] = "file=%s,index=0,if=floppy,cache=writethrough" % fda
	if hdb:
		args["hdb"] = hdb
	if hda:
		args["hda"] = hda
	if qmVersion < [1, 1]:
		args["chardev"] = "socket,id=qmp,path=%s,server,nowait" % _controlPath(vmid)
		args["mon"] = "chardev=qmp,mode=control"
	if args:
		argstr = " ".join(["-%s %s" % (key, value) for key, value in args.iteritems()])
		options.update(args=argstr)
	_set(vmid, **options)
		
def _control(vmid, execute, timeout=10, more_args=None, **arguments):
	if not more_args: more_args = {}
	vmid = params.convert(vmid, convert=int, gte=1)
	timeout = params.convert(timeout, convert=float, gt=0.0)
	execute = params.convert(execute, convert=str)
	if more_args:
		arguments.update(more_args)
	controlPath = _controlPath(vmid)
	QMError.check(os.path.exists(controlPath), QMError.CODE_CONTROL, "Control socket does not exist", {"socket": controlPath})
	sock = None
	try:
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock.settimeout(timeout)
		sock.connect(controlPath)
		header = sock.recv(4096)
		try:
			header = json.loads(header)
		except Exception, exc:
			raise QMError(QMError.CODE_CONTROL, "Received invalid header", {"socket": controlPath, "header": header})
		cmd = json.dumps({'execute': 'qmp_capabilities'})
		sock.send(cmd+"\n")
		res = sock.recv(4096)
		try:
			res = json.loads(res)
		except Exception, exc:
			raise QMError(QMError.CODE_CONTROL, "Received invalid response", {"socket": controlPath, "response": res, "command": cmd})
		cmd = json.dumps({'execute': execute, 'arguments': arguments})
		sock.send(cmd+"\n")
		res = sock.recv(4096)
		try:
			res = json.loads(res)
			res = res["return"]
		except Exception, exc:
			raise QMError(QMError.CODE_CONTROL, "Received invalid response", {"socket": controlPath, "response": res, "command": cmd})
		return res
	except QMError:
		raise
	except Exception, exc:
		raise QMError(QMError.CODE_CONTROL, "Failed to connect to control socket", {"socket": controlPath})
	finally:
		if sock:
			sock.close()
		
def _setVncPassword(vmid, vncpassword):
	_control(vmid, 'set_password', protocol="vnc", password=vncpassword)

def _getNicNames(vmid):
	cmd = _getKvmCmd(vmid)
	names = re.findall("type=tap,id=net(\d+),ifname=([^,]+),", cmd)
	return dict((int(num), name) for num, name in names)

@cache.cached(timeout=SUPPORT_CHECK_PERIOD)
def _check():
	QMError.check(os.path.exists("/dev/kvm"), QMError.CODE_UNSUPPORTED, "No KVM support on host")
	QMError.check(os.access("/dev/kvm", os.W_OK), QMError.CODE_UNSUPPORTED, "No permission to use KVM")
	QMError.check(os.geteuid() == 0, QMError.CODE_UNSUPPORTED, "Not running as root")
	QMError.check(cmd.exists("qm"), QMError.CODE_UNSUPPORTED, "Binary qm does not exist")
	QMError.check(cmd.exists("socat"), QMError.CODE_UNSUPPORTED, "Binary socat does not exist")
	dpkg.checkSupport()
	QMError.check(dpkg.isInstalled("pve-qemu-kvm"), QMError.CODE_UNSUPPORTED, "Package pve-qemu-kvm not installed")
	global qmVersion
	qmVersion = dpkg.getVersion("pve-qemu-kvm")
	QMError.check(([0, 15, 0] <= qmVersion < [2, 3]), QMError.CODE_UNSUPPORTED, "Unsupported version of pve-qemu-kvm", {"version": qmVersion})
	brctl.checkSupport()
	return True

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
	return _check()

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
	with locks[vmid]:
		_checkStatus(vmid, Status.Stopped)
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
def start(vmid, detachInterfaces=True):
	vmid = params.convert(vmid, convert=int, gte=1)
	if not net.bridgeExists("dummy"):
		brctl.create("dummy")
	with locks[vmid]:
		_checkStatus(vmid, Status.Stopped)
		_qm(vmid, "start")
		_checkStatus(vmid, Status.Running)
		try:
			for ifname in _getNicNames(vmid).values():
				wait.waitFor(lambda :net.ifaceExists(ifname), failCond=lambda :_status(vmid) != Status.Running)
				bridge = net.ifaceBridge(ifname)
				if bridge and detachInterfaces:
					brctl.detach(bridge, ifname)
		except:
			stop(vmid)
			raise
		
@_public
def startVnc(vmid, vncpassword, vncport, websockifyPort=None, websockifyCert=None):
	vmid = params.convert(vmid, convert=int, gte=1)
	vncpassword = params.convert(vncpassword, convert=unicode)
	vncport = params.convert(vncport, convert=int, gte=1, lt=2**16)
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		_setVncPassword(vmid, vncpassword)
		vncPid = spawnDaemon(["socat", "TCP-LISTEN:%d,reuseaddr,fork" % vncport, "UNIX-CLIENT:/var/run/qemu-server/%d.vnc" % vmid])
		websockifyPid = None
		try:
			if websockifyPort:
				websockifyPid = websockify.start(websockifyPort, vncport, websockifyCert)
		except:
			stopVnc(vncPid)
			raise
		return vncPid, websockifyPid

@_public
def stopVnc(pid, websockifyPid=None):
	proc.autoKill(pid, group=True)
	QMError.check(not proc.isAlive(pid), QMError.CODE_STILL_RUNNING, "Failed to stop socat")
	if websockifyPid:
		websockify.stop(websockifyPid)
	
@_public
def addNic(vmid, num, bridge="dummy", model="e1000", mac=None):
	vmid = params.convert(vmid, convert=int, gte=1)
	num = params.convert(num, convert=int, gte=0, lte=31)
	bridge = params.convert(bridge, convert=str)
	model = params.convert(model, convert=str, oneOf=["e1000", "i82551", "rtl8139"])
	mac = params.convert(mac, convert=str, regExp="^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", null=True)
	with locks[vmid]:
		_checkStatus(vmid, Status.Stopped)
		if num in getNicList(vmid):
			raise QMError(QMError.CODE_NIC_ALREADY_EXISTS, "Nic already exists", {"vmid": vmid, "num": num})
		_set(vmid, **{("net%d" % num): "%s%s%s" % (model, ("=%s" % mac) if mac else "", (",bridge=%s" % bridge) if bridge else "")})

@_public
def delNic(vmid, num):
	with locks[vmid]:
		_checkStatus(vmid, Status.Stopped)
		if not num in getNicList(vmid):
			raise QMError(QMError.CODE_NO_SUCH_NIC, "No such nic", {"vmid": vmid, "num": num})
		_unset(vmid, ["net%d" % num])
	
@_public
def getNicList(vmid):
	with locks[vmid]:
		_checkStatus(vmid, [Status.Stopped, Status.Running])
		return _getNicNames(vmid).keys()

@_public
def getNicName(vmid, num):
	with locks[vmid]:
		_checkStatus(vmid, [Status.Stopped, Status.Running])
		names = _getNicNames(vmid)
	QMError.check(num in names, QMError.CODE_NO_SUCH_NIC, "No such nic", {"vmid": vmid, "num": num})
	return names[num]

@_public
def sendKey(vmid, key, hold=10):
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		_control(vmid, "send-key", keys=[{"type": "qcode", "data": k} for k in key.split("-")], more_args={"hold-time": hold})

@_public
def createScreenshot(vmid, filename):
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		_control(vmid, "screendump", filename=filename)

Statistics = proc.Statistics

@_public
def getStatistics(vmid):
	with locks[vmid]:
		_checkStatus(vmid, Status.Running)
		pid = _getPid(vmid)
		return proc.getStatistics(pid)

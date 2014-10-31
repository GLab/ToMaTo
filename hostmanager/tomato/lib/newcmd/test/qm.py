
import unittest, os, shutil, tempfile, sys
from .. import qm, vfat, netstat
from ..util import net, proc

if sys.version_info < (2, 7):
	import unittest2 as unittest

VMID_RANGE = xrange(9000, 10000)
TEMPLATE_PATHS = ['/var/lib/vz/template/qemu', '/var/lib/tomato/templates']
PORT_RANGE = xrange(2000, 3000)
WEBSOCKIFY_CERT = '/etc/tomato/server.pem'
if not os.path.exists(WEBSOCKIFY_CERT):
	WEBSOCKIFY_CERT = None

class Test(unittest.TestCase):

	def setUp(self):
		qm.checkSupport()
		self.vmid = None
		for vmid in VMID_RANGE:
			if qm.getStatus(vmid) == qm.Status.NoSuchVm:
				self.vmid = vmid
				break
		self.assertTrue(self.vmid, "No free vmid found")
		self.template = None
		for path in TEMPLATE_PATHS:
			for name in os.listdir(path):
				if os.path.splitext(name)[1] in [".qcow2", ".qcow"]:
					self.template = os.path.join(path, name)
					break
		self.assertTrue(self.template, "No KVM template found")
		self.temp = tempfile.mkdtemp()
		self.hda = os.path.join(self.temp, "hda")
		self.fda = os.path.join(self.temp, "fda")
		self.pids = []
		self.ports = []

	def _getPort(self):
		for port in PORT_RANGE:
			if netstat.isPortFree(port) and not port in self.ports:
				self.ports.append(port)
				return port

	def tearDown(self):
		status = qm.getStatus(self.vmid)
		if status == qm.Status.Running:
			qm.stop(self.vmid)
			qm.destroy(self.vmid)
		elif status == qm.Status.Stopped:
			qm.destroy(self.vmid)
		if os.path.exists(self.temp):
			shutil.rmtree(self.temp)
		for pid in self.pids:
			proc.autoKill(pid, True)

	def test_create_destroy(self):
		self.assertRaises(qm.QMError, qm.destroy, self.vmid)
		# Simple create with no parameters
		qm.create(self.vmid)
		self.assertEqual(qm.getStatus(self.vmid), qm.Status.Stopped)
		self.assertRaises(qm.QMError, qm.create, self.vmid)
		qm.destroy(self.vmid)
		# Create with all possible parameters
		shutil.copy(self.template, self.hda)
		vfat.create(self.fda, size=512)
		qm.create(self.vmid, keyboard="de", localtime=True, tablet=False, highres=True, cores=2, memory=256, hda=self.hda, fda=self.fda)

	def test_start_stop(self):
		self.assertRaises(qm.QMError, qm.start, self.vmid)
		self.assertRaises(qm.QMError, qm.stop, self.vmid)
		# Create simple VM
		shutil.copy(self.template, self.hda)
		vfat.create(self.fda, size=512)
		qm.create(self.vmid, keyboard="de", hda=self.hda, fda=self.fda)
		qm.addNic(self.vmid, 1)
		self.assertRaises(qm.QMError, qm.stop, self.vmid)
		# Starting VM
		qm.start(self.vmid)
		self.assertEqual(qm.getStatus(self.vmid), qm.Status.Running)
		self.assertRaises(qm.QMError, qm.start, self.vmid)
		self.assertRaises(qm.QMError, qm.destroy, self.vmid)
		self.assertRaises(qm.QMError, qm.create, self.vmid)
		qm.stop(self.vmid)
		self.assertEqual(qm.getStatus(self.vmid), qm.Status.Stopped)
		self.assertRaises(qm.QMError, qm.stop, self.vmid)

	def test_statistics(self):
		self.assertRaises(qm.QMError, qm.getStatistics, self.vmid)
		# Create simple VM
		shutil.copy(self.template, self.hda)
		vfat.create(self.fda, size=512)
		qm.create(self.vmid, keyboard="de", hda=self.hda, fda=self.fda)
		qm.addNic(self.vmid, 1)
		self.assertRaises(qm.QMError, qm.getStatistics, self.vmid)
		# Starting VM
		qm.start(self.vmid)
		# Get statistics
		stats = qm.getStatistics(self.vmid)
		self.assertEquals(stats.__class__, qm.Statistics)
		self.assertNotEqual(stats.memory_used, 0)
		self.assertNotEqual(stats.cputime_total, 0)

	def test_interfaces(self):
		self.assertRaises(qm.QMError, qm.addNic, self.vmid, 1)
		self.assertRaises(qm.QMError, qm.delNic, self.vmid, 1)
		self.assertRaises(qm.QMError, qm.getNicName, self.vmid, 1)
		self.assertRaises(qm.QMError, qm.getNicList, self.vmid)
		# Create simple VM
		shutil.copy(self.template, self.hda)
		vfat.create(self.fda, size=512)
		qm.create(self.vmid, keyboard="de", hda=self.hda, fda=self.fda)
		# Adding and removing interfaces
		self.assertEqual(qm.getNicList(self.vmid), [])
		self.assertRaises(qm.QMError, qm.delNic, self.vmid, 1)
		qm.addNic(self.vmid, 1)
		self.assertEqual(qm.getNicList(self.vmid), [1])
		self.assertTrue(qm.getNicName(self.vmid, 1))
		self.assertRaises(qm.QMError, qm.addNic, self.vmid, 1)
		qm.delNic(self.vmid, 1)
		self.assertEqual(qm.getNicList(self.vmid), [])
		self.assertRaises(qm.QMError, qm.delNic, self.vmid, 1)
		# Checking for at least 4 simultaneous interfaces
		for i in xrange(1, 5):
			qm.addNic(self.vmid, i)
		self.assertEqual(len(qm.getNicList(self.vmid)), 4)
		for i in xrange(1, 5):
			qm.delNic(self.vmid, i)
		# Check for NIC 31
		qm.addNic(self.vmid, 31)
		qm.delNic(self.vmid, 31)
		# Checking different models
		qm.addNic(self.vmid, 1, model="e1000")
		qm.addNic(self.vmid, 2, model="i82551")
		qm.addNic(self.vmid, 3, model="rtl8139")
		# Starting VM
		qm.start(self.vmid)
		self.assertRaises(qm.QMError, qm.delNic, self.vmid, 1)
		self.assertRaises(qm.QMError, qm.addNic, self.vmid, 4)
		self.assertTrue(qm.getNicName(self.vmid, 1))
		self.assertTrue(net.ifaceExists(qm.getNicName(self.vmid, 1)))
		self.assertFalse(net.ifaceBridge(qm.getNicName(self.vmid, 1)))

	def test_vnc(self):
		self.assertRaises(qm.QMError, qm.startVnc, self.vmid, "password", self._getPort())
		# Create simple VM
		shutil.copy(self.template, self.hda)
		vfat.create(self.fda, size=512)
		qm.create(self.vmid, keyboard="de", hda=self.hda, fda=self.fda)
		self.assertRaises(qm.QMError, qm.startVnc, self.vmid, "password", self._getPort())
		# Starting VM
		qm.start(self.vmid)
		# Starting VNC only
		vncport = self._getPort()
		vncpid, _ = qm.startVnc(self.vmid, "password", vncport)
		self.pids.append(vncpid)
		self.assertTrue(vncpid)
		self.assertFalse(netstat.isPortFree(vncport))
		self.assertTrue(netstat.isPortUsedBy(vncport, vncpid))
		# Stopping VNC
		qm.stopVnc(vncpid)
		self.assertTrue(netstat.isPortFree(vncport))
		# Starting VNC+websockify
		websockifyPort = self._getPort()
		vncpid, websockifyPid = qm.startVnc(self.vmid, "password", vncport, websockifyPort, WEBSOCKIFY_CERT)
		self.pids.append(vncpid)
		self.pids.append(websockifyPid)
		self.assertTrue(vncpid)
		self.assertTrue(websockifyPid)
		self.assertFalse(netstat.isPortFree(vncport))
		self.assertTrue(netstat.isPortUsedBy(vncport, vncpid))
		self.assertFalse(netstat.isPortFree(websockifyPort))
		self.assertTrue(netstat.isPortUsedBy(websockifyPort, websockifyPid))
		qm.stopVnc(vncpid, websockifyPid)
		self.assertTrue(netstat.isPortFree(vncport))
		self.assertTrue(netstat.isPortFree(websockifyPort))

	def test_configure(self):
		self.assertRaises(qm.QMError, qm.configure, self.vmid)
		# Create simple VM
		shutil.copy(self.template, self.hda)
		vfat.create(self.fda, size=512)
		qm.create(self.vmid, keyboard="de", hda=self.hda, fda=self.fda)
		qm.configure(self.vmid, keyboard="de", localtime=True, tablet=False, highres=True, cores=2, memory=256, hda=self.hda, fda=self.fda)
		qm.start(self.vmid)
		self.assertRaises(qm.QMError, qm.configure, self.vmid)
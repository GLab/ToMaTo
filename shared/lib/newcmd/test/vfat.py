
import unittest, os, shutil, tempfile
from .. import vfat

class Test(unittest.TestCase):

	def setUp(self):
		vfat.checkSupport()
		self.temp = tempfile.mkdtemp()
		self.mountpoint = os.path.join(self.temp, "mountpoint")
		os.mkdir(self.mountpoint)
		self.image = os.path.join(self.temp, "image")
		self.testfile = os.path.join(self.mountpoint, "test")

	def tearDown(self):
		vfat.unmount(self.mountpoint, ignoreUnmounted=True)
		if os.path.exists(self.temp):
			shutil.rmtree(self.temp)

	def test_create(self):
		# Simple create with no parameters
		vfat.create(self.image, "512")
		self.assertTrue(os.path.exists(self.image))

	def test_mount(self):
		# Create empty image
		vfat.create(self.image, "512")
		# Try simple mount
		vfat.mount(self.image, self.mountpoint)
		self.assertTrue(vfat.isMounted(self.mountpoint))
		# Try to remount
		self.assertRaises(vfat.VFatError, vfat.mount, self.image, self.mountpoint)

	def test_umount(self):
		# Create and mount image
		vfat.create(self.image, "512")
		vfat.mount(self.image, self.mountpoint)
		self.assertTrue(vfat.isMounted(self.mountpoint))
		# Unmount image
		vfat.unmount(self.mountpoint)
		self.assertFalse(vfat.isMounted(self.mountpoint))
		# Check duplicate unmount
		self.assertRaises(vfat.VFatError, vfat.unmount, self.mountpoint)
		# Check duplicate unmount with ignoreUnmounted=True
		vfat.unmount(self.mountpoint, ignoreUnmounted=True) #no error expected

	def test_mount_rw(self):
		# Create and mount image
		vfat.create(self.image, "512")
		vfat.mount(self.image, self.mountpoint)
		self.assertTrue(vfat.isMounted(self.mountpoint))
		# Test read and write
		self.assertFalse(os.path.exists(self.testfile))
		with open(self.testfile, 'w') as fp:
			fp.write("test1")
		with open(self.testfile, 'r') as fp:
			self.assertEqual("test1", fp.read())
		vfat.unmount(self.mountpoint)
		self.assertFalse(os.path.exists(self.testfile))
		vfat.mount(self.image, self.mountpoint, sync=True)
		with open(self.testfile, 'r') as fp:
			self.assertEqual("test1", fp.read())

	def test_mount_ro(self):
		# Create and mount image
		vfat.create(self.image, "512")
		vfat.mount(self.image, self.mountpoint)
		with open(self.testfile, 'w') as fp:
			fp.write("test1")
		vfat.unmount(self.mountpoint)
		vfat.mount(self.image, self.mountpoint, readOnly=True)
		self.assertTrue(vfat.isMounted(self.mountpoint))
		# Test read and write
		self.assertRaises(IOError, open,self.testfile, 'w')
		self.assertTrue(open(self.testfile, 'r'))

	def test_error_realpath(self):
		# Mounts to symlinks would not show as mounted
		link = os.path.join(self.temp, "symlink")
		os.symlink(self.mountpoint, link)
		vfat.create(self.image, "512")
		vfat.mount(self.image, link)
		self.assertTrue(vfat.isMounted(self.mountpoint))
		self.assertTrue(vfat.isMounted(link))

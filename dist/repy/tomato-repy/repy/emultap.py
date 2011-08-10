from fcntl import ioctl
import os, struct, atexit, thread
from threading import Thread, Lock, RLock, Condition
import select

TUNSETIFF = 0x400454ca
IFF_TUN   = 0x0001
IFF_TAP   = 0x0002
IFF_NO_PI = 0x1000 #prevent kernel from adding 4 additional bytes

DEFAULT_MTU = 1518

class TunTapDevice:
    """
    This class represents a tun/tap device and offers to write to it and read
    from it. A networking interface will be created and this object will serve
    as its wire side.
    Creating a tun/tap device requires higher privileges so the __init__ might
    fail with an IOError.
    """
    def __init__(self, ifname, mode = IFF_TAP | IFF_NO_PI, dev = '/dev/net/tun', mtu = DEFAULT_MTU, alias=None):
        """
        Creates a new tun/tap device. A new device will be created by cloning
        the default tun/tap device with a given mode.
        The name is the future name of the networking interface and the caller
        must make sure that the name is not in use.
        The mode determines whether the device should be a tun or a tap device
        and whether additional packet information should be added or not. The
        mode must be either IFF_TUN or IFF_TAP with an additional IFF_NO_PI 
        added to supress the additional packet information.
        The default tun/tap device to clone can be given by its complete path
        in the dev variable.
        The mtu parameter defines the maximal size of a packet plus its 
        additional packet information. This value is used when reading from the
        device.
        If the process lacks the needed rights an IOError is raised.
        """
        self.ifname = ifname
        self.mode = mode
        self.dev = dev
        self.mtu = mtu
        self.alias = alias
        fd = os.open(dev, os.O_RDWR)
        ifs = ioctl(fd, TUNSETIFF, struct.pack("16sH", self.ifname, self.mode))
        self.ifname = ifs[:16].strip("\x00")
        self._fd = fd
        atexit.register(self.close)
    def fileno(self):
        return self._fd
    def _check_open(self):
        if not self._fd:
            raise Exception("Device has been closed")        
    def _read(self):
        self._check_open()
        data = os.read(self._fd, self.mtu)
        return data
    def _write(self, data):
        self._check_open()
        os.write(self._fd, data)
    def close(self):
        '''
        Closes the tun/tap device. This is a final action, this instance can
        not be opened again.
        '''
        if self._fd:
            os.close(self._fd)
            self._fd = None
    def _ifup(self):
        self._check_open()
        os.system("ip link set %s up" % self.ifname)
    def _ifdown(self):
        self._check_open()
        os.system("ip link set %s down" % self.ifname)
    def send(self, data):
        '''
        Sends a packet to the device. The data must be byte string, otherwise
        an exception will be raised.
        '''
        self._write(data)
    def info(self):
        info={}
        if self.mode & IFF_TAP:
            info["type"] = "tap"
        elif self.mode & IFF_TUN:
            info["type"] = "tun"
        else:
            info["type"] = "unknown"
        info["packet_information"] = self.mode & IFF_NO_PI == 0
        info["open"] = self._fd != None
        info["mtu"] = self.mtu
        return info
    def read(self):
        self._check_open()
        return self._read()
    
devices = {}

# public method, but not for repy code
def device_create(ifname, mode=IFF_TAP|IFF_NO_PI, alias=None, mtu=DEFAULT_MTU, dev="/dev/net/tun"):
    if alias:
        name = alias
    else:
        name = ifname
    dev = TunTapDevice(ifname, mode, alias=name, mtu=mtu, dev=dev)
    devices[name] = dev

def _get_device(name):
    if not name in devices:
        raise Exception("No such device: %s" % name)
    return devices[name]

# public method, but not for repy code
def device_destroy(name):
    _get_device(name).close()
    del devices[name]    
    
# public method for repy code
def device_send(name, data):
    _get_device(name).send(data)

def _read(devs, timeout=None):
    ready = select.select(devs, [], [], timeout)[0]
    if ready:
        dev = ready[0]
        return (dev.alias, dev.read())
    return (None, None)

# public method for repy code
def device_read(name, timeout=None):
    return _read([_get_device(name)], timeout)[1]

# public method for repy code
def device_read_any(timeout=None):
    return _read(devices.values(), timeout)
    
# public method for repy code
def device_list():
    devs = devices.keys()
    devs.sort()
    return devs

# public method for repy code
def device_info(name):
    return _get_device(name).info()
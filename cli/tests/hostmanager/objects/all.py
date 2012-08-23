from openvz import check as checkOpenVZ
from kvmqm import check as checkKVMQM
from repy import check as checkRepy
from tinc import check as checkTinc
from udp_tunnel import check as checkUDPTunnel
from external_network import check as checkExternalNetwork
from bridge import check as checkBridge

if __name__ == "__main__":
	try:
		checkOpenVZ(shellError=False)
		checkKVMQM(shellError=False)
		checkRepy(shellError=False)
		checkTinc(shellError=False)
		checkUDPTunnel(shellError=False)
		checkExternalNetwork(shellError=False)
		checkBridge(shellError=False)
	except:
		import traceback
		traceback.print_exc()
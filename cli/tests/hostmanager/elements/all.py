from openvz import check as checkOpenVZ
from kvmqm import check as checkKVMQM
from repy import check as checkRepy

if __name__ == "__main__":
	try:
		checkOpenVZ(shellError=False)
		checkKVMQM(shellError=False)
		checkRepy(shellError=False)
	except:
		import traceback
		traceback.print_exc()
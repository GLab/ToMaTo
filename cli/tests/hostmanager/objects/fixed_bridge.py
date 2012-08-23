from external_network import check as checkExternalNetwork

if __name__ == "__main__":
	try:
		#external network test uses fixed_bridge
		checkExternalNetwork(shellError=False)
	except:
		import traceback
		traceback.print_exc()
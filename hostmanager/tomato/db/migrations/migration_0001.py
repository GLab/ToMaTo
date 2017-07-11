from ...lib.newcmd.util import run, CommandError, cmd, proc
from ... import config
import os
from ...modelsold import User, Resource, Template, Network, Element, External_Network, KVM, KVM_Interface, KVMQM, KVMQM_Interface, OpenVZ, OpenVZ_Interface, Repy, Repy_Interface, Tinc, UDP_Tunnel, VpnCloud, Connection, Bridge, Fixed_Bridge, UsageRecord, UsageStatistics, ResourceInstance

'''
Migration through 2 Steps:
1. Create old elements in the new database with all attributes except for references
2. Update all elements to integrate the old references and relationships between them.
'''

def migrate():

	#Create old elements in the new database with all attributes except for references
	from django.core.management import call_command
	call_command('syncdb', verbosity=0)

	userMapping = {}
	from ...user import User as NewUser
	for user in User.objects.filter():
		newUser = NewUser(
			id="{0:0{1}x}".format(user.id, 24),
			name=user.name)
		newUser.save()
		userMapping[user.id]=newUser

	resourceMapping = {}
	from ...resources import Resource as NewResource
	for resource in Resource.objects.filter():
		if resource.type not in ["network","template"]:
			newResource = NewResource(
				id="{0:0{1}x}".format(resource.id, 24),
				attrs=resource.attrs,
				type=resource.type)
			newResource.save()
			resourceMapping[resource.id] = newResource

	from ...resources.template import Template as NewTemplate
	for template in Template.objects.filter():
		newTemplate = NewTemplate(
				id="{0:0{1}x}".format(template.id, 24),
				attrs=resource.attrs,
				type=resource.type,
				owner=userMapping[template.owner.id],
				tech=template.tech,
				name=template.name,
				preference=template.preference,
				urls=template.urls,
				checksum=template.checksum,
				size=template.size,
				popularity=template.popularity,
				ready=template.ready,
				kblang=template.kblang)
		newTemplate.save()
		resourceMapping[template.id] = newTemplate

	from ...resources.network import Network as NewNetwork
	for network in Network.objects.filter():
		newNetwork = NewNetwork(
				id="{0:0{1}x}".format(network.id, 24),
				attrs=resource.attrs,
				type=resource.type,
				owner=userMapping[network.owner.id],
				kind=network.kind,
				bridge=network.bridge,
				preference=network.preference)
		resourceMapping[network.id] = newNetwork

	elementMapping = {}
	from ...elements.external_network import External_Network as NewExternalNetwork
	for externalNetwork in External_Network.objects.filter():
		newExternalNetwork = NewExternalNetwork(
			id="{0:0{1}x}".format(externalNetwork.id, 24),
			owner=userMapping[externalNetwork.owner.id],
			state=externalNetwork.state,
			timeout=externalNetwork.timeout,
			network=resourceMapping[externalNetwork.network.id]
		)
		elementMapping[externalNetwork.id] = newExternalNetwork

		
	from ...elements.kvmqm import KVMQM as New_KVMQM
	for kvmqm in KVMQM.objects.filter():
		newKVMQM = New_KVMQM(
			id="{0:0{1}x}".format(kvmqm.id, 24),
			owner=userMapping[kvmqm.owner.id],
			state=kvmqm.state,
			timeout=kvmqm.timeout,
			vmid=kvmqm.vmid,
			websocket_port=kvmqm.websocket_port,
			websocket_pid=kvmqm.websocket_pid,
			vncport=kvmqm.vncport,
			vncpid=kvmqm.vncpid,
			vncpassword=kvmqm.vncpassword,
			cpus=kvmqm.cpus,
			ram=kvmqm.ram,
			kblang=kvmqm.kblang,
			usbtablet=kvmqm.usbtablet,
			template=resourceMapping[kvmqm.template.id]
		)
		newKVMQM.save()
		elementMapping[kvmqm.id] = newKVMQM

	from ...elements.kvmqm import KVMQM_Interface as New_KVMQM_Interface
	for kvmqm_interface in KVM_Interface.objects.filter(): #This is due to an old naming error (Should have been KVMQM_Interface)
		newKVMQMInterface = New_KVMQM_Interface(
			id="{0:0{1}x}".format(kvmqm_interface.id, 24),
			owner=userMapping[kvmqm_interface.owner.id],
			state=kvmqm_interface.state,
			timeout=kvmqm_interface.timeout,
			num=kvmqm_interface.num,
			mac=kvmqm_interface.mac,
			ipspy_pid=kvmqm_interface.ipspy_pid,
			used_addresses=kvmqm_interface.used_addresses
		)
		newKVMQMInterface.save()
		elementMapping[kvmqm_interface.id] = newKVMQMInterface


	#They should never exist
	"""
	from ...elements.kvm import KVM as New_KVM
	for kvm in KVM.objects.filter():
		newKVM = New_KVM(
			id="{0:0{1}x}".format(kvm.id, 24),
			owner=userMapping[kvm.owner.id],
			state=kvm.state,
			timeout=kvm.timeout,
			vmid=kvm.vmid,
			websocket_port=kvm.websocket_port,
			websocket_pid=kvm.websocket_pid,
			vncport=kvm.vncport,
			vncpid=kvm.vncpid,
			vncpassword=kvm.vncpassword,
			cpus=kvm.cpus,
			ram=kvm.ram,
			kblang=kvm.kblang,
			usbtablet=kvm.usbtablet,
			template = resourceMapping[kvm.template.id]
		)
		newKVM.save()
		elementMapping[kvm.id] = newKVM
	
	from ...elements.kvm import KVM_Interface as New_KVM_Interface
	for kvm_interface in KVM_Interface.objects.filter():
		newKVMInterface = New_KVM_Interface(
			id="{0:0{1}x}".format(kvm_interface.id, 24),
			owner=userMapping[kvm_interface.owner.id],
			state=kvm_interface.state,
			timeout=kvm_interface.timeout,
			num=kvm_interface.num,
			mac=kvm_interface.mac,
			ipspy_pid=kvm_interface.ipspy_pid,
			used_addresses=kvm_interface.used_addresses
		)
		newKVMInterface.save()
		elementMapping[kvm_interface.id] = newKVMInterface
	"""

	from ...elements.openvz import OpenVZ as New_OpenVZ
	for openvz in OpenVZ.objects.filter():
		newOpenVZ = New_OpenVZ(
			id="{0:0{1}x}".format(openvz.id, 24),
			owner=userMapping[openvz.owner.id],
			state=openvz.state,
			timeout=openvz.timeout,
			vmid=openvz.vmid,
			websocket_port=openvz.websocket_port,
			websocket_pid=openvz.websocket_pid,
			vncport=openvz.vncport,
			vncpid=openvz.vncpid,
			vncpassword=openvz.vncpassword,
			cpus=openvz.cpus,
			ram=openvz.ram,
			diskspace=openvz.diskspace,
			rootpassword=openvz.rootpassword,
			gateway4=openvz.gateway4,
			hostname=openvz.hostname,
			gateway6=openvz.gateway6,
			template=resourceMapping[openvz.template.id]
		)
		newOpenVZ.save()
		elementMapping[openvz.id] = newOpenVZ

	from ...elements.openvz import OpenVZ_Interface as New_OpenVZ_Interface
	for openvz_interface in OpenVZ_Interface.objects.filter():
		newOpenVZ_Interface = New_OpenVZ_Interface(
				id="{0:0{1}x}".format(openvz_interface.id, 24),
				owner=userMapping[openvz_interface.owner.id],
				state=openvz_interface.state,
				timeout=openvz_interface.timeout,
				name=openvz_interface.name,
				ip4address=openvz_interface.ip4address,
				ip6address=openvz_interface.ip6address,
				use_dhcp=openvz_interface.use_dhcp,
				mac=openvz_interface.mac,
				ipspy_pid=openvz_interface.ipspy_pid,
				used_addresses=openvz_interface.used_addresses
				)
		newOpenVZ_Interface.save()
		elementMapping[openvz_interface.id]=newOpenVZ_Interface

	from ...elements.repy import Repy as NewRepy
	for repy in Repy.objects.filter():
		newRepy = NewRepy(
				id="{0:0{1}x}".format(repy.id, 24),
				owner=userMapping[repy.owner.id],
				state=repy.state,
				timeout=repy.timeout,
				pid=repy.pid,
				websocket_port=repy.websocket_port,
				websocket_pid=repy.websocket_pid,
				vncport=repy.vncport,
				vncpid=repy.vncpid,
				vncpassword=repy.vncpassword,
				args=repy.args,
				cpus=repy.cpus,
				ram=repy.ram,
				bandwidth=repy.bandwidth,
				template=resourceMapping[repy.template.id]
		)
		newRepy.save()
		elementMapping[repy.id] = newRepy

	from ...elements.repy import Repy_Interface as New_Repy_Interface
	for repy_interface in Repy_Interface.objects.filter():
		newRepyInterface = New_Repy_Interface(
			id="{0:0{1}x}".format(repy_interface.id, 24),
			owner=userMapping[repy_interface.owner.id],
			state=repy_interface.state,
			timeout=repy_interface.timeout,
			name=repy_interface.name,
			ipspy_pid=repy_interface.ipspy_pid,
			used_addresses=repy_interface.used_addresses,
		)
		newRepyInterface.save()
		elementMapping[repy_interface.id] = newRepyInterface


	from ...elements.tinc import Tinc as NewTc
	for tinc in Tinc.objects.filter():
		newTinc = NewTc(
			id="{0:0{1}x}".format(tinc.id, 24),
			owner=userMapping[tinc.owner.id],
			state=tinc.state,
			timeout=tinc.timeout,
			port=tinc.port,
			path=tinc.path,
			mode=tinc.mode,
			privkey=tinc.privkey,
			pubkey=tinc.pubkey,
			peers=tinc.peers
		)
		newTinc.save()
		elementMapping[tinc.id] = newTinc


	from ...elements.udp_tunnel import UDP_Tunnel as NewUDP_Tunnel
	for udp_tunnel in UDP_Tunnel.objects.filter():
		newUDP_Tunnel = NewUDP_Tunnel(
			id="{0:0{1}x}".format(udp_tunnel.id, 24),
			owner=userMapping[udp_tunnel.owner.id],
			state=udp_tunnel.state,
			timeout=udp_tunnel.timeout,
			pid=udp_tunnel.pid,
			port=udp_tunnel.port,
			connect=udp_tunnel.connect
		)
		newUDP_Tunnel.save()
		elementMapping[udp_tunnel.id] = newUDP_Tunnel


	from ...elements.vpncloud import VpnCloud as NewVPNCloud
	for vpncloud in VpnCloud.objects.filter():
		newVPNcloud = NewVPNCloud(
			id="{0:0{1}x}".format(vpncloud.id, 24),
			owner=userMapping[vpncloud.owner.id],
			state=vpncloud.state,
			timeout=vpncloud.timeout,
			port=vpncloud.port,
			pid=vpncloud.pid,
			networkid=vpncloud.network_id,
			peers=vpncloud.peers
		)
		newVPNcloud.save()
		elementMapping[vpncloud.id] = newVPNcloud


	connectionMapping={}
	from ...connections.bridge import Bridge as NewBridge
	for bridge in Bridge.objects.filter():
		newBridge = NewBridge(
			id="{0:0{1}x}".format(bridge.id, 24),
			owner=userMapping[bridge.owner.id],
			state=bridge.state,
			bridge=bridge.bridge,
			emulation=bridge.emulation,
			bandwidth_to=bridge.bandwidth_to,
			bandwidth_from=bridge.bandwidth_from,
			lossratio_to=bridge.lossratio_to,
			lossratio_from=bridge.lossratio_from,
			duplicate_to=bridge.duplicate_to,
			duplicate_from=bridge.duplicate_from,
			corrupt_to=bridge.corrupt_to,
			corrupt_from=bridge.corrupt_from,
			delay_to=bridge.delay_to,
			delay_from=bridge.delay_from,
			jitter_to=bridge.jitter_to,
			jitter_from=bridge.jitter_from,
			distribution_to=bridge.distribution_to,
			distribution_from=bridge.distribution_from,
			capturing=bridge.capturing,
			capture_filter=bridge.capture_filter,
			capture_port=bridge.capture_port,
			capture_mode=bridge.capture_mode,
			capture_pid=bridge.capture_pid)
		newBridge.save()
		connectionMapping[bridge.id] = newBridge

	from ...connections.fixed_bridge import Fixed_Bridge as NewFixedBridge
	for fixedBridge in Fixed_Bridge.objects.filter():
		newFixedBridge = NewFixedBridge(
			id="{0:0{1}x}".format(fixedBridge.id, 24),
			owner=userMapping[fixedBridge.owner.id],
			state = fixedBridge.state)
		newFixedBridge.save()
		connectionMapping[fixedBridge.id]=newFixedBridge

	usageStatisticsMapping={}
	from ...accounting import UsageStatistics as NewUsageStatistics
	for usageStatistic in UsageStatistics.objects.filter():
		newUsageStatistic = NewUsageStatistics(
			id="{0:0{1}x}".format(usageStatistic.id, 24),
			begin =usageStatistic.begin,
			attrs=usageStatistic.attrs
		)
		newUsageStatistic.save()
		usageStatisticsMapping[usageStatistic.id] = newUsageStatistic

	usageRecordMapping={}
	from ...accounting import UsageRecord as NewUsageRecord
	for usageRecord in UsageRecord.objects.filter():
		newUsageRecord = NewUsageRecord(
			id="{0:0{1}x}".format(usageRecord.id, 24),
			statistics=usageStatisticsMapping[usageRecord.statistics.id],
			type=usageRecord.type,
			begin=usageRecord.begin,
			end=usageRecord.end,
			measurements=usageRecord.measurements,
			memory=usageRecord.memory,
			diskspace=usageRecord.diskspace,
			traffic=usageRecord.traffic,
			cputime=usageRecord.cputime
		)
		newUsageRecord.save()
		usageRecordMapping[usageRecord.id]=newUsageRecord

	resourceInstanceMapping={}
	from ...resources import ResourceInstance as NewResourceInstance

	for resourceInstance in ResourceInstance.objects.filter():
		ownerElement = None
		if resourceInstance.ownerElement:
			ownerElement=elementMapping[resourceInstance.ownerElement.id]
		ownerConnection = None
		if resourceInstance.ownerConnection:
			ownerConnection=connectionMapping[resourceInstance.ownerConnection.id]
		newResourceInstance = NewResourceInstance(
			id="{0:0{1}x}".format(resourceInstance.id, 24),
			type=resourceInstance.type,
			num=resourceInstance.num,
			ownerElement=ownerElement,
			ownerConnection=ownerConnection,
			attrs=resourceInstance.attrs
		)
		newResourceInstance.save()
		resourceInstanceMapping[resourceInstance.id] = newResourceInstance


	#Update all elements to integrate the old references and relationships between them.

	for externalNetwork in External_Network.objects.filter():
		newExternalNetwork= elementMapping.get(externalNetwork.id)
		newExternalNetwork.parent = elementMapping.get(externalNetwork.parent.id if externalNetwork.parent else None)
		newExternalNetwork.connection = connectionMapping.get(externalNetwork.connection.id if externalNetwork.connection else None)
		newExternalNetwork.usageStatistics = usageStatisticsMapping.get(externalNetwork.usageStatistics.id if externalNetwork.usageStatistics else None)
		newExternalNetwork.save()

	for kvmqm in KVMQM.objects.filter():
		newKVMQM = elementMapping.get(kvmqm.id)
		newKVMQM.parent = elementMapping.get(kvmqm.parent.id if kvmqm.parent else None)
		newKVMQM.connection = connectionMapping.get(kvmqm.connection.id if kvmqm.connection else None)
		newKVMQM.usageStatistics = usageStatisticsMapping.get(kvmqm.usageStatistics.id if kvmqm.usageStatistics else None)
		newKVMQM.save()

	for kvmqm_interface in KVM_Interface.objects.filter():
		newKVMQM_Interface = elementMapping.get(kvmqm_interface.id)
		newKVMQM_Interface.parent = elementMapping.get(kvmqm_interface.parent.id if kvmqm_interface.parent else None)
		newKVMQM_Interface.connection = connectionMapping.get(kvmqm_interface.connection.id if kvmqm_interface.connection else None)
		newKVMQM_Interface.usageStatistics = usageStatisticsMapping.get(kvmqm_interface.usageStatistics.id if kvmqm_interface.usageStatistics else None)
		newKVMQM_Interface.save()

	"""
	for kvm in KVM.objects.filter():
		print "New KVM Object ????"
		newKVM = elementMapping.get(kvm.id)
		newKVM.parent = elementMapping.get(kvm.parent.id if kvm.parent else None)
		newKVM.connection = connectionMapping.get(kvm.connection.id if kvm.connection else None)
		newKVM.usageStatistics = usageStatisticsMapping.get(kvm.usageStatistics.id if kvm.usageStatistics else None)
		newKVM.save()

	for kvm_interface in KVM_Interface.objects.filter():
		newKVM_Interface = elementMapping.get(kvm_interface.id)
		print "[Old]Kvm_interface.parent.id=%s" % str(kvm_interface.parent.id)
		print "[New]Kvm_interface.parent.id=%s" % str(elementMapping.get(kvm_interface.parent.id if kvm_interface.parent else None))
		if not elementMapping.get(kvm_interface.parent.id if kvm_interface.parent else None):
			print "No daddy!"
		newKVM_Interface.parent = elementMapping.get(kvm_interface.parent.id if kvm_interface.parent else None)
		newKVM_Interface.connection = connectionMapping.get(kvm_interface.connection.id if kvm_interface.connection else None)
		newKVM_Interface.usageStatistics = usageStatisticsMapping.get(kvm_interface.usageStatistics.id if kvm_interface.usageStatistics else None)
		newKVM_Interface.save()
	"""

	for openvz in OpenVZ.objects.filter():
		newOpenVZ = elementMapping.get(openvz.id)
		newOpenVZ.parent = elementMapping.get(openvz.parent.id if openvz.parent else None)
		newOpenVZ.connection = connectionMapping.get(openvz.connection.id if openvz.connection else None)
		newOpenVZ.usageStatistics = usageStatisticsMapping.get(openvz.usageStatistics.id if openvz.usageStatistics else None)
		newOpenVZ.save()

	for openvz_interface in OpenVZ_Interface.objects.filter():
		newOpenVZ_Interface = elementMapping.get(openvz_interface.id)
		newOpenVZ_Interface.parent = elementMapping.get(openvz_interface.parent.id if openvz_interface.parent else None)
		newOpenVZ_Interface.connection = connectionMapping.get(openvz_interface.connection.id if openvz_interface.connection else None)
		newOpenVZ_Interface.usageStatistics = usageStatisticsMapping.get(openvz_interface.usageStatistics.id if openvz_interface.usageStatistics else None)
		newOpenVZ_Interface.save()


	for repy in Repy.objects.filter():
		newRepy = elementMapping.get(repy.id)
		newRepy.parent = elementMapping.get(repy.parent.id if repy.parent else None)
		newRepy.connection = connectionMapping.get(repy.connection.id if repy.connection else None)
		newRepy.usageStatistics = usageStatisticsMapping.get(repy.usageStatistics.id if repy.usageStatistics else None)
		newRepy.save()

	for repy_interface in Repy_Interface.objects.filter():
		newRepy_Interface = elementMapping.get(repy_interface.id)
		newRepy_Interface.parent = elementMapping.get(repy_interface.parent.id if repy_interface.parent else None)
		newRepy_Interface.connection = connectionMapping.get(repy_interface.connection.id if repy_interface.connection else None)
		newRepy_Interface.usageStatistics = usageStatisticsMapping.get(repy_interface.usageStatistics.id if repy_interface.usageStatistics else None)
		newRepy_Interface.save()

	for tinc in Tinc.objects.filter():
		newTinc = elementMapping.get(tinc.id)
		newTinc.parent = elementMapping.get(tinc.parent.id if tinc.parent else None)
		newTinc.connection = connectionMapping.get(tinc.connection.id if tinc.connection else None)
		newTinc.usageStatistics = usageStatisticsMapping.get(tinc.usageStatistics.id if tinc.usageStatistics else None)
		newTinc.save()

	for udp_tunnel in UDP_Tunnel.objects.filter():
		newUDP_Tunnel = elementMapping.get(udp_tunnel.id)
		newUDP_Tunnel.parent = elementMapping.get(udp_tunnel.parent.id if udp_tunnel.parent else None)
		newUDP_Tunnel.connection = connectionMapping.get(udp_tunnel.connection.id if udp_tunnel.connection else None)
		newUDP_Tunnel.usageStatistics = usageStatisticsMapping.get(udp_tunnel.usageStatistics.id if udp_tunnel.usageStatistics else None)
		newUDP_Tunnel.save()

	for vpncloud in VpnCloud.objects.filter():
		newVpnCloud = elementMapping.get(vpncloud.id)
		newVpnCloud.parent = elementMapping.get(vpncloud.parent.id if vpncloud.parent else None)
		newVpnCloud.connection = connectionMapping.get(vpncloud.connection.id if vpncloud.connection else None)
		newVpnCloud.usageStatistics = usageStatisticsMapping.get(vpncloud.usageStatistics.id if vpncloud.usageStatistics else None)
		newVpnCloud.save()

	for bridge in Bridge.objects.filter():
		newBridge = connectionMapping.get(bridge.id)
		newBridge.usageStatistics = usageStatisticsMapping.get(bridge.usageStatistics.id if bridge.usageStatistics else None)

		eleList=[]
		for element in bridge.elements.all():
			eleList.append(elementMapping.get(element.id))
		newBridge.elements = eleList
		newBridge.save()

	for fixed_bridge in Fixed_Bridge.objects.filter():
		newFixedBridge = connectionMapping.get(fixed_bridge.id)
		newFixedBridge.usageStatistics = usageStatisticsMapping.get(fixed_bridge.usageStatistics.id if fixed_bridge.usageStatistics else None)

		eleList = []
		for element in fixed_bridge.elements.all():
			eleList.append(elementMapping.get(element.id))
		newFixedBridge.elements = eleList
		newFixedBridge.save()


	#Move all old element files to new element
	"""
	try:
		kvmqm_interface_path = os.path.join(config.DATA_DIR, "kvmqm_interface")
		if not os.path.exists(kvmqm_interface_path):
			cmd_ = ["mkdir", kvmqm_interface_path]
			out = cmd.run(cmd_)
	except:
		print "Couldn't create kvmqm_interface folder"
	for element in Element.objects.filter():
		try:
			oldPath = os.path.join(config.DATA_DIR, element.type, str(element.id))
			if element.type == "kvm_interface":
				element.type = "kvmqm_interface"
			if os.path.exists(oldPath):
				newPath = os.path.join(config.DATA_DIR, element.type, str(elementMapping[element.id].id))
				cmd_ = ["mv", oldPath, newPath]
				out = cmd.run(cmd_)
		except Exception, e:
			oldPath = os.path.join(config.DATA_DIR, element.type, str(element.id))
			if element.type == "kvm_interface":
				element.type = "kvmqm_interface"
			newPath = os.path.join(config.DATA_DIR, element.type, str(elementMapping[element.id].id))
			print "Couldn't move element folder: old_id=%s, new_id=%s, type=%s, path=%s, new_path=%s" \
			      % (str(element.id),
			         str(elementMapping[element.id].id),
			         str(element.type),
			         str(oldPath),
			         str(newPath))
			print e

	for connection in Connection.objects.filter():
		try:
			oldPath = os.path.join(config.DATA_DIR, connection.type, str(connection.id))
			if os.path.exists(oldPath):
				newPath = os.path.join(config.DATA_DIR, connection.type, str(connectionMapping[connection.id].id))
				cmd_ = ["mv", oldPath, newPath]
				out = cmd.run(cmd_)
		except Exception, e:
			oldPath = os.path.join(config.DATA_DIR, connection.type, str(connection.id))
			newPath = os.path.join(config.DATA_DIR, connection.type, str(connectionMapping[connection.id].id))
			print "Couldn't move connection folder: old_id=%s, new_id=%s, type=%s, path=%s, new_path=%s" \
			      % (str(connection.id),
			         str(connectionMapping[connection.id].id),
			         str(connection.type),
			         str(oldPath),
			         str(newPath))
			raise e
	"""

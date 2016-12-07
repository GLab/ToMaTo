class ActionName:
	START = "start"
	STOP = "stop"
	PREPARE = "prepare"
	DESTROY = "destroy"

	RENEW = "renew"

	UPLOAD_GRANT = "upload_grant"
	UPLOAD_USE = "upload_use"
	DOWNLOAD_GRANT = "download_grant"

	REXTFV_UPLOAD_GRANT = "rextfv_upload_grant"
	REXTFV_UPLOAD_USE = "rextfv_upload_use"
	REXTFV_DOWNLOAD_GRANT = "rextfv_download_grant"

	CHANGE_TEMPLATE = "change_template"

class StateName:
	CREATED = "created"
	PREPARED = "prepared"
	STARTED = "started"

class TechName:
	OPENVZ = "openvz"
	OPENVZ_INTERFACE = "openvz_interface"

	KVMQM = "kvmqm"
	KVMQM_INTERFACE = "kvmqm_interface"

	KVM = "kvm"
	KVM_INTERFACE = "kvm_interface"

	LXC = "lxc"
	LXC_INTERFACE = "lxc_interface"

class TypeName:
	FULL_VIRTUALIZATION = "full"
	FULL_VIRTUALIZATION_INTERFACE = "full_interface"

	CONTAINER_VIRTUALIZATION = "container"
	CONTAINER_VIRTUALIZATION_INTERFACE = "container_interface"

	REPY = "repy"
	REPY_INTERFACE = "repy_interface"

	EXTERNAL_NETWORK = "external_network"
	EXTERNAL_NETWORK_ENDPOINT = "external_network_endpoint"

	TINC = "tinc"
	TINC_VPN = "tinc_vpn"
	TINC_ENDPOINT = "tinc_endpoint"

	UDP_ENDPOINT = "udp_endpoint"
	UDP_TUNNEL = "udp_tunnel"

	VPNCLOUD = "vpncloud"
	VPNCLOUD_ENDPOINT = "vpncloud_endpoint"

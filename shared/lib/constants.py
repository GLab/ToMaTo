class Action:
	START = "start"
	STOP = "stop"
	PREPARE = "prepare"
	DESTROY = "destroy"

	RENEW = "renew"

	UPLOAD_GRANT = "upload_grant"
	UPLOAD_USE = "upload_use"
	REXTFV_UPLOAD_GRANT = "rextfv_upload_grant"
	REXTFV_UPLOAD_USE = "rextfv_upload_use"
	CHANGE_TEMPLATE = "change_template"

class State:
	CREATED = "created"
	PREPARED = "prepared"
	STARTED = "started"

class Type:
	OPENVZ = "openvz"
	OPENVZ_INTERFACE = "openvz_interface"

	KVMQM = "kvmqm"
	KVMQM_INTERFACE = "kvmqm_interface"

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

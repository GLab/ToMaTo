// http://marijnhaverbeke.nl/uglifyjs

var settings = {
	childElementDistance: 25,
	childElementRadius: 7,
	connectionHandleWidth: 10,

	commonPreferenceThreshold: 100,
	otherCommonElements: [
	                      {
	                  		label: "Switch (Tinc)",
	                		name: "vpn-switch",
	                		icon: "img/switch32.png",
	                		data: {
	                		  type: "tinc_vpn",
	                		  mode: "switch"
	                		}
	                      }
	],
	supported_configwindow_help_pages: ['kvmqm','openvz','connection']
}

var ignoreErrors = false;


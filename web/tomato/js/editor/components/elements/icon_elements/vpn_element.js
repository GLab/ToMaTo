
var VPNElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconSize = {x: 32, y:16};
	},
	iconUrl: function() {
		return dynimg(32,"vpn",this.data.mode,null);
	},
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	isEndpoint: function() {
		return false;
	},
	getConnectTarget: function(callback) {
		return this.topology.createElement({type: "tinc_endpoint", parent: this.data.id}, callback);
	}
});

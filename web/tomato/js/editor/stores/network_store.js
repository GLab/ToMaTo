var NetworkStore = Class.extend({
	init: function(data,editor) {
		this.editor = editor;
		data.sort(function(t1, t2){
			var t = t2.preference - t1.preference;
			if (t) return t;
			if (t1.kind < t2.kind) return -1;
			if (t2.kind < t1.kind) return 1;
			return 0;
		});
		this.nets = [];
		for (var i=0; i<data.length; i++) {
		     net = data[i];
			 if (!net.icon) {
				 net.icon = this.getNetworkIcon(net.kind);
			 }
			 this.nets.push(net);
		}
	},
	getAll: function() {
		return this.nets;
	},
	getAllowed: function() {
		var allowedNets = this.getAll()
		if (!this.editor.allowRestrictedNetworks) {
			var nets_filtered = [];
			
			for (var i = 0; i<allowedNets.length;i++) {
				if (!(allowedNets[i].restricted)) {
					nets_filtered.push(allowedNets[i]);
				}
			}
			allowedNets = nets_filtered;
		}
		return allowedNets;
	},
	getCommon: function() {
		var common = [];
		for (var i = 0; i < this.nets.length; i++)
		 if (this.nets[i].show_as_common && (!this.nets[i].restricted || this.editor.allowRestrictedNetworks))
		   common.push(this.nets[i]);
		return common;
	},
	getNetworkIcon: function(kind) {
		return dynimg(32,"network",kind.split("/")[0],(kind.split("/")[1]?kind.split("/")[1]:null));
	}
});

var ExternalNetworkElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconSize = {x: 32, y:32};

	},
	iconUrl: function() {
		return editor.networks.getNetworkIcon(this.data.kind);
	},
	configWindowSettings: function() {
		var config = this._super();
		config.order = ["name", "kind"];
		
		var networkInfo = {};
		var networks = this.editor.networks.getAllowed();
		
		for (var i=0; i<networks.length; i++) {
			var info = $('<div class="hoverdescription" style="display: inline;"></div>');
			var d = $('<div class="hiddenbox"></div>');
			var p = $('<p style="margin:4px; border:0px; padding:0px; color:black;"></p>');
			var desc = $('<table></table>');
			p.append(desc);
			d.append(p);
			
			net = networks[i];
			
			info.append('<img src="/img/info.png" />');

			if (net.description) {
				desc.append($('<tr><td style="background:white;"><img src="/img/info.png" /></td><td style="background:white;">'+net.description+'</td></tr>'));
			
			}
			
			info.append(d);
			networkInfo[net.kind] = info;
		}
		
		config.special.kind = new ChoiceElement({
			label: "Network kind",
			name: "kind",
			info: networkInfo,
			choices: createMap(this.editor.networks.getAll(), "kind", "label"),
			value: this.data.kind || this.caps.attributes.kind["default"],
			disabled: !this.attrEnabled("kind")
		});
		return config;
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
		return this.topology.createElement({type: "external_network_endpoint", parent: this.data.id}, callback);
	}
});

var createMap = function(listOfObj, keyAttr, valueAttr, startMap) {
	var map = startMap ? copy(startMap) : {};
	for (var i = 0; i < listOfObj.length; i++) 
		map[listOfObj[i][keyAttr]] = typeof valueAttr === "function" ? valueAttr(listOfObj[i]) : listOfObj[i][valueAttr];
	return map;
};

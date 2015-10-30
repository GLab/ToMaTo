var SwitchPortElement = ChildElement.extend({
	configWindowSettings: function() {
		var config = this._super();
		config.order.remove("name");
		config.ignore += ["name", "kind", "peers"];
		return config;
	}	
});

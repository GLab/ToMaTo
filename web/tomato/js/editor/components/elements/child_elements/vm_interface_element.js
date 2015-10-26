
var VMInterfaceElement = ChildElement.extend({
	showUsedAddresses: function() {
		var t = this;
		this.update(true, function() {
	 		var win = new Window({
	 			title: "Used addresses on " + t.name(),
	 			content: '<p>'+t.data.used_addresses.join('<br/>')+'</p>',
	 			autoShow: true
	 		});			
		});
	}
});


var VMConfigurableInterfaceElement = VMInterfaceElement.extend({
	onConnected: function() {
		var hint = this.getAddressHint();
		if (hint == "dhcp") this.modify({"use_dhcp": true});
		else this.modify({"ip4address": "10.0." + hint[0] + "." + hint[1] + "/24"});
	}
});



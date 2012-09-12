var MenuGroup = Class.extend({
	init: function(name) {
		this.name = name;
		this.container = $('<li></li>');
		this.panel = $('<div></div>');
		this.container.append(this.panel);
		this.label = $('<h3><span>'+name+'</span></h3>');
		this.container.append(this.label);
	},
	addElement: function(element) {
		this.panel.append(element);
	},
	addStackedElements: function(elements) {
		var ul = $('<ul class="ui-ribbon-element ui-ribbon-list"></ul>');
		for (var i=0; i < elements.length; i++) {
			var li = $('<li></li>');
			li.append(elements[i]);
			ul.append(li);
		}
		this.addElement(ul);
	}
});

var MenuTab = Class.extend({
	init: function(name) {
		this.name = name;
		this.div = $('<div id="menu_tab_'+name+'"></div>');
		this.link = $('<li><a href="#menu_tab_'+name+'"><span><label>'+name+'</label></span></a></li>');
		this.panel = $('<ul></ul>');
		this.div.append(this.panel);
		this.groups = {};
	},
	addGroup: function(name) {
		var group = new MenuGroup(name);
		this.groups[name] = group;
		this.panel.append(group.container);
		return group;
	},
	getGroup: function(name) {
		return this.groups[name];
	}
});

var Menu = Class.extend({
	init: function(container) {
		this.container = container;
		this.tabs = {};
		this.tabLinks = $('<ul/>');
		this.container.append(this.tabLinks);
	},
	addTab: function(name) {
		var tab = new MenuTab(name);
		this.tabs.name = tab;
		this.container.append(tab.div);
		this.tabLinks.append(tab.link);
		return tab;
	},
	getTab: function(name) {
		return this.tabs[name];
	},
	paint: function() {
		this.container.ribbon();
	},
});

Menu.button = function(options) {
	var html = $('<button class="ui-ribbon-element ui-ribbon-control ui-button"/>');
	if (options.toggle) html.addClass("ui-button-toggle");
	var icon = $('<span class="ui-icon"></span>');
	if (options.small) {
		html.addClass("ui-ribbon-small-button");
		icon.addClass("icon-16x16");
	} else {
		html.addClass("ui-ribbon-large-button");
		icon.addClass("icon-32x32");
	}
	html.append(icon);
	html.append($('<span>'+options.name+'</span>'));
	if (options.func) html.click(options.func); //must be done before call to button()
	html.button();
	icon.css('background-image', 'url("'+options.icon+'")'); //must be done after call to button()
	if (options.tooltip) html.attr("title", options.tooltip);
	return html
};

Menu.checkbox = function(options) {
	var html = $('<input type="checkbox" id="'+options.name+'"/><label for="'+options.name+'">'+options.label+'</label>');
	if (options.tooltip) html.attr("title", options.tooltip);
	return html
};

var Workspace = Class.extend({
	init: function(container) {
		this.container = container;
	}
});

var Editor = Class.extend({
	init: function(options) {
		this.options = options;
		this.menu = new Menu(this.options.menu_container);
		this.workspace = new Workspace(this.options.workspace_container);
		this.topology = options.topology;
		this.buildMenu();
	},
	buildMenu: function() {
		var t = this;
	
		var tab = this.menu.addTab("Home");
		var group = tab.addGroup("Modes");
		group.addElement(Menu.button({name: "Select & Move", icon: "/img/select32.png", toggle: true, small: false}));
		group.addStackedElements([
			Menu.button({name: "Connect", icon: "/img/connect16.png", toggle: true, small: true}),
			Menu.button({name: "Delete", icon: "/img/eraser16.png", toggle: true, small: true}),
		]);
		var group = tab.addGroup("Topology control");
		group.addElement(Menu.button({name: "Start", icon: "/img/start32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Stop", icon: "/img/stop32.png", toggle: false, small: false}));
		group.addStackedElements([
			Menu.button({name: "Prepare", icon: "/img/prepare16.png", toggle: false, small: true}),
			Menu.button({name: "Destroy", icon: "/img/destroy16.png", toggle: false, small: true}),
			Menu.button({name: "Delete", icon: "/img/eraser16.png", toggle: false, small: true}),
		]);
		var group = tab.addGroup("Common elements");
		group.addElement(Menu.button({name: "Debian 6.0 (OpenVZ)", icon: "/img/openvz_linux32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Debian 6.0 (KVM)", icon: "/img/kvm_linux32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Switch", icon: "/img/switch32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Internet", icon: "/img/internet32.png", toggle: false, small: false}));

		var tab = this.menu.addTab("Devices");
		var group = tab.addGroup("Linux (OpenVZ)");
		group.addElement(Menu.button({name: "Debian 6.0", icon: "/img/openvz_linux32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Ubuntu 10.04", icon: "/img/openvz_linux32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Ubuntu 12.04", icon: "/img/openvz_linux32.png", toggle: false, small: false}));		
		var group = tab.addGroup("Linux (KVM)");
		group.addElement(Menu.button({name: "Debian 6.0", icon: "/img/kvm_linux32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Ubuntu 10.04", icon: "/img/kvm_linux32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Ubuntu 12.04", icon: "/img/kvm_linux32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "TinyCore", icon: "/img/kvm_linux32.png", toggle: false, small: false}));
		var group = tab.addGroup("Scripts (Repy)");
		group.addElement(Menu.button({name: "Pingable node", icon: "/img/repy32.png", toggle: false, small: false}));
		group.addStackedElements([
			Menu.button({name: "DHCP Server", icon: "/img/repy16.png", toggle: false, small: true}),
			Menu.button({name: "Fake DNS Server", icon: "/img/repy16.png", toggle: false, small: true})
		]);
		var group = tab.addGroup("Upload images");
		group.addStackedElements([
			Menu.button({name: "KVM image", icon: "/img/kvm16.png", toggle: false, small: true}),
			Menu.button({name: "OpenVZ image", icon: "/img/openvz16.png", toggle: false, small: true}),
			Menu.button({name: "Repy script", icon: "/img/repy16.png", toggle: false, small: true})
		]);
		var group = tab.addGroup("Other (KVM)");
		group.addElement(Menu.button({name: "Android", icon: "/img/kvm32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "ReactOS", icon: "/img/kvm32.png", toggle: false, small: false}));

		var tab = this.menu.addTab("Network");
		var group = tab.addGroup("VPN Elements");
		group.addElement(Menu.button({name: "Switch", icon: "/img/switch32.png", toggle: false, small: false}));
		group.addElement(Menu.button({name: "Hub", icon: "/img/hub32.png", toggle: false, small: false}));
		var group = tab.addGroup("Scripts (Repy)");
		group.addElement(Menu.button({name: "Custom script", icon: "/img/repy32.png", toggle: false, small: false}));
		group.addStackedElements([
			Menu.button({name: "Switch", icon: "/img/repy16.png", toggle: false, small: true}),
			Menu.button({name: "NAT Gateway", icon: "/img/repy16.png", toggle: false, small: true})
		]);
		var group = tab.addGroup("External");
		group.addElement(Menu.button({name: "Internet", icon: "/img/internet32.png", toggle: false, small: false}));
		var group = tab.addGroup("Other");
		group.addElement(Menu.button({name: "OpenFlow", icon: "/img/openflow32.png", toggle: false, small: false}));

		var tab = this.menu.addTab("Topology");
		var group = tab.addGroup("");
		group.addElement(Menu.button({name: "Notes", icon: "/img/notes32.png", toggle: false, small: false}));
		group.addStackedElements([
			Menu.button({name: "Usage", icon: "/img/chart_bar.png", toggle: false, small: true, func: function(){
			  	window.open('/topology/'+t.topology.id+'/usage', '_blank', 'innerHeight=450,innerWidth=600,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');			
			}}),
			Menu.button({name: "Rename", icon: "/img/rename.png", toggle: false, small: true}),
			Menu.button({name: "Export", icon: "/img/export16.png", toggle: false, small: true}),
		]);
		group.addElement(Menu.button({name: "Users & Permissions", icon: "/img/user32.png", toggle: false, small: false}));

		var tab = this.menu.addTab("Options");
		var group = tab.addGroup("Editor");
		group.addStackedElements([
			Menu.checkbox({name:"safe_mode", label:"Safe mode", tooltip:"Asks before all destructive actions"}),
			Menu.checkbox({name:"snap_to_grid", label:"Snap to grid", tooltip:"All elements snap to an invisible 10x10 pixel grid"}),
			Menu.checkbox({name:"fixed_pos", label:"Fixed positions", tooltip:"Elements can not be moved"}),
		]);
		group.addStackedElements([
			Menu.checkbox({name:"beginner_mode", label:"Beginner mode", tooltip:"Displays help messages for all elements"}),
		]);

		this.menu.paint();
	},
});
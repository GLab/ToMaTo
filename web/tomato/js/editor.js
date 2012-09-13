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
		var count = 0;
		for (var i=0; i < elements.length; i++) {
			if (count >= 3) { //only 3 elements fit
				this.addElement(ul);
				ul = $('<ul class="ui-ribbon-element ui-ribbon-list"></ul>');
				count = 0;
			}			
			var li = $('<li></li>');
			li.append(elements[i]);
			ul.append(li);
			count++;
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
		this.tabs[name] = tab;
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
	if (options.toggle) {
		html.addClass("ui-button-toggle");
		if (options.toggleGroup) options.toggleGroup.add(html);
	}
	var icon = $('<span class="ui-icon"></span>');
	if (options.small) {
		html.addClass("ui-ribbon-small-button");
		icon.addClass("icon-16x16");
	} else {
		html.addClass("ui-ribbon-large-button");
		icon.addClass("icon-32x32");
	}
	html.append(icon);
	html.append($('<span>'+options.label+'</span>'));
	if (options.func || options.toggle && options.toggleGroup) {
		html.click(function() {
			if (options.toggle && options.toggleGroup) options.toggleGroup.selected(this);
			if (options.func) options.func(this);	
		}); //must be done before call to button()
	}
	html.button({
		tooltip: options.tooltip || options.label || options.name,
	});
	html.attr("id", options.name || options.label);
	icon.css('background-image', 'url("'+options.icon+'")'); //must be done after call to button()
	html.setChecked = function(value){
		this.button("option", "checked", value);
	}
	return html
};

Menu.checkbox = function(options) {
	var html = $('<input type="checkbox" id="'+options.name+'"/><label for="'+options.name+'">'+options.label+'</label>');
	if (options.tooltip) html.attr("title", options.tooltip);
	if (options.func) html.click(function(){
		options.func(html.attr("checked"), html);
	});
	html.setChecked = function(value){
		this.attr("checked", value);
	}
	if (options.checked) html.setChecked(true);
	return html
};

var ToggleGroup = Class.extend({
	init: function() {
		this.buttons = [];
	},
	add: function(button) {
		this.buttons.push(button);
	},
	selected: function(button) {
		for (var i=0; i<this.buttons.length; i++)
			this.buttons[i].setChecked(this.buttons[i].attr("id") == $(button).attr("id"));
	},
});

var ContextMenu = Class.extend({
    //TODO: move to http://medialize.github.com/jQuery-contextMenu/index.html
	init: function(callback, options) {
		this.menu = $("<ul/>");
		this.callback = callback;
		this.options = options;
		$("body").append(this.menu);
	},
	applyTo: function(target) {
		if (target.node) target = $(target.node);
		target.contextMenu(this.menu, this.callback, this.options);
	},
	addItem: function(item, separator) {
		var li = $("<li/>").append(item);
		if (separator) li.addClass("separator");
		this.menu.append(li);
	},
});

var Workspace = Class.extend({
	init: function(container, editor) {
		this.container = container;
		this.editor = editor;
		container.addClass("ui-widget-content").addClass("ui-corner-all");
    	this.size = {x: this.container.width(), y: this.container.height()};
    	this.canvas = Raphael(this.container[0], this.size.x, this.size.y);
    	this.editor.topology.getContextMenu().applyTo(this.container);
	}
});

var Topology = Class.extend({
	init: function(editor, data) {
		this.data = data;
	},
	getContextMenu: function() {
		var cmenu = new ContextMenu();
		cmenu.addItem($('<b>Topology</b>'));
		cmenu.addItem($('<a href="#">Start</a>'), true);
		cmenu.addItem($('<a href="#">Stop</a>'));
		cmenu.addItem($('<a href="#">Prepare</a>'));
		cmenu.addItem($('<a href="#">Destroy</a>'));
		return cmenu;
	},
	action: function(action, params) {
		log("Topology action: "+action);
	},
	action_start: function() {
		this.action("start");
	},
	action_stop: function() {
		this.action("stop");
	},
	action_prepare: function() {
		this.action("prepare");
	},
	action_destroy: function() {
		this.action("destroy");
	},
	remove: function() {
	}
});

var Template = Class.extend({
	init: function(options) {
		this.type = options.type;
		this.subtype = options.subtype;
		this.name = options.name;
		this.label = options.label || options.name;
	},
	menuButton: function(toggleGroup, small) {
		return Menu.button({
			name: this.type + "-" + this.name,
			label: this.label || (this.type + "-" + this.name),
			icon: "img/"+this.type+((this.subtype&&!small)?("_"+this.subtype):"")+(small?16:32)+".png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: small
		});
	},
});

var TemplateStore = Class.extend({
	init: function(data) {
		this.types = {};
		for (var i=0; i<data.length; i++) this.add(new Template(data[i]));
	},
	add: function(tmpl) {
		if (! this.types[tmpl.type]) this.types[tmpl.type] = {};
		this.types[tmpl.type][tmpl.name] = tmpl;
	},
	getAll: function(type) {
		if (! this.types[type]) return [];
		var tmpls = [];
		for (var name in this.types[type]) tmpls.push(this.types[type][name]);
		return tmpls;
	}
});

var Editor = Class.extend({
	init: function(options) {
		this.options = options;
		this.topology = new Topology(this, options.topology);
		this.menu = new Menu(this.options.menu_container);
		this.workspace = new Workspace(this.options.workspace_container, this);
		this.templates = new TemplateStore(this.options.templates);
		this.buildMenu();
	},
	optionMenuItem: function(options) {
		var t = this;
		return Menu.checkbox({
			name: options.name, label: options.label, tooltip: options.tooltip,
			func: function(value){t.options[options.name]=value;},
			checked: this.options[options.name]
		});
	},
	buildMenu: function() {
		var t = this;
	
		var toggleGroup = new ToggleGroup();
	
		var tab = this.menu.addTab("Home");

		var group = tab.addGroup("Modes");
		group.addElement(Menu.button({label: "Select & Move", icon: "img/select32.png", toggle: true, toggleGroup: toggleGroup, small: false}));
		group.addStackedElements([
			Menu.button({label: "Connect", icon: "img/connect16.png", toggle: true, toggleGroup: toggleGroup, small: true}),
			Menu.button({label: "Delete", name: "mode-remove", icon: "img/eraser16.png", toggle: true, toggleGroup: toggleGroup, small: true}),
		]);

		var group = tab.addGroup("Topology control");
		group.addElement(Menu.button({label: "Start", icon: "img/start32.png", toggle: false, small: false, func: function() {t.topology.action_start();}}));
		group.addElement(Menu.button({label: "Stop", icon: "img/stop32.png", toggle: false, small: false, func: function() {t.topology.action_start();}}));
		group.addStackedElements([
			Menu.button({label: "Prepare", icon: "img/prepare16.png", toggle: false, small: true, func: function() {t.topology.action_prepare();}}),
			Menu.button({label: "Destroy", icon: "img/destroy16.png", toggle: false, small: true, func: function() {t.topology.action_destroy();}}),
			Menu.button({label: "Delete", name: "topology-remove", icon: "img/eraser16.png", toggle: false, small: true, func: function() {t.topology.remove();}}),
		]);
		
		var group = tab.addGroup("Common elements");
		group.addElement(Menu.button({label: "Debian 6.0 (OpenVZ)", name: "openvz-debian-6", icon: "img/openvz_linux32.png", toggle: true, toggleGroup: toggleGroup, small: false}));
		group.addElement(Menu.button({label: "Debian 6.0 (KVM)", name: "kvm-debian-6", icon: "img/kvm_linux32.png", toggle: true, toggleGroup: toggleGroup, small: false}));
		group.addElement(Menu.button({label: "Switch", name: "vpn-switch", icon: "img/switch32.png", toggle: true, toggleGroup: toggleGroup, small: false}));
		group.addElement(Menu.button({label: "Internet", name: "net-internet", icon: "img/internet32.png", toggle: true, toggleGroup: toggleGroup, small: false}));


		var tab = this.menu.addTab("Devices");

		var group = tab.addGroup("Linux (OpenVZ)");
		var tmpls = t.templates.getAll("openvz");
		for (var i=0; i<tmpls.length; i++) group.addElement(tmpls[i].menuButton(toggleGroup)); 

		var group = tab.addGroup("Linux (KVM)");
		var tmpls = t.templates.getAll("kvm", "linux");
		for (var i=0; i<tmpls.length; i++) if(tmpls[i].subtype == "linux") group.addElement(tmpls[i].menuButton(toggleGroup)); 

		var group = tab.addGroup("Other (KVM)");
		var tmpls = t.templates.getAll("kvm");
		for (var i=0; i<tmpls.length; i++) if(tmpls[i].subtype != "linux") group.addElement(tmpls[i].menuButton(toggleGroup)); 

		var group = tab.addGroup("Scripts (Repy)");
		var tmpls = t.templates.getAll("repy");
		var btns = [];
		for (var i=0; i<tmpls.length; i++) if(tmpls[i].subtype == "device") btns.push(tmpls[i].menuButton(toggleGroup, true)); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Upload images");
		group.addStackedElements([
			Menu.button({label: "KVM image", name: "kvm-custom", icon: "img/kvm16.png", toggle: true, toggleGroup: toggleGroup, small: true}),
			Menu.button({label: "OpenVZ image", name: "openvz-custom", icon: "img/openvz16.png", toggle: true, toggleGroup: toggleGroup, small: true}),
			Menu.button({label: "Repy script", name: "repy-custom", icon: "img/repy16.png", toggle: true, toggleGroup: toggleGroup, small: true})
		]);


		var tab = this.menu.addTab("Network");

		var group = tab.addGroup("VPN Elements");
		group.addElement(Menu.button({label: "Switch", name: "vpn-switch", icon: "img/switch32.png", toggle: true, toggleGroup: toggleGroup, small: false}));
		group.addElement(Menu.button({label: "Hub", name: "vpn-hub", icon: "img/hub32.png", toggle: true, toggleGroup: toggleGroup, small: false}));

		var group = tab.addGroup("Scripts (Repy)");
		group.addElement(Menu.button({label: "Custom script", name: "repy-custom", icon: "img/repy32.png", toggle: true, toggleGroup: toggleGroup, small: false}));
		var tmpls = t.templates.getAll("repy");
		var btns = [];
		for (var i=0; i<tmpls.length; i++) if(tmpls[i].subtype != "device") btns.push(tmpls[i].menuButton(toggleGroup, true)); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Networks");
		group.addElement(Menu.button({label: "Internet", name: "net-internet", icon: "img/internet32.png", toggle: true, toggleGroup: toggleGroup, small: false}));
		group.addElement(Menu.button({label: "OpenFlow", name: "net-openflow", icon: "img/openflow32.png", toggle: true, toggleGroup: toggleGroup, small: false}));


		var tab = this.menu.addTab("Topology");

		var group = tab.addGroup("");
		group.addElement(Menu.button({label: "Notes", icon: "img/notes32.png", toggle: false, small: false}));
		group.addStackedElements([
			Menu.button({label: "Usage", icon: "img/chart_bar.png", toggle: false, small: true, func: function(){
			  	window.open('/topology/'+t.topology.id+'/usage', '_blank', 'innerHeight=450,innerWidth=600,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');			
			}}),
			Menu.button({label: "Rename", icon: "img/rename.png", toggle: false, small: true}),
			Menu.button({label: "Export", icon: "img/export16.png", toggle: false, small: true}),
		]);
		group.addElement(Menu.button({label: "Users & Permissions", icon: "img/user32.png", toggle: false, small: false}));


		var tab = this.menu.addTab("Options");

		var group = tab.addGroup("Editor");		
		group.addStackedElements([
			this.optionMenuItem({name:"safe_mode", label:"Safe mode", tooltip:"Asks before all destructive actions"}),
			this.optionMenuItem({name:"snap_to_grid", label:"Snap to grid", tooltip:"All elements snap to an invisible 10x10 pixel grid"}),
			this.optionMenuItem({name:"fixed_pos", label:"Fixed positions", tooltip:"Elements can not be moved"}), 
			this.optionMenuItem({name:"beginner_mode", label:"Beginner mode", tooltip:"Displays help messages for all elements"})
		]);

		this.menu.paint();
	},
});
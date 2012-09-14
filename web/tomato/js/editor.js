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
	}
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
	html.button({tooltip: options.tooltip || options.label || options.name});
	html.attr("id", options.name || options.label);
	icon.css('background-image', 'url("'+options.icon+'")'); //must be done after call to button()
	html.setChecked = function(value){
		this.button("option", "checked", value);
	}
	if (options.checked) html.setChecked(true);
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
	}
});

var Workspace = Class.extend({
	init: function(container, editor) {
		this.container = container;
		this.editor = editor;
		container.addClass("ui-widget-content").addClass("ui-corner-all")
		container.addClass("tomato").addClass("workspace");
		container[0].obj = editor.topology;
    	this.size = {x: this.container.width(), y: this.container.height()};
    	this.canvas = Raphael(this.container[0], this.size.x, this.size.y);
    	var c = this.canvas;
		var fs = this.editor.options.frame_size;
    	this.canvas.absPos = function(pos) {
    		return {x: fs + pos.x * (c.width-2*fs), y: fs + pos.y * (c.height-2*fs)};
    	}
    	this.canvas.relPos = function(pos) {
    		return {x: (pos.x - fs) / (c.width-2*fs), y: (pos.y - fs) / (c.height-2*fs)};
    	}
    	this.beginnerHelp = this.canvas.text(c.width/2, c.height/4, "Beginner help").attr({"font-size": 25, "fill": "#999999"});
		if (this.editor.options.beginner_mode && this.editor.topology.isEmpty()) this.beginnerHelp.show();
		else this.beginnerHelp.hide();
	},
	onOptionChanged: function(name) {
		if (this.editor.options.beginner_mode && this.editor.topology.isEmpty()) this.beginnerHelp.show();
		else this.beginnerHelp.hide();
	}
});

var Topology = Class.extend({
	init: function(editor, data) {
		this.editor = editor;
		this.elements = {};
		this.connections = {};
		if (data) this.load(data);
	},
	load: function(data) {
		this.data = data;
		this.id = data.id;
		this.elements = {};
		for (var i=0; i<data.elements.length; i++) {
			var el = data.elements[i];
			var elObj;
			switch (el.type) {
				case "kvmqm":
				case "openvz":
				case "repy":
					elObj = new VMElement(this.editor, el);
					break;
				case "kvmqm_interface":
				case "openvz_interface":
				case "repy_interface":
					elObj = new VMInterfaceElement(this.editor, el);
					break;
				case "tinc_vpn":
					elObj = new VPNElement(this.editor, el);
					break;
				case "tinc_endpoint":
					//hide tinc endpoints with tinc_vpn parents but show endpoints without parent 
					elObj = el.parent ? new HiddenChildElement(this.editor, el) : new VPNElement(this.editor, el) ;
					break;
				default:
					elObj = new UnknownElement(this.editor, el);
					break;
			}
			this.elements[el.id] = elObj;
			if (el.parent) {
				//parent id is less and thus objects exists
				elObj.parent = this.elements[el.parent];
				this.elements[el.parent].children.push(elObj);
			}
		}
		this.connections = {};
		for (var i=0; i<data.connections.length; i++) {
			var con = data.connections[i];
			var conObj = new Connection(this.editor, con);
			this.connections[con.id] = conObj;
			for (var j=0; j<con.elements.length; j++) {
				this.elements[con.elements[j]].connection = conObj;
				conObj.elements.push(this.elements[con.elements[j]]);
			}
		}
	},
	isEmpty: function() {
		for (var id in this.elements) if (this.elements[id] != this.elements[id].constructor.prototype[id]) return false;
		return true;
		//no connections without elements
	},
	paint: function(canvas) {
		for (var id in this.elements) this.elements[id].setCanvas(canvas);
		for (var id in this.connections) this.connections[id].setCanvas(canvas);
		for (var id in this.elements) this.elements[id].paint();
		for (var id in this.connections) this.connections[id].paint();
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

$.contextMenu({
	selector: '.tomato.workspace',
	build: function(trigger, e) {
		var obj = trigger[0].obj;
		return {
			callback: function(key, options) {
				alert("Clicked " + key);
			},
			items: {
				"header": {html:'<span>Topology</span>', type:"html"},
				"control": {
					"name": "Control",
					"icon": "control",
					"items": {
						"start": {name:'Start', icon:'start'},
						"stop": {name:"Stop", icon:"stop"},
						"prepare": {name:"Prepare", icon:"prepare"},
						"destroy": {name:"Destroy", icon:"destroy"},
					}
				},
				"remove": {name:'Delete', icon:'remove'},
			}
		}
	}
});

var Connection = Class.extend({
	init: function(editor, data) {
		this.editor = editor;
		this.data = data;
		this.id = data.id;
		this.elements = [];
	},
	otherElement: function(me) {
		for (var i=0; i<this.elements.length; i++) if (this.elements[i].id != me.id) return this.elements[i];
	},
	getCenter: function() {
		if (this.path) return this.path.getPointAtLength(this.path.getTotalLength()/2);
		else {
			var pos1 = this.elements[0].getAbsPos();
			var pos2 = this.elements[1].getAbsPos();
			return {x: (pos1.x + pos2.x)/2, y: (pos1.y + pos2.y)/2}; 
		}
	},
	getPath: function() {
		var pos1 = this.elements[0].getAbsPos();
		var pos2 = this.elements[1].getAbsPos();
		var path = "M"+pos1.x+" "+pos1.y+"L"+pos2.x+" "+pos2.y;
		//TODO: use bezier loop for very short connections
		return path;
	},
	getAbsPos: function() {
		return this.getCenter();
	},
	getAngle: function() {
		var pos1 = this.elements[0].getAbsPos();
		var pos2 = this.elements[1].getAbsPos();
		return Raphael.angle(pos1.x, pos1.y, pos2.x, pos2.y);
	},
	setCanvas: function(canvas) {
		this.canvas = canvas;
	},
	paint: function() {
		this.path = this.canvas.path(this.getPath());
		this.path.toBack();
		var pos = this.getAbsPos();
		this.handle = this.canvas.rect(pos.x-5, pos.y-5, 10, 10).attr({fill: "#4040FF", transform: "R"+this.getAngle()});
		$(this.handle.node).attr("class", "tomato connection");
		this.handle.node.obj = this;
	},
	paintUpdate: function(){
		var pos = this.getAbsPos();
		this.path.attr({path: this.getPath()});
		this.handle.attr({x: pos.x-5, y: pos.y-5, transform: "R"+this.getAngle()});
	},
	action: function(action, params) {
		log("Connection action: "+action);
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

$.contextMenu({
	selector: '.tomato.connection',
	build: function(trigger, e) {
		var obj = trigger[0].obj;
		return {
			callback: function(key, options) {
				alert("Clicked " + key);
			},
			items: {
				"header": {html:'<span>Connection '+obj.id+'</span>', type:"html"},
				"configure": {name:'Configure', icon:'configure'},
				"remove": {name:'Delete', icon:'remove'},
			}
		}
	}
});


var Element = Class.extend({
	init: function(editor, data) {
		this.editor = editor;
		this.data = data;
		this.id = data.id;
		this.children = [];
		this.connection = null;
	},
	onDragged: function() {
	},
	isMovable: function() {
		return !this.editor.options.fixed_pos;
	},
	enableDragging: function(obj) {
		obj.drag(function(dx, dy, x, y) { //move
			if (!this.isMovable()) return;
			this.setAbsPos({x: this.opos.x + dx, y: this.opos.y + dy});
		}, function() { //start
			this.opos = this.getAbsPos();
		}, function() { //stop
			this.onDragged();
		}, this, this, this);
	},
	getPos: function() {
		if (! this.data.attrs._pos) this.data.attrs._pos = {x: Math.random(), y: Math.random()};
		return this.data.attrs._pos;
	},
	setPos: function(pos) {
		if (this.editor.options.fixed_pos) return;
		this.data.attrs._pos = {x: Math.min(1, Math.max(0, pos.x)), y: Math.min(1, Math.max(0, pos.y))};
		this.onPosChanged(true);
	},
	onPosChanged: function(con) {
		this.paintUpdate();
		for (var i=0; i<this.children.length; i++) this.children[i].onPosChanged(con);
		if (con && this.connection) {
			this.connection.otherElement(this).onPosChanged(false);
			this.connection.paintUpdate();
		}
	},
	getAbsPos: function() {
		return this.canvas.absPos(this.getPos());
	},
	setAbsPos: function(pos) {
		var grid = this.editor.options.grid_size;
		if (this.editor.options.snap_to_grid) pos = {x: Math.round(pos.x/grid)*grid, y: Math.round(pos.y/grid)*grid};
		this.setPos(this.canvas.relPos(pos));
	},
	setCanvas: function(canvas) {
		this.canvas = canvas;
	},
	paint: function() {
	},
	paintUpdate: function() {
	},
	action: function(action, params) {
		log("Element action: "+action);
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

$.contextMenu({
	selector: '.tomato.element',
	build: function(trigger, e) {
		var obj = trigger[0].obj;
		return {
			callback: function(key, options) {
				alert("Clicked " + key);
			},
			items: {
				"header": {html:'<span>Element '+obj.data.attrs.name+'</span>', type:"html"},
				"connect": {name:'Connect', icon:'connect'},
				"sep1": "---",
				"control": {
					"name": "Control",
					"icon": "control",
					"items": {
						"start": {name:'Start', icon:'start', callback: function(){obj.action_start();}},
						"stop": {name:"Stop", icon:"stop", callback: function(){obj.action_stop();}},
						"prepare": {name:"Prepare", icon:"prepare", callback: function(){obj.action_prepare();}},
						"destroy": {name:"Destroy", icon:"destroy", callback: function(){obj.action_destroy();}},
					}
				},
				"configure": {name:'Configure', icon:'configure'},
				"sep2": "---",
				"remove": {name:'Delete', icon:'remove'},
			}
		}
	}
});

var UnknownElement = Element.extend({
	paint: function() {
		var pos = this.getAbsPos();
		this.circle = this.canvas.circle(pos.x, pos.y, 15).attr({fill: "#CCCCCC"});
		this.innerText = this.canvas.text(pos.x, pos.y, "?").attr({"font-size": 25});
		this.text = this.canvas.text(pos.x, pos.y+22, this.data.type + ": " + this.data.attrs.name);
		this.enableDragging(this.circle);
		this.enableDragging(this.innerText);
	},
	paintUpdate: function() {
		var pos = this.getAbsPos();
		this.circle.attr({cx: pos.x, cy:pos.y});
		this.innerText.attr({x: pos.x, y:pos.y});
		this.text.attr({x: pos.x, y: pos.y+22});
		this.enableDragging(this.circle);
		$(this.circle.node).attr("class", "tomato element");
		this.circle.node.obj = this;
	}
});

var IconElement = Element.extend({
	init: function(editor, data) {
		this._super(editor, data);
		this.iconUrl = "img/" + this.data.type + "32.png";
		this.iconSize = {x: 32, y:32};
		this.busy = false;
	},
	isMovable: function() {
		return this._super() && !this.busy;
	},
	updateStateIcon: function() {
		if (this.busy) {
			this.stateIcon.attr({src: "img/loading.gif", opacity: 1.0});
			return;			
		}
		switch (this.data.state) {
			case "started":
				this.stateIcon.attr({src: "img/started.png", opacity: 1.0});
				break;
			case "prepared":
				this.stateIcon.attr({src: "img/prepared.png", opacity: 1.0});
				break;
			case "created":
			default:
				this.stateIcon.attr({src: "img/pixel.png", opacity: 0.0});
				break;
		}
	},
	paint: function() {
		var pos = this.canvas.absPos(this.getPos());
		this.icon = this.canvas.image(this.iconUrl, pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2, this.iconSize.x, this.iconSize.y);
		this.text = this.canvas.text(pos.x, pos.y+this.iconSize.y/2+5, this.data.attrs.name);
		this.stateIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2-10, pos.y+this.iconSize.y/2-10, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		this.updateStateIcon();
		//hide icon below rect to disable special image actions on some browsers
		this.rect = this.canvas.rect(pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2+5, this.iconSize.x, this.iconSize.y + 10).attr({opacity: 0.0, fill:"#FFFFFF"});
		this.enableDragging(this.rect);
		$(this.rect.node).attr("class", "tomato element");
		this.rect.node.obj = this;
	},
	paintUpdate: function() {
		var pos = this.getAbsPos();
		this.icon.attr({x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2});
		this.stateIcon.attr({x: pos.x+this.iconSize.x/2-10, y: pos.y+this.iconSize.y/2-10});
		this.rect.attr({x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2+5});
		this.text.attr({x: pos.x, y: pos.y+this.iconSize.y/2+5});
		this.updateStateIcon();
	},
	action: function(action, params) {
		this.busy = true;
		this.updateStateIcon();
		this._super(action, params);
	}
});

var VPNElement = IconElement.extend({
	init: function(editor, data) {
		this._super(editor, data);
		this.iconUrl = "img/" + this.data.attrs.mode + "32.png";
		this.iconSize = {x: 32, y:16};
	}
});

var VMElement = IconElement.extend({
});

var VMInterfaceElement = Element.extend({
	getHandlePos: function() {
		var ppos = this.parent.getAbsPos();
		var cpos = this.connection.getCenter();
		var xd = cpos.x - ppos.x;
		var yd = cpos.y - ppos.y;
		var magSquared = (xd * xd + yd * yd);
		var mag = 14.0 / Math.sqrt(magSquared);
		return {x: ppos.x + (xd * mag), y: ppos.y + (yd * mag)};
	},
	getAbsPos: function() {
		return this.parent.getAbsPos();
	},
	paint: function() {
		var pos = this.getHandlePos();
		this.circle = this.canvas.circle(pos.x, pos.y, 7).attr({fill: "#CDCDB3"});
		$(this.circle.node).attr("class", "tomato element");
		this.circle.node.obj = this;
	},
	paintUpdate: function() {
		var pos = this.getHandlePos();
		this.circle.attr({cx: pos.x, cy: pos.y});
	}
});

var HiddenChildElement = Element.extend({
	getPos: function() {
		return this.parent.getPos();
	},
	getAbsPos: function() {
		return this.parent.getAbsPos();
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
	}
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
		this.options.grid_size = this.options.grid_size || 25;
		this.options.frame_size = this.options.frame_size || this.options.grid_size;
		this.topology = new Topology(this, options.topology);
		this.menu = new Menu(this.options.menu_container);
		this.workspace = new Workspace(this.options.workspace_container, this);
		this.templates = new TemplateStore(this.options.templates);
		this.buildMenu();
		this.topology.paint(this.workspace.canvas);
	},
	onOptionChanged: function(name) {
		this.workspace.onOptionChanged(name);
	},
	optionMenuItem: function(options) {
		var t = this;
		return Menu.checkbox({
			name: options.name, label: options.label, tooltip: options.tooltip,
			func: function(value){
				t.options[options.name]=value;
			  t.onOptionChanged(options.name);
			},
			checked: this.options[options.name]
		});
	},
	buildMenu: function() {
		var t = this;
	
		var toggleGroup = new ToggleGroup();
	
		var tab = this.menu.addTab("Home");

		var group = tab.addGroup("Modes");
		group.addElement(Menu.button({label: "Select & Move", icon: "img/select32.png", toggle: true, toggleGroup: toggleGroup, small: false, checked: true}));
		group.addStackedElements([
			Menu.button({label: "Connect", icon: "img/connect16.png", toggle: true, toggleGroup: toggleGroup, small: true}),
			Menu.button({label: "Delete", name: "mode-remove", icon: "img/eraser16.png", toggle: true, toggleGroup: toggleGroup, small: true})
		]);

		var group = tab.addGroup("Topology control");
		group.addElement(Menu.button({label: "Start", icon: "img/start32.png", toggle: false, small: false, func: function() {t.topology.action_start();}}));
		group.addElement(Menu.button({label: "Stop", icon: "img/stop32.png", toggle: false, small: false, func: function() {t.topology.action_start();}}));
		group.addStackedElements([
			Menu.button({label: "Prepare", icon: "img/prepare16.png", toggle: false, small: true, func: function() {t.topology.action_prepare();}}),
			Menu.button({label: "Destroy", icon: "img/destroy16.png", toggle: false, small: true, func: function() {t.topology.action_destroy();}}),
			Menu.button({label: "Delete", name: "topology-remove", icon: "img/eraser16.png", toggle: false, small: true, func: function() {t.topology.remove();}})
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

		var group = tab.addGroup("Upload own images");
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
			Menu.button({label: "Export", icon: "img/export16.png", toggle: false, small: true})
		]);
		group.addElement(Menu.button({label: "Users & Permissions", icon: "img/user32.png", toggle: false, small: false}));


		var tab = this.menu.addTab("Options");

		var group = tab.addGroup("Editor");		
		group.addStackedElements([
			this.optionMenuItem({name:"safe_mode", label:"Safe mode", tooltip:"Asks before all destructive actions"}),
			this.optionMenuItem({name:"snap_to_grid", label:"Snap to grid", tooltip:"All elements snap to an invisible "+this.options.grid_size+" pixel grid"}),
			this.optionMenuItem({name:"fixed_pos", label:"Fixed positions", tooltip:"Elements can not be moved"}), 
			this.optionMenuItem({name:"beginner_mode", label:"Beginner mode", tooltip:"Displays help messages for all elements"})
		]);

		this.menu.paint();
	}
});
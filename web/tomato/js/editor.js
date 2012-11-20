// http://marijnhaverbeke.nl/uglifyjs

var ajax = function(options) {
	var t = this;
	$.ajax({
		type: "POST",
	 	async: true,
	 	url: "../ajax/" + options.url,
	 	data: {data: $.toJSON(options.data || {})},
	 	complete: function(res) {
	 		if (res.status != 200) return options.errorFn ? options.errorFn(res.statusText) : null;
	 		var msg = $.parseJSON(res.responseText);
	 		if (! msg.success) return options.errorFn ? options.errorFn(msg.error) : null;
	 		return options.successFn ? options.successFn(msg.result) : null;
	 	}
	});
};

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

var FormElement = Class.extend({
	init: function(options) {
		this.options = options;
		this.name = options.name || options.label;
		this.label = options.label || options.name;
		if (options.callback) this.callback = options.callback;
		this.element = null;
	},
	getElement: function() {
		return this.element;
	},
	getLabel: function() {
		return this.label;
	},
	getName: function() {
		return this.name;
	},
	setEnabled: function(value) {
		this.element.attr({disabled: !value});
	},
	onChanged: function(value) {
		if (this.isValid(value)) {
			this.element.removeClass("invalid");
			this.element.addClass("valid");
		} else {
			this.element.removeClass("valid");
			this.element.addClass("invalid");
		}
		if (this.callback) this.callback(this, value);
	},
	isValid: function(value) {
		return true;
	}
});

var TextElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.pattern = options.pattern || /^.*$/;
		this.element = $('<input class="form-element" size=10 type="'+(options.password ? "password" : "text")+'" name="'+this.name+'"/>');
		if (options.disabled) this.element.attr({disabled: true});
		var t = this;
		this.element.change(function() {
			t.onChanged(this.value);
		});
		if (options.value != null) this.setValue(options.value);
	},
	getValue: function() {
		return this.element[0].value;
	},
	setValue: function(value) {
		this.element[0].value = value;
	},
	isValid: function(value) {
		var val = value || this.getValue();
		return this.pattern.test(val);
	}
});

var CheckboxElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.element = $('<input class="form-element" type="checkbox" name="'+this.name+'"/>');
		if (options.disabled) this.element.attr({disabled: true});
		var t = this;
		this.element.change(function() {
			t.onChanged(this.checked);
		});
		if (options.value != null) this.setValue(options.value);
	},
	getValue: function() {
		return this.element[0].checked;
	},
	setValue: function(value) {
		this.element[0].checked = value;
	}
});

var ChoiceElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.element = $('<select class="form-element" name="'+this.name+'"/>');
		if (options.disabled) this.element.attr({disabled: true});
		var t = this;
		this.element.change(function() {
			t.onChanged(this.value);
		});
		this.choices = options.choices || {};
		this.setChoices(this.choices);
		if (options.value != null) this.setValue(options.value);
	},
	setChoices: function(choices) {
		this.element.find("option").remove();
		for (var name in choices) this.element.append($('<option value="'+name+'">'+choices[name]+'</option>'));
		this.setValue(this.getValue());
	},
	getValue: function() {
		return this.element[0].value;
	},
	setValue: function(value) {
		var options = this.element.find("option");
		for (var i=0; i < options.length; i++) {
			$(options[i]).attr({selected: options[i].value == value});
		}
	}
});

var Window = Class.extend({
	init: function(options) {
		this.options = options;
		this.options.position = options.position || 'center center';
		this.div = $('<div/>').dialog({
			autoOpen: false,
			draggable: false,
			resizable: false,
			height: options.height || "auto",
			width: options.width || "auto",
			maxHeight:600,
			maxWidth:800,
			title: options.title,
			show: "slide",
			hide: "slide",
			minHeight:50,
			modal: true,
			buttons: options.buttons || {}
		});
		this.setPosition(options.position);
		if (options.content) this.div.append(options.content);
		if (options.autoShow) this.show();
	},
	setTitle: function(title) {
		this.div.dialog("option", "title", title);
	},
	setPosition: function(position) {
		this.div.dialog("option", "position", position);
	},
	show: function() {
		this.setPosition(this.position);
		this.div.dialog("open");
	},
	hide: function() {
		this.div.dialog("close");
	},
	toggle: function() {
		if (this.div.dialog("isOpen")) this.hide();
		else this.show();
	},
	add: function(div) {
		this.div.append(div);
	},
	getDiv: function() {
		return this.div;
	}
});

var AttributeWindow = Window.extend({
	init: function(options) {
		this._super(options);
		this.table = $('<table/>');
		this.div.append(this.table);
		this.elements = [];
	},
	add: function(element) {
		this.elements.push(element);
		var tr = $("<tr/>");
		tr.append($("<td/>").append(element.getLabel()));
		tr.append($("<td/>").append(element.getElement()));
		this.table.append(tr);
	},
	autoElement: function(info, value) {
		var el;
		if (info.options) {
			el = new ChoiceElement({
				label: info.desc || info.name,
				name: info.name,
				choices: info.options,
				value: value || info["default"],
				disabled: !info.enabled
			});
		} else if (info.type == "bool") {
			el = new CheckboxElement({
				label: info.desc || info.name,
				name: info.name,
				value: value || info["default"],
				disabled: !info.enabled
			});
		} else {
			el = new TextElement({
				label: info.desc || info.name,
				name: info.name,
				value: value || info["default"],
				disabled: !info.enabled
			});
		}
		return el;
	},
	autoAdd: function(info, value) {
		this.add(this.autoElement(info, value));
	},
	getValues: function() {
		var values = {};
		for (var i=0; i < this.elements.length; i++) values[this.elements[i].name] = this.elements[i].getValue();
		return values;
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
    	this.beginnerHelp = this.canvas.text(c.width/2, c.height/4, "").attr({"font-size": 25, "fill": "#999999"});
    	this.updateBeginnerHelp();
		var t = this;
		this.connectPath = this.canvas.path("M0 0L0 0").attr({"stroke-dasharray": "- "});
		this.container.click(function(evt){
			t.onClicked(evt);
		});
		this.container.mousemove(function(evt){
			t.onMouseMove(evt);
		});
	},
	updateBeginnerHelp: function() {
		if (! this.editor.options.beginner_mode) {
			this.beginnerHelp.hide();
			return;
		}
		var text = "";
		if (this.editor.topology.elementCount() == 0) { 
			text = "Select an element from the palette\nand click into the workspace to\nadd it to the topology.";
		} else if (this.editor.topology.elementCount() < 3) { 
			text = "Add some other elements to the topology\nso you can create connections.";
		} else if (this.editor.topology.connectionCount() == 0) {
 			text = "Right-click on an element, select connect\nand click on another element to\nconnect these elements.";
		} else if (this.editor.topology.connectionCount() < 2) { 
			text = "Add another connection so your\ntopology is fully connected.";
		}
		this.beginnerHelp.attr({text: text});
		if (text) this.beginnerHelp.show();
		else this.beginnerHelp.hide();
		window.setTimeout("editor.workspace.updateBeginnerHelp();", 1000);
	},
	onMouseMove: function(evt) {
		if (! this.editor.connectElement) {
			this.connectPath.hide();
			return;
		}
		this.connectPath.show();
		var pos = this.editor.connectElement.getAbsPos();
		var mousePos = {x: evt.pageX - this.container.offset().left, y: evt.pageY - this.container.offset().top};
		this.connectPath.attr({path: "M"+pos.x+" "+pos.y+"L"+mousePos.x+" "+mousePos.y});
	},
	onClicked: function(evt) {
		switch (this.editor.mode) {
			case Mode.position:
				var pos;
				if (evt.offsetX) pos = this.canvas.relPos({x: evt.offsetX, y: evt.offsetY});
				else {
					var objPos = this.container.offset();
					pos = this.canvas.relPos({x: evt.pageX - objPos.left, y: evt.pageY - objPos.top});
				}
				this.editor.positionElement(pos);
				break;
			default:
				break;
		}
	},
	onOptionChanged: function(name) {
    	this.updateBeginnerHelp();
	},
	onModeChanged: function(mode) {
		for (var name in Mode) this.container.removeClass("mode_" + Mode[name]);
		this.container.addClass("mode_" + mode);
	}
});

var Topology = Class.extend({
	init: function(editor) {
		this.editor = editor;
		this.elements = {};
		this.connections = {};
	},
	_getCanvas: function() {
		return this.editor.workspace.canvas;
	},
	loadElement: function(el) {
		var elObj;
		switch (el.type) {
			case "kvm":
			case "kvmqm":
			case "openvz":
			case "repy":
				elObj = new VMElement(this, el, this._getCanvas());
				break;
			case "kvm_interface":
			case "kvmqm_interface":
			case "openvz_interface":
			case "repy_interface":
				elObj = new VMInterfaceElement(this, el, this._getCanvas());
				break;
			case "external_network":
				elObj = new ExternalNetworkElement(this, el, this._getCanvas());
				break;
			case "external_network_endpoint":
				//hide external network endpoints with external_network parent but show endpoints without parent 
				elObj = el.parent ? new SwitchPortElement(this, el, this._getCanvas()) : new ExternalNetworkElement(this, el, this._getCanvas()) ;
				break;
			case "tinc_vpn":
				elObj = new VPNElement(this, el, this._getCanvas());
				break;
			case "tinc_endpoint":
				//hide tinc endpoints with tinc_vpn parent but show endpoints without parent 
				elObj = el.parent ? new SwitchPortElement(this, el, this._getCanvas()) : new VPNElement(this, el, this._getCanvas()) ;
				break;
			default:
				elObj = new UnknownElement(this, el, this._getCanvas());
				break;
		}
		if (el.id) this.elements[el.id] = elObj;
		if (el.parent) {
			//parent id is less and thus objects exists
			elObj.parent = this.elements[el.parent];
			this.elements[el.parent].children.push(elObj);
		}
		elObj.paint();
		return elObj;
	},
	loadConnection: function(con, elements) {
		var conObj = new Connection(this, con, this._getCanvas());
		if (con.id) this.connections[con.id] = conObj;
		if (con.elements) { //elements are given by id
			for (var j=0; j<con.elements.length; j++) {
				this.elements[con.elements[j]].connection = conObj;
				conObj.elements.push(this.elements[con.elements[j]]);
			}
		} else { //elements are given by object reference 
			for (var j=0; j<elements.length; j++) {
				elements[j].connection = conObj;
				conObj.elements.push(elements[j]);
			}
		}
		conObj.paint();
		return conObj;
	},
	load: function(data) {
		this.data = data;
		this.id = data.id;
		this.elements = {};
		//sort elements by id so parents get loaded before children
		data.elements.sort(function(a, b){return a.id - b.id;});
		for (var i=0; i<data.elements.length; i++) this.loadElement(data.elements[i]);
		this.connections = {};
		for (var i=0; i<data.connections.length; i++) this.loadConnection(data.connections[i]);
		
		this.settingOptions = true;
		var opts = ["safe_mode", "snap_to_grid", "fixed_pos", "beginner_mode", "debug_mode"];
		for (var i = 0; i < opts.length; i++) {
			if (this.data.attrs["_"+opts[i]] != null) this.editor.setOption(opts[i], this.data.attrs["_"+opts[i]]);
		}
		this.settingOptions = false;		
	},
	setBusy: function(busy) {
		this.busy = busy;
	},
	modify: function(attrs) {
		this.setBusy(true);
		log("Modify topology #"+this.id);
		log(attrs);
		var t = this;
		//TODO: success and error callbacks
		ajax({
			url: 'topology/'+this.id+'/modify',
		 	data: {attrs: attrs},
		});
	},
	modify_value: function(name, value) {
		var attrs = {};
		attrs[name] = value;
		this.modify(attrs);
		this.data.attrs[name] = value;
	},
	isEmpty: function() {
		for (var id in this.elements) if (this.elements[id] != this.elements[id].constructor.prototype[id]) return false;
		return true;
		//no connections without elements
	},
	elementCount: function() {
		var count = 0;
		for (var id in this.elements) count++;
		return count;
	},
	connectionCount: function() {
		var count = 0;
		for (var id in this.connections) count++;
		return count;
	},
	nextElementName: function(data) {
		var names = [];
		for (var id in this.elements) names.push(this.elements[id].data.attrs.name);
		var base;
		switch (data.type) {
			case "external_network":
				base = data.attrs.kind || "internet";
				break;
			case "external_network_endpoint":
				base = (data.attrs.kind || "internet") + "_endpoint";
				break;		
			case "tinc_vpn":
				base = data.attrs.mode || "switch";
				break;
			case "tinc_endpoint":
				base = "tinc";
				break;		
			default:
				base = data.type;
		}
		var num = 1;
		while (names.indexOf(base+num) != -1) num++;
		return base+num;
	},
	createElement: function(data, callback) {
		log("Create element");
		log(data);
		data.attrs = data.attrs || {};
		if (!data.parent) data.attrs.name = data.attrs.name || this.nextElementName(data);
		var obj = this.loadElement(data);
		obj.setBusy(true);
		var t = this;
		ajax({
			url: "topology/" + this.id + "/create_element",
			data: data,
			successFn: function(data) {
				obj.setBusy(false);
				obj.updateData(data);
				t.elements[data.id] = obj;
				if (callback) callback(obj);
			},
			errorFn: function(error) {
				alert(error);
				obj.paintRemove();
			}
		});
		return obj;
	},
	createConnection: function(el1, el2, data) {
		if (el1 == el2) return;
		if (! el1.isConnectable()) return;
		if (! el2.isConnectable()) return;
		var ids = 0;
		var t = this;
		var obj;
		var callback = function(ready) {
			ids++;
			if (ids < 2) return;
			data.elements = [el1.id, el2.id];
			ajax({
				url: "connection/create",
				data: data,
				successFn: function(data) {
					obj.updateData(data);
					t.connections[data.id] = obj;
				},
				errorFn: function(error) {
					alert(error);
					obj.paintRemove();
				}
			});
		};
		el1 = el1.getConnectTarget(callback);
		el2 = el2.getConnectTarget(callback);
		data = data || {};
		data.attrs = data.attrs || {};
		obj = this.loadConnection(data, [el1, el2]);
		return obj;
	},
	onOptionChanged: function(name) {
		if (this.settingOptions) return;
		this.modify_value("_" + name, this.editor.options[name]);
	},
	action: function(action, options) {
		var options = options || {};
		if ((action=="destroy"||action=="stop") && !options.noask && this.editor.options.safe_mode && ! confirm("Do you want to " + action + " this topology?")) return;
		var ids = 0;
		var cb = function() {
			ids--;
			if (ids <= 0 && options.callback) options.callback();
		}
		for (var id in this.elements) {
			var el = this.elements[id];
			if (el.busy) continue;
			if (el.parent) continue;
			if (el.actionAvailable(action)) {
				el.action(action, {
					noask: true,
					callback: cb
				});
				ids++;
			}
		}
		if (ids <= 0 && options.callback) options.callback();
	},
	action_start: function() {
		var t = this;
		this.action("prepare", {
			callback: function(){
				t.action("start", {});
			}
		});
	},
	action_stop: function() {
		this.action("stop");
	},
	action_prepare: function() {
		this.action("prepare");
	},
	action_destroy: function() {
		var t = this;
		this.action("stop", {
			callback: function(){
				t.action("destroy", {});
			}
		});
	},
	remove: function() {
		alert("Not implemented yet.");
	},
	showUsage: function() {
  		window.open('/topology/'+this.id+'/usage', '_blank', 'innerHeight=450,innerWidth=650,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
	},
	notesDialog: function() {
		var dialog = $("<div/>");
		var ta = $('<textarea cols=60 rows=20 class="notes"></textarea>');
		ta.text(this.data.attrs._notes || "");
		dialog.append(ta);
		var t = this;
		dialog.dialog({
			autoOpen: true,
			draggable: false,
			resizable: true,
			height: "auto",
			width: "auto",
			title: "Notes for Topology",
			show: "slide",
			hide: "slide",
			modal: true,
			buttons: {
				Save: function() {
		        	dialog.dialog("close");
			      	t.modify_value("_notes", ta.val());
			    },
		        Close: function() {
		        	dialog.dialog("close");
		        }				
			}
		});
	},
	renameDialog: function() {
		var name = prompt("Topology name:", this.data.attrs.name);
		if (name) {
			this.modify_value("name", name);
			$('#topology_name').text("Topology '"+this.data.attrs.name+"' [#"+this.id+"]");
		}
	},
	name: function() {
		return this.data.attrs.name;
	}
});

$.contextMenu({
	selector: '.tomato.workspace',
	build: function(trigger, e) {
		var obj = trigger[0].obj;
		return {
			callback: function(key, options) {},
			items: {
				"header": {
					html:'<span>Topology "'+obj.name()+'"</span>',
					type:"html"
				},
				"start": {
					name:'Start',
					icon:'start',
					callback: function(){
						obj.action_start();
					}
				},
				"stop": {
					name:"Stop",
					icon:"stop",
					callback: function(){
						obj.action_stop();
					}
				},
				"prepare": {
					name:"Prepare",
					icon:"prepare",
					callback: function(){
						obj.action_prepare();
					}
				},
				"destroy": {
					name:"Destroy",
					icon:"destroy",
					callback:function(){
						obj.action_destroy();
					}
				},
				"sep1": "---",
				"notes": {
					name:"Notes",
					icon:"notes",
					callback: function(){
						obj.notesDialog();
					}
				},
				"usage": {
					name:"Usage",
					icon:"usage",
					callback: function(){
						obj.showUsage();
					}
				},
				"sep2": "---",
				"remove": {name:'Delete', icon:'remove'}
			}
		};
	}
});

var Component = Class.extend({
	init: function(topology, data, canvas) {
		this.topology = topology;
		this.editor = topology.editor;
		this.data = data;
		this.canvas = canvas;
		this.id = data.id;
	},	
	paint: function() {
	},
	paintUpdate: function() {
	},
	paintRemove: function() {
	},
	setBusy: function(busy) {
		this.busy = busy;
	},
	updateData: function(data) {
		if (data) this.data = data;
		this.id = this.data.id;
		this.paintUpdate();
	},
	showDebugInfo: function() {
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/info',
		 	data: {},
		 	successFn: function(result) {
		 		var win = new Window({
		 			title: "Debug info",
		 			location: "center center",
		 			height: 600,
		 			width: 800,
		 			buttons: {
		 				Close: function() {
		 					win.hide();
		 				}
					} 
		 		});
		 		win.add($("<pre></pre>").text(JSON.stringify(result, undefined, 2)));
		 		win.show();
		 	},
		 	errorFn: function(error) {
		 		alert(error);
		 	}
		});
	},
	showUsage: function() {
  		window.open('../'+this.component_type+'/'+this.id+'/usage', '_blank', 'innerHeight=450,innerWidth=650,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
	},
	configWindowSettings: function() {
		return {
			order: ["name"],
			ignore: [],
			unknown: true,
			special: {}
		} 
	},
	showConfigWindow: function() {
		var absPos = this.getAbsPos();
		var wsPos = this.editor.workspace.container.position();
		var t = this;
		this.configWindow = new AttributeWindow({
			title: "Attributes",
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) if (values[name] == t.data.attrs[name]) delete values[name];
					t.modify(values);					
					t.configWindow = null;
				},
				Cancel: function() {
					t.configWindow.hide();
					t.configWindow = null;
				} 
			}
		});
		var settings = this.configWindowSettings();
		for (var i=0; i<settings.order.length; i++) {
			var name = settings.order[i];
			if (settings.special[name]) this.configWindow.add(settings.special[name]);
			else if (this.data.cap_attrs[name]) this.configWindow.autoAdd(this.data.cap_attrs[name], this.data.attrs[name]);
		}
		if (settings.unknown) {
			for (var name in this.data.cap_attrs) {
				if (settings.order.indexOf(name) >= 0) continue; //do not repeat ordered fields
				if (settings.ignore.indexOf(name) >= 0) continue;
				if (settings.special[name]) this.configWindow.add(settings.special[name]);
				else if (this.data.cap_attrs[name]) this.configWindow.autoAdd(this.data.cap_attrs[name], this.data.attrs[name]);
			}
		}
		this.configWindow.show();
	},
	modify: function(attrs) {
		this.setBusy(true);
		log("Modify "+this.component_type+" #"+this.id);
		log(attrs);
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/modify',
		 	data: {attrs: attrs},
		 	successFn: function(result) {
		 		t.updateData(result);
		 		t.setBusy(false);
		 	},
		 	errorFn: function(error) {
		 		alert(error);
		 		t.setBusy(false);
		 	}
		});
	},
	modify_value: function(name, value) {
		var attrs = {};
		attrs[name] = value;
		this.modify(attrs);
	},
	action: function(action, options) {
		var options = options || {};
		if ((action=="destroy"||action=="stop") && !options.noask && this.editor.options.safe_mode && ! confirm("Do you want to " + action + " this "+this.component_type+"?")) return;
		this.setBusy(true);
		var params = options.params || {};
		log(this.component_type+" action #"+this.id+": "+action);
		log(params);
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/action',
		 	data: {action: action, params: params},
		 	successFn: function(result) {
		 		t.updateData(result[1]);
		 		t.setBusy(false);
		 		if (options.callback) options.callback(t, result[0], result[1]);
		 	},
		 	errorFn: function(error) {
		 		alert(error);
		 		t.setBusy(false);
		 	}
		});
	}
});

var ConnectionAttributeWindow = AttributeWindow.extend({
	init: function(options, con) {
		this._super(options);
		this.table.append($("<tr/>").append($("<th colspan=4>Link emulation</th>")));
		this.emulation_elements = [];
		var t = this;
		var el = new CheckboxElement({
			name: "emulation",
			value: con.data.attrs.emulation,
			callback: function(el, value) {
				t.updateEmulationStatus(value);
			}
		});
		this.elements.push(el);
		this.table.append($("<tr/>").append($("<td>Enabled</td>")).append($("<td colspan=3/>").append(el.getElement())));
		//direction arrows
		var size = 30;
		var _div = '<div style="width: '+size+'px; height: '+size+'px;"/>';
		var dir1 = $(_div); var dir2 = $(_div);
    	var canvas1 = Raphael(dir1[0], size, size);
    	var canvas2 = Raphael(dir2[0], size, size);
    	var _path1 = "M 0.1 0.5 L 0.9 0.5";
    	var _path2 = "M 0.7 0.5 L 0.4 0.3 M 0.7 0.5 L 0.4 0.7";
    	var _transform1 = "R"+con.getAngle()+",0.5,0.5S"+size+","+size+",0,0";
    	var _transform2 = "R"+(con.getAngle()+180)+",0.5,0.5S"+size+","+size+",0,0";
    	var _attrs = {"stroke-width": 2, stroke: "red", "stroke-linecap": "round", "stroke-linejoin": "round"};
    	canvas1.path(_path1).transform(_transform1);
    	canvas1.path(_path2).transform(_transform1).attr(_attrs);
    	canvas2.path(_path1).transform(_transform2);
    	canvas2.path(_path2).transform(_transform2).attr(_attrs);
    	var name1 = con.elements[0].name();
    	var name2 = con.elements[1].name();
    	if (con.elements[0].id > con.elements[1].id) {
    		var t = name1;
    		name1 = name2;
    		name2 = t;
    	}
    	var fromDir = $("<div>From " + name1 + "<br/>to " + name2 + "</div>");
    	var toDir = $("<div>From " + name2 + " <br/>to " + name1 + "</div>");
		this.table.append($('<tr/>')
				.append($("<th>Direction</th>"))
				.append($('<td align="middle"/>').append(fromDir).append(dir1))
				.append($('<td align="middle"/>').append(toDir).append(dir2))
				.append($('<td>&nbsp;</td>'))
		);
		//simple fields
		var order = ["bandwidth", "delay", "jitter", "distribution", "lossratio", "duplicate", "corrupt"];
		for (var i = 0; i < order.length; i++) {
			var name = order[i];
			var el_from = this.autoElement(con.data.cap_attrs[name+"_from"], con.data.attrs[name+"_from"])
			this.elements.push(el_from);
			this.emulation_elements.push(el_from);
			var el_to = this.autoElement(con.data.cap_attrs[name+"_to"], con.data.attrs[name+"_to"])
			this.elements.push(el_to);
			this.emulation_elements.push(el_to);
			this.table.append($("<tr/>")
					.append($("<td/>").append(con.data.cap_attrs[name+"_to"].desc))
					.append($("<td/>").append(el_from.getElement()))
					.append($("<td/>").append(el_to.getElement()))
					.append($("<td/>").append(con.data.cap_attrs[name+"_to"].unit))
			);
		}
		this.updateEmulationStatus(con.data.attrs.emulation);
		
		this.table.append($("<tr/>").append($("<td colspan=4>&nbsp;</td>")));		
		this.table.append($("<tr/>").append($("<th colspan=4>Packet capturing</th>")));
		this.capturing_elements = [];
		var el = new CheckboxElement({
			name: "capturing",
			value: con.data.attrs.capturing,
			callback: function(el, value) {
				t.updateCapturingStatus(value);
			}
		});
		this.elements.push(el);
		this.table.append($("<tr/>").append($("<td>Enabled</td>")).append($("<td colspan=3/>").append(el.getElement())));
		var order = ["capture_mode", "capture_filter"];
		for (var i = 0; i < order.length; i++) {
			var name = order[i];
			var el = this.autoElement(con.data.cap_attrs[name], con.data.attrs[name])
			this.capturing_elements.push(el);
			this.elements.push(el);
			this.table.append($("<tr/>")
					.append($("<td/>").append(con.data.cap_attrs[name].desc))
					.append($("<td colspan=3/>").append(el.getElement()))
			);
		}
		this.updateCapturingStatus(con.data.attrs.capturing);
	},
	updateEmulationStatus: function(enabled) {
		for (var i=0; i<this.emulation_elements.length; i++)
			 this.emulation_elements[i].setEnabled(enabled);
	},
	updateCapturingStatus: function(enabled) {
		for (var i=0; i<this.capturing_elements.length; i++)
			 this.capturing_elements[i].setEnabled(enabled);
	}
});


var Connection = Component.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.elements = [];
		this.component_type = "connection";
	},
	fromElement: function() {
		return this.elements[0].id < this.elements[1].id ? this.elements[0] : this.elements[1];
	},
	toElement: function() {
		return this.elements[0].id >= this.elements[1].id ? this.elements[0] : this.elements[1];
	},
	otherElement: function(me) {
		for (var i=0; i<this.elements.length; i++) if (this.elements[i].id != me.id) return this.elements[i];
	},
	onClicked: function() {
		this.editor.onConnectionSelected(this);
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
		var pos1 = this.toElement().getAbsPos();
		var pos2 = this.fromElement().getAbsPos();
		return Raphael.angle(pos1.x, pos1.y, pos2.x, pos2.y);
	},
	paint: function() {
		this.path = this.canvas.path(this.getPath());
		this.path.toBack();
		var pos = this.getAbsPos();
		this.handle = this.canvas.rect(pos.x-5, pos.y-5, 10, 10).attr({fill: "#4040FF", transform: "R"+this.getAngle()});
		$(this.handle.node).attr("class", "tomato connection removable");
		this.handle.node.obj = this;
		var t = this;
		$(this.handle.node).click(function() {
			t.onClicked();
		})
		for (var i=0; i<this.elements.length; i++) this.elements[i].paintUpdate();
	},
	paintRemove: function(){
		this.path.remove();
		this.handle.remove();
	},
	paintUpdate: function(){
		this.path.attr({path: this.getPath()});
		var pos = this.getAbsPos();
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
	showConfigWindow: function() {
		var absPos = this.getAbsPos();
		var wsPos = this.editor.workspace.container.position();
		var t = this;
		this.configWindow = new ConnectionAttributeWindow({
			title: "Attributes",
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) if (values[name] == t.data.attrs[name]) delete values[name];
					t.modify(values);					
					t.configWindow = null;
				},
				Cancel: function() {
					t.configWindow.hide();
					t.configWindow = null;
				} 
			}
		}, this);
		this.configWindow.show();
	},
	remove: function(callback, ask) {
		if (this.busy) return;
		if (ask && this.editor.options.safe_mode && ! confirm("Do you want to delete this connection?")) return;
		this.setBusy(true);
		var t = this;
		ajax({
			url: 'connection/'+this.id+'/remove',
		 	successFn: function(result) {
		 		t.paintRemove();
		 		delete t.topology.connections[t.id];
		 		for (var i=0; i<t.elements.length; i++) delete t.elements[i].connection;
		 		t.setBusy(false);
		 		if (callback) callback(t);
		 	},
		 	errorFn: function(error) {
		 		alert(error);
		 		t.setBusy(false);
		 	}
		});
		for (var i=0; i<t.elements.length; i++) t.elements[i].remove();
	},
	name: function() {
		return this.fromElement().name() + " &#x21C4; " + this.toElement().name();
	}
});

$.contextMenu({
	selector: '.tomato.connection',
	build: function(trigger, e) {
		var obj = trigger[0].obj;
		var menu = {
			callback: function(key, options) {},
			items: {
				"header": {
					html:'<span>Connection '+obj.name()+'</span>', type:"html"
				},
				"usage": {
					name:"Usage",
					icon:"usage",
					callback: function(){
						obj.showUsage();
					}
				},
				"configure": {
					name:'Configure',
					icon:'configure',
					callback: function(){
						obj.showConfigWindow();
					}
				},
				"debug": obj.editor.options.debug_mode ? {
					name:'Debug',
					icon:'debug',
					callback: function(){
						obj.showDebugInfo();
					}
				} : null,
				"remove": {
					name:'Delete',
					icon:'remove',
					callback: function(){
						obj.remove(null, true);
					}
				}
			}
		};
		for (var name in menu.items) {
			if (! menu.items[name]) delete menu.items[name]; 
		}
		return menu;
	}
});


var Element = Component.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.children = [];
		this.connection = null;
		this.component_type = "element";
	},
	onDragged: function() {
		if (!this.isMovable()) return;
		this.modify_value("_pos", this.getPos());
	},
	onClicked: function() {
		this.editor.onElementSelected(this);
	},
	isMovable: function() {
		return (!this.editor.options.fixed_pos) && this.editor.mode == Mode.select;
	},
	isConnectable: function() {
		if (this.connection) return false;
		if (! this.data.cap_children) return false;
		return this.data.cap_children.length > 0;
	},
	isRemovable: function() {
		return this.actionAvailable("(remove)");
	},
	actionAvailable: function(action) {
		return this.data.cap_actions && this.data.cap_actions.indexOf(action) > -1;
	},
	enableClick: function(obj) {
		obj.click(function() {
			this.onClicked();
		}, this);
	},
	enableDragging: function(obj) {
		obj.drag(function(dx, dy, x, y) { //move
			if (!this.isMovable()) return;
			this.setAbsPos({x: this.opos.x + dx, y: this.opos.y + dy});
		}, function() { //start
			if (!this.isMovable()) return false;
			this.opos = this.getAbsPos();
		}, function() { //stop
			var pos = this.getAbsPos();
			if (! this.opos) return;
			if (pos.x == this.opos.x && pos.y == this.opos.y) return;
			this.onDragged();
		}, this, this, this);
	},
	getConnectTarget: function() {
		return this;
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
	openConsole: function() {
	    window.open('../element/'+this.id+'/console', '_blank', "innerWidth=745,innerheight=400,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
	},
	openConsoleNoVNC: function() {
	    window.open('../element/'+this.id+'/console_novnc', '_blank', "innerWidth=760,innerheight=440,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
	},
	openVNCurl: function() {
		var host = this.data.attrs.host;
		var port = this.data.attrs.vncport;
		var passwd = this.data.attrs.vncpassword;
		var link = "vnc://:" + passwd + "@" + host + ":" + port;
	    window.open(link, '_self');
	},
	showVNCinfo: function() {
		var host = this.data.attrs.host;
		var port = this.data.attrs.vncport;
		var wport = this.data.attrs.websocket_port;
		var passwd = this.data.attrs.vncpassword;
		var link = "vnc://:" + passwd + "@" + host + ":" + port;
 		var win = new Window({
 			title: "VNC info",
 			content: '<p>Link: <a href="'+link+'">'+link+'</a><p>Host: '+host+"</p><p>Port: "+port+"</p><p>Websocket-Port: "+wport+"</p><p>Password: <pre>"+passwd+"</pre></p>",
 			autoShow: true
 		});
	},
	consoleAvailable: function() {
		return this.data.attrs.vncpassword && this.data.attrs.vncport && this.data.attrs.host;
	},
	downloadImage: function() {
		this.action("download_grant", {callback: function(el, res) {
			var name = el.topology.data.attrs.name + "_" + el.data.attrs.name;
			switch (el.data.type) {
				case "kvmqm":
				case "kvm":
					name += ".qcow2";
					break;
				case "openvz":
					name += ".tar.gz";
					break;
				case "repy":
					name += ".repy";
					break;
			}
			var url = "http://" + el.data.attrs.host + ":" + el.data.attrs.host_fileserver_port + "/" + res + "/download?name=" + name; 
			window.location.href = url;
		}})
	},
	uploadImage: function() {
		this.action("upload_grant", {callback: function(el, res) {
			var url = "http://" + el.data.attrs.host + ":" + el.data.attrs.host_fileserver_port + "/" + res + "/upload";
			var div = $('<div/>');
			var iframe = $('<iframe id="upload_target" name="upload_target"/>');
			iframe.css("display", "none");
			$('body').append(iframe);
			div.append('<form method="post" enctype="multipart/form-data" action="'+url+'" target="upload_target"><input type="file" name="upload"/><br/><input type="submit" value="upload"/></form>');
			iframe.load(function(){
				iframe.remove();
				info.hide();
				el.action("upload_use");
			});
			var info = new Window({title: "Upload image", content: div, autoShow: true});
		}});
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
	removeChild: function(ch) {
		for (var i = 0; i < this.children.length; i++)
	     if (this.children[i].id == ch.id)
	      this.children.splice(i, 1);
	},
	remove: function(callback, ask) {
		if (this.busy) return;
		if (ask && this.editor.options.safe_mode && ! confirm("Do you want to delete this element?")) return;
		this.setBusy(true);
		var t = this;
		var removed = false;
		var waiter = function(obj) {
			t.removeChild(obj);
			if (t.children.length) return;
			if (removed) return;
			removed = true;
			ajax({
				url: 'element/'+t.id+'/remove',
			 	successFn: function(result) {
			 		t.paintRemove();
			 		delete t.topology.elements[t.id];
			 		if (t.parent) t.parent.removeChild(t);
			 		t.setBusy(false);
			 		if (callback) callback(t);
			 	},
			 	errorFn: function(error) {
			 		alert(error);
			 		t.setBusy(false);
			 	}
			});			
		}
		for (var i=0; i<this.children.length; i++) this.children[i].remove(waiter);
		if (this.connection) this.connection.remove();
		waiter(this);
	},
	name: function() {
		var name = this.data.attrs.name;
		if (this.parent) name = this.parent.name() + "." + name;
		return name;
	}
});

$.contextMenu({
	selector: '.tomato.element',
	build: function(trigger, e) {
		var obj = trigger[0].obj;
		var menu = {
			callback: function(key, options) {},
			items: {
				"header": {html:'<span>Element '+obj.name()+'</span>', type:"html"},
				"connect": obj.isConnectable() ? {
					name:'Connect',
					icon:'connect',
					callback: function(){
						obj.editor.onElementConnectTo(obj);
					}
				} : null,
				"start": obj.actionAvailable("start") ? {
					name:'Start',
					icon:'start',
					callback: function(){
						obj.action_start();
					}
				} : null,
				"stop": obj.actionAvailable("stop") ? {
					name:"Stop",
					icon:"stop",
					callback: function(){
						obj.action_stop();
					}
				} : null,
				"prepare": obj.actionAvailable("prepare") ? {
					name:"Prepare",
					icon:"prepare",
					callback: function(){
						obj.action_prepare();
					}
				} : null,
				"destroy": obj.actionAvailable("destroy") ? {
					name:"Destroy",
					icon:"destroy",
					callback: function(){
						obj.action_destroy();
					}
				} : null,
				"sep2": "---",
				"console": obj.consoleAvailable() ? {
					name:"Console",
					icon:"console",
					items: {
						"console_info": {
							name:"VNC Information",
							icon:"info",
							callback: function(){
								obj.showVNCinfo();
							}
						},
						"console_link": {
							name:"vnc:// link",
							icon:"console",
							callback: function(){
								obj.openVNCurl();
							}
						},
						"console_novnc": {
							name:"NoVNC (HTML5+JS)",
							icon:"novnc",
							callback: function(){
								obj.openConsoleNoVNC();
							}
						},
						"console_java": {
							name: "Java applet",
							icon: "java-applet",
							callback: function(){
								obj.openConsole();
							}
						}, 
					}
				} : null,
				"usage": {
					name:"Usage",
					icon:"usage",
					callback: function(){
						obj.showUsage();
					}
				},
				"download_image": obj.actionAvailable("download_grant") ? {
					name:"Download image",
					icon:"drive",
					callback: function(){
						obj.downloadImage();
					}
				} : null,
				"upload_image": obj.actionAvailable("upload_grant") ? {
					name:"Upload image",
					icon:"drive",
					callback: function(){
						obj.uploadImage();
					}
				} : null,
				"sep3": "---",
				"configure": {
					name:'Configure',
					icon:'configure',
					callback:function(){
						obj.showConfigWindow();
					}
				},
				"debug": obj.editor.options.debug_mode ? {
					name:'Debug',
					icon:'debug',
					callback: function(){
						obj.showDebugInfo();
					}
				} : null,
				"sep4": "---",
				"remove": obj.isRemovable() ? {
					name:'Delete',
					icon:'remove',
					callback: function(){
						obj.remove(null, true);
					}
				} : null
			}
		};
		for (var name in menu.items) {
			if (! menu.items[name]) delete menu.items[name]; 
		}
		return menu;
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
		this.enableClick(this.circle);
		$(this.circle.node).attr("class", "tomato element selectable");
		this.enableClick(this.innerText);
	},
	paintRemove: function(){
		this.circle.remove();
		this.innerText.remove();
		this.text.remove();
	},
	paintUpdate: function() {
		var pos = this.getAbsPos();
		this.circle.attr({cx: pos.x, cy:pos.y});
		this.innerText.attr({x: pos.x, y:pos.y});
		this.text.attr({x: pos.x, y: pos.y+22});
		this.enableDragging(this.circle);
		this.circle.node.obj = this;
	}
});

var IconElement = Element.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconUrl = "img/" + this.data.type + "32.png";
		this.iconSize = {x: 32, y:32};
		this.busy = false;
	},
	isMovable: function() {
		return this._super() && !this.busy;
	},
	setBusy: function(busy) {
		this._super(busy);
		this.updateStateIcon();
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
	getRectObj: function() {
		return this.rect[0];
	},
	paint: function() {
		var pos = this.canvas.absPos(this.getPos());
		this.icon = this.canvas.image(this.iconUrl, pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2, this.iconSize.x, this.iconSize.y);
		this.text = this.canvas.text(pos.x, pos.y+this.iconSize.y/2+5, this.data.attrs.name);
		this.stateIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2-10, pos.y+this.iconSize.y/2-10, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		this.updateStateIcon();
		//hide icon below rect to disable special image actions on some browsers
		this.rect = this.canvas.rect(pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2-5, this.iconSize.x, this.iconSize.y + 10).attr({opacity: 0.0, fill:"#FFFFFF"});
		this.enableDragging(this.rect);
		this.enableClick(this.rect);
		$(this.rect.node).attr("class", "tomato element selectable");
		this.rect.node.obj = this;
		this.rect.conditionalClass("connectable", this.isConnectable());
		this.rect.conditionalClass("removable", this.isRemovable());
	},
	paintRemove: function(){
		this.icon.remove();
		this.text.remove();
		this.stateIcon.remove();
		this.rect.remove();
	},
	paintUpdate: function() {
		var pos = this.getAbsPos();
		this.icon.attr({x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2});
		this.stateIcon.attr({x: pos.x+this.iconSize.x/2-10, y: pos.y+this.iconSize.y/2-10});
		this.rect.attr({x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2+5});
		this.text.attr({x: pos.x, y: pos.y+this.iconSize.y/2+5});
		this.updateStateIcon();
		this.rect.conditionalClass("connectable", this.isConnectable());
		this.rect.conditionalClass("removable", this.isRemovable());
	}
});

var VPNElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconUrl = "img/" + this.data.attrs.mode + "32.png";
		this.iconSize = {x: 32, y:16};
	},
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	getConnectTarget: function(callback) {
		return this.topology.createElement({type: "tinc_endpoint", parent: this.data.id}, callback);
	}
});

var ExternalNetworkElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconUrl = "img/" + this.data.attrs.kind + "32.png";
		this.iconSize = {x: 32, y:32};
	},
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	isRemovable: function() {
		return this._super() && !this.busy;
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

var VMElement = IconElement.extend({
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	configWindowSettings: function() {
		var config = this._super();
		config.order = ["name", "site", "profile", "template"];
		config.special.template = new ChoiceElement({
			label: "Template",
			name: "template",
			choices: createMap(this.editor.templates.getAll(this.data.type), "name", "label"),
			value: this.data.attrs.template || this.data.cap_attrs.template["default"],
			disabled: !this.data.cap_attrs.template.enabled
		});
		config.special.site = new ChoiceElement({
			label: "Site",
			name: "site",
			choices: createMap(this.editor.sites, "name", function(site) {
				return (site.description || site.name) + (site.location ? (", " + site.location) : "");
			}, {"": "Any site"}),
			value: this.data.attrs.site || this.data.cap_attrs.site["default"],
			disabled: !this.data.cap_attrs.site.enabled
		});
		config.special.profile = new ChoiceElement({
			label: "Profile",
			name: "profile",
			choices: createMap(this.editor.profiles.getAll(this.data.type), "name", "label"),
			value: this.data.attrs.profile || this.data.cap_attrs.profile["default"],
			disabled: !this.data.cap_attrs.profile.enabled
		});
		return config;
	},
	getConnectTarget: function(callback) {
		return this.topology.createElement({type: this.data.type + "_interface", parent: this.data.id}, callback);
	}
});

var ChildElement = Element.extend({
	getHandlePos: function() {
		var ppos = this.parent.getAbsPos();
		var cpos = this.connection ? this.connection.getCenter() : {x:0, y:0};
		var xd = cpos.x - ppos.x;
		var yd = cpos.y - ppos.y;
		var magSquared = (xd * xd + yd * yd);
		var mag = 14.0 / Math.sqrt(magSquared);
		return {x: ppos.x + (xd * mag), y: ppos.y + (yd * mag)};
	},
	getAbsPos: function() {
		return this.parent.getAbsPos();
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	paint: function() {
		var pos = this.getHandlePos();
		this.circle = this.canvas.circle(pos.x, pos.y, 7).attr({fill: "#CDCDB3"});
		$(this.circle.node).attr("class", "tomato element");
		this.circle.node.obj = this;
		this.enableClick(this.circle);
	},
	paintRemove: function(){
		this.circle.remove();
	},
	paintUpdate: function() {
		var pos = this.getHandlePos();
		this.circle.attr({cx: pos.x, cy: pos.y});
	}
});

var VMInterfaceElement = ChildElement.extend({
	
});

var SwitchPortElement = ChildElement.extend({
	configWindowSettings: function() {
		var config = this._super();
		config.ignore = ["peers"];
		return config;
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
		this.type = options.tech;
		this.subtype = options.subtype;
		this.name = options.name;
		this.label = options.label || options.name;
	},
	menuButton: function(options) {
		return Menu.button({
			name: options.name || (this.type + "-" + this.name),
			label: options.label || this.label || (this.type + "-" + this.name),
			icon: "img/"+this.type+((this.subtype&&!options.small)?("_"+this.subtype):"")+(options.small?16:32)+".png",
			toggle: true,
			toggleGroup: options.toggleGroup,
			small: options.small,
			func: options.func
		});
	}
});

var TemplateStore = Class.extend({
	init: function(data) {
		data.sort(function(t1, t2){
			var t = t1.attrs.preference - t2.attrs.preference;
			if (t) return t;
			if (t1.attrs.name < t2.attrs.name) return -1;
			if (t2.attrs.name < t1.attrs.name) return 1;
			return 0;
		});
		this.types = {};
		for (var i=0; i<data.length; i++)
		 if (data[i].type == "template")
		  this.add(new Template(data[i].attrs));
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
	},
	get: function(type, name) {
		if (! this.types[type]) return null;
		return this.types[type][name];
	}
});

var Profile = Class.extend({
	init: function(options) {
		this.type = options.tech;
		this.name = options.name;
		this.label = options.label || options.name;
		this.restricted = options.restricted;
	}
});

var ProfileStore = Class.extend({
	init: function(data) {
		data.sort(function(t1, t2){
			var t = t1.attrs.preference - t2.attrs.preference;
			if (t) return t;
			if (t1.attrs.name < t2.attrs.name) return -1;
			if (t2.attrs.name < t1.attrs.name) return 1;
			return 0;
		});
		this.types = {};
		for (var i=0; i<data.length; i++)
		 if (data[i].type == "profile")
		  this.add(new Profile(data[i].attrs));
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
	},
	get: function(type, name) {
		if (! this.types[type]) return null;
		return this.types[type][name];
	}
});

var Mode = {
	select: "select",
	connect: "connect",
	connectOnce: "connect_once",
	remove: "remove",
	position: "position"
}

var Editor = Class.extend({
	init: function(options) {
		this.options = options;
		this.options.grid_size = this.options.grid_size || 25;
		this.options.frame_size = this.options.frame_size || this.options.grid_size;
		this.menu = new Menu(this.options.menu_container);
		this.topology = new Topology(this);
		this.workspace = new Workspace(this.options.workspace_container, this);
		this.sites = this.options.sites;
		this.profiles = new ProfileStore(this.options.resources);
		this.templates = new TemplateStore(this.options.resources);
		this.buildMenu();
		this.topology.load(options.topology);
		this.setMode(Mode.select);
	},
	setOption: function(name, value) {
		this.options[name] = value;
		this.optionCheckboxes[name].setChecked(value);
		this.onOptionChanged(name);
	},
	onOptionChanged: function(name) {
		this.topology.onOptionChanged(name);
		this.workspace.onOptionChanged(name);
	},
	optionMenuItem: function(options) {
		var t = this;
		return Menu.checkbox({
			name: options.name, label: options.label, tooltip: options.tooltip,
			func: function(value){
				t.options[options.name]=value != null;
			  t.onOptionChanged(options.name);
			},
			checked: this.options[options.name]
		});
	},
	onElementConnectTo: function(el) {
		this.setMode(Mode.connectOnce);
		this.connectElement = el;
	},
	onElementSelected: function(el) {
		switch (this.mode) {
			case Mode.connectOnce:
				if (! el.isConnectable()) return;
				this.topology.createConnection(el, this.connectElement);
				this.setMode(Mode.select);
				break;
			case Mode.connect:
				if (! el.isConnectable()) return;
				if (this.connectElement) {
					this.topology.createConnection(el, this.connectElement);
					this.connectElement = null;
				} else this.connectElement = el;
				break;
			case Mode.remove:
				if (! el.isRemovable()) return;
				el.remove();
				break;
			default:
				break;
		}
	},
	onConnectionSelected: function(con) {
		switch (this.mode) {
			case Mode.remove:
				con.remove();
				break;
			default:
				break;
		}
	},
	setMode: function(mode) {
		this.mode = mode;
		this.workspace.onModeChanged(mode);
		if (mode != Mode.position) this.positionElement = null;
		if (mode != Mode.connect && mode != Mode.connectOnce) this.connectElement = null;
	},
	setPositionElement: function(el) {
		this.positionElement = el;
		this.setMode(Mode.position);
		
	},
	createPositionElementFunc: function(el) {
		var t = this;
		return function() {
			t.setPositionElement(el);
		}
	},
	createModeFunc: function(mode) {
		var t = this;
		return function() {
			t.setMode(mode);
		}
	},
	createElementFunc: function(el) {
		var t = this;
		return function(pos) {
			var data = copy(el, true);
			data.attrs._pos = pos;
			t.topology.createElement(data);
			t.selectBtn.click();
		}
	},
	createTemplateFunc: function(tmpl) {
		return this.createElementFunc({type: tmpl.type, attrs: {template: tmpl.name}});
	},
	buildMenu: function() {
		var t = this;
	
		var toggleGroup = new ToggleGroup();
	
		var tab = this.menu.addTab("Home");

		var group = tab.addGroup("Modes");
		this.selectBtn = Menu.button({
			label: "Select & Move",
			icon: "img/select32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			checked: true,
			func: this.createModeFunc(Mode.select)
		});
		group.addElement(this.selectBtn);
		group.addStackedElements([
			Menu.button({
				label: "Connect",
				icon: "img/connect16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createModeFunc(Mode.connect)
			}),
			Menu.button({
				label: "Delete",
				name: "mode-remove",
				icon: "img/eraser16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createModeFunc(Mode.remove)
			})
		]);

		var group = tab.addGroup("Topology control");
		group.addElement(Menu.button({
			label: "Start",
			icon: "img/start32.png",
			toggle: false,
			small: false,
			func: function() {
				t.topology.action_start();
			}
		}));
		group.addElement(Menu.button({
			label: "Stop",
			icon: "img/stop32.png",
			toggle: false,
			small: false,
			func: function() {
				t.topology.action_stop();
			}
		}));
		group.addStackedElements([
			Menu.button({
				label: "Prepare",
				icon: "img/prepare16.png",
				toggle: false,
				small: true,
				func: function() {
					t.topology.action_prepare();
				}
			}),
			Menu.button({
				label: "Destroy",
				icon: "img/destroy16.png",
				toggle: false,
				small: true,
				func: function() {
					t.topology.action_destroy();
				}
			}),
			Menu.button({
				label: "Delete",
				name: "topology-remove",
				icon: "img/eraser16.png",
				toggle: false,
				small: true,
				func: function() {
					t.topology.remove();
				}
			})
		]);
		
		var group = tab.addGroup("Common elements");
		var tmpl = t.templates.get("openvz", "debian-6.0_x86");
		if (tmpl)
		 group.addElement(tmpl.menuButton({
			label: "Debian 6.0 (OpenVZ)",
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createTemplateFunc(tmpl))
		}));
		var tmpl = t.templates.get("kvmqm", "debian-6.0_x86");
		if (tmpl)
		 group.addElement(tmpl.menuButton({
			label: "Debian 6.0 (KVM)",
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createTemplateFunc(tmpl))
		}));
		group.addElement(Menu.button({
			label: "Switch",
			name: "vpn-switch",
			icon: "img/switch32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "tinc_vpn",
				attrs: {mode: "switch"}
			}))
		}));
		group.addElement(Menu.button({
			label: "Internet",
			name: "net-internet",
			icon: "img/internet32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "external_network",
				attrs: {kind: "internet"}
			}))
		}));


		var tab = this.menu.addTab("Devices");

		var group = tab.addGroup("Linux (OpenVZ)");
		var tmpls = t.templates.getAll("openvz");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 btns.push(tmpls[i].menuButton({
			toggleGroup: toggleGroup,
			small: true,
			func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Linux (KVM)");
		var tmpls = t.templates.getAll("kvmqm", "linux");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype == "linux")
		  btns.push(tmpls[i].menuButton({
			toggleGroup: toggleGroup,
			small: true,
			func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Other (KVM)");
		var tmpls = t.templates.getAll("kvmqm");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype != "linux")
		  btns.push(tmpls[i].menuButton({
		  	toggleGroup: toggleGroup,
			small: true,
		  	func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Scripts (Repy)");
		var tmpls = t.templates.getAll("repy");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype == "device")
		  btns.push(tmpls[i].menuButton({
		  	toggleGroup: toggleGroup,
		  	small: true,
		  	func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Upload own images");
		group.addStackedElements([
			Menu.button({
				label: "KVM image",
				name: "kvm-custom",
				icon: "img/kvm16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: function() {
					alert("Not implemented yet.");
				}
			}),
			Menu.button({
				label: "OpenVZ image",
				name: "openvz-custom",
				icon: "img/openvz16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: function() {
					alert("Not implemented yet.");
				}
			}),
			Menu.button({
				label: "Repy script",
				name: "repy-custom",
				icon: "img/repy16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: function() {
					alert("Not implemented yet.");
				}
			})
		]);


		var tab = this.menu.addTab("Network");

		var group = tab.addGroup("VPN Elements");
		group.addElement(Menu.button({
			label: "Switch",
			name: "vpn-switch",
			icon: "img/switch32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "tinc_vpn",
				attrs: {mode: "switch"}
			}))
		}));
		group.addElement(Menu.button({
			label: "Hub",
			name: "vpn-hub",
			icon: "img/hub32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "tinc_vpn",
				attrs: {mode: "hub"}
			}))
		}));

		var group = tab.addGroup("Scripts (Repy)");
		group.addElement(Menu.button({
			label: "Custom script",
			name: "repy-custom",
			icon: "img/repy32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: function() {
				alert("Not implemented yet.");
			}
		}));
		var tmpls = t.templates.getAll("repy");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype != "device")
		  btns.push(tmpls[i].menuButton({
		  	toggleGroup: toggleGroup,
		  	small: true,
		  	func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Networks");
		group.addElement(Menu.button({
			label: "Internet",
			name: "net-internet",
			icon: "img/internet32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "external_network",
				attrs: {kind: "internet"}
			}))
		}));
		group.addElement(Menu.button({
			label: "OpenFlow",
			name: "net-openflow",
			icon: "img/openflow32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "external_network",
				attrs: {kind: "openflow"}
			}))
		}));


		var tab = this.menu.addTab("Topology");

		var group = tab.addGroup("");
		group.addElement(Menu.button({
			label: "Notes",
			icon: "img/notes32.png",
			toggle: false,
			small: false,
			func: function(){
				t.topology.notesDialog();
			}
		}));
		group.addStackedElements([
			Menu.button({
				label: "Usage",
				icon: "img/chart_bar.png",
				toggle: false,
				small: true,
				func: function(){
					t.topology.showUsage();
				}
			}),
			Menu.button({
				label: "Rename",
				icon: "img/rename.png",
				toggle: false,
				small: true,
				func: function(){
					t.topology.renameDialog();
				}
			}),
			Menu.button({
				label: "Export",
				icon: "img/export16.png",
				toggle: false,
				small: true,
				func: function() {
					alert("Not implemented yet.");
				}
			})
		]);
		group.addElement(Menu.button({
			label: "Users & Permissions",
			icon: "img/user32.png",
			toggle: false,
			small: false,
			func: function() {
				alert("Not implemented yet.");
			}
		}));


		var tab = this.menu.addTab("Options");

		var group = tab.addGroup("Editor");
		this.optionCheckboxes = {
			safe_mode: this.optionMenuItem({
				name:"safe_mode",
   				label:"Safe mode",
   				tooltip:"Asks before all destructive actions"
   			}),
   			snap_to_grid: this.optionMenuItem({
   				name:"snap_to_grid",
   				label:"Snap to grid",
   				tooltip:"All elements snap to an invisible "+this.options.grid_size+" pixel grid"
   			}),
   			fixed_pos: this.optionMenuItem({
		        name:"fixed_pos",
		        label:"Fixed positions",
		        tooltip:"Elements can not be moved"
		    }),
		    beginner_mode: this.optionMenuItem({
		        name:"beginner_mode",
		        label:"Beginner mode",
		        tooltip:"Displays help messages for all elements"
		    }),
		    debug_mode: this.optionMenuItem({
		        name:"debug_mode",
		        label:"Debug mode",
		        tooltip:"Displays debug messages"
		    })
		};
		group.addStackedElements([this.optionCheckboxes.safe_mode, this.optionCheckboxes.snap_to_grid, this.optionCheckboxes.fixed_pos, this.optionCheckboxes.beginner_mode, this.optionCheckboxes.debug_mode]);

		this.menu.paint();
	}
});
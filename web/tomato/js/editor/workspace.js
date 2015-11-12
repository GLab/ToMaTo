var Workspace = Class.extend({
	init: function(container, editor) {
		this.container = container;
		this.editor = editor;
		container.addClass("ui-widget-content").addClass("ui-corner-all")
		container.addClass("tomato").addClass("workspace");
		container[0].obj = editor.topology;
		this.container.click(function(){});
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
    	
    	//tutorial UI
    	this.tutorialWindow = new TutorialWindow({ 
			autoOpen: false, 
			draggable: true,  
			resizable: false, 
			title: ".", 
			modal: false, 
			buttons: {},
			width:500,
			closeOnEscape: false,
			tutorialVisible:this.editor.options.tutorial_show,
			tutorial_state:this.editor.options.tutorial_state,
			hideCloseButton: true,
			editor: this.editor
		});
    	
    	this.permissionsWindow = new PermissionsWindow({
    		autoOpen: false,
    		draggable: true,
    		resizable: false,
    		title: "Permissions",
    		modal: false,
    		width: 500,
    		topology: this.editor.topology,
    		isGlobalOwner: this.editor.options.isGlobalOwner, //todo: set value depending on user permissions
    		ownUserId: this.editor.options.user.id,
    		permissions: this.editor.options.permission_list
    	});
    	
    	var t = this;
    	this.editor.listeners.push(function(obj){
    		t.tutorialWindow.triggerProgress(obj);
    	});
    	
    	
		this.connectPath = this.canvas.path("M0 0L0 0").attr({"stroke-dasharray": "- "});
		this.container.click(function(evt){
			t.onClicked(evt);
		});
		this.container.mousemove(function(evt){
			t.onMouseMove(evt);
		});
		this.busyIcon = this.canvas.image("img/loading_big.gif", this.size.x/2, this.size.y/2, 32, 32);
		this.busyIcon.attr({opacity: 0.0});
	},
	
	setBusy: function(busy) {
		this.busyIcon.attr({opacity: busy ? 1.0 : 0.0});
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
    		this.tutorialWindow.updateText();
	},
	onModeChanged: function(mode) {
		for (var name in Mode) this.container.removeClass("mode_" + Mode[name]);
		this.container.addClass("mode_" + mode);
	},
	
	updateTopologyTitle: function() {
		var t = editor.topology;
		var new_name="Topology '"+t.data.name+"'"+(editor.options.show_ids ? " ["+t.id+"]" : "");
		$('#topology_name').text(new_name);
		document.title = new_name+" - G-Lab ToMaTo";
	}
});

var Topology = Class.extend({
	init: function(editor) {
		this.editor = editor;
		this.elements = {};
		this.connections = {};
		this.pendingNames = [];
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
			case "repy_interface":
				elObj = new VMInterfaceElement(this, el, this._getCanvas());
				break;
			case "openvz_interface":
				elObj = new VMConfigurableInterfaceElement(this, el, this._getCanvas());
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
		data.elements.sort(function(a, b){return a.id > b.id ? 1 : (a.id < b.id ? -1 : 0);});
		for (var i=0; i<data.elements.length; i++) this.loadElement(data.elements[i]);
		this.connections = {};
		for (var i=0; i<data.connections.length; i++) this.loadConnection(data.connections[i]);
		
		this.settingOptions = true;
		var opts = ["safe_mode", "snap_to_grid", "fixed_pos", "colorify_segments", "big_editor", "debug_mode", "show_ids", "show_sites_on_elements"];
		for (var i = 0; i < opts.length; i++) {
			if (this.data["_"+opts[i]] != null) this.editor.setOption(opts[i], this.data["_"+opts[i]]);
		}
		this.settingOptions = false;		

		this.onUpdate();
	},
	setBusy: function(busy) {
		this.busy = busy;
	},
	configWindowSettings: function() {
		return {
			order: ["name"],
			ignore: [],
			unknown: true,
			special: {}
		}
	},
	showConfigWindow: function(callback) {
		var t = this;
		var settings = this.configWindowSettings();

		this.configWindow = new AttributeWindow({
			title: "Attributes",
			width: 600,
			height: 600,
			maxHeight:800,
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) {
						if (values[name] === t.data[name]) delete values[name];
						// Treat "" like null
						if (values[name] === "" && t.data[name] === null) delete values[name];
					}
					t.modify(values);
					t.configWindow.remove();
					t.configWindow = null;

					if(callback != null) {
						callback(t);
					}
				},
				Cancel: function() {
					t.configWindow.remove();
					t.configWindow = null;
				}
			}
		});
        this.configWindow.add(new TextElement({
				label: "Name",
				name: "name",
				value: this.data.name,
				disabled: false
		}));
		this.configWindow.add(new ChoiceElement({
			label: "Site",
			name: "site",
			choices: createMap(this.editor.sites, "name", function(site) {
				return (site.label || site.name) + (site.location ? (", " + site.location) : "");
			}, {"": "Any site"}),
			value: this.data.site,
			disabled: false
		}));
		this.configWindow.show();
	},
	modify: function(attrs) {
		this.setBusy(true);
		this.editor.triggerEvent({component: "topology", object: this, operation: "modify", phase: "begin", attrs: attrs});
		var t = this;
		ajax({
			url: 'topology/'+this.id+'/modify',
		 	data: attrs,
		 	successFn: function(result) {
				t.editor.triggerEvent({component: "topology", object: this, operation: "modify", phase: "end", attrs: attrs});
		 	},
		 	errorFn: function(error) {
		 		new errorWindow({error:error});
				t.editor.triggerEvent({component: "topology", object: this, operation: "modify", phase: "error", attrs: attrs});
		 	}
		});
		for (var name in attrs) {
		    this.data[name] = attrs[name];
    		if (name == "name") editor.workspace.updateTopologyTitle();
		}
	},
	action: function(action, options) {
		var options = options || {};
		var params = options.params || {};
		this.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "begin", action: action, params: params});
		var t = this;
		ajax({
			url: 'topology/'+this.id+'/action',
		 	data: {action: action, params: params},
		 	successFn: function(result) {
		 		var data = result[1];
		 		t.data = data;
				t.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "end", action: action, params: params});
		 	},
		 	errorFn: function(error) {
		 		new errorWindow({error:error});
				t.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "error", action: action, params: params});
		 	}
		});
	},
	modify_value: function(name, value) {
		var attrs = {};
		attrs[name] = value;
		this.modify(attrs);
		if (name == "name") editor.workspace.updateTopologyTitle();
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
		for (var id in this.elements) names.push(this.elements[id].data.name);
		var base;
		switch (data.type) {
			case "external_network":
				base = data.kind || "internet";
				break;
			case "external_network_endpoint":
				base = (data.kind || "internet") + "_endpoint";
				break;		
			case "tinc_vpn":
				base = data.mode || "switch";
				break;
			case "tinc_endpoint":
				base = "tinc";
				break;		
			default:
				if (data && data.template) {
					base = editor.templates.get(data.type, data.template).label;
				} else {
					base = data.type;
				}
		}
		base = base+" #";
		var num = 1;
		while (names.indexOf(base+num) != -1 || this.pendingNames.indexOf(base+num) != -1) num++;
		return base+num;
	},
	createElement: function(data, callback) {
		if (!data.parent) data.name = data.name || this.nextElementName(data);
		var obj = this.loadElement(data);
		this.editor.triggerEvent({component: "element", object: obj, operation: "create", phase: "begin", attrs: data});
		obj.setBusy(true);
		this.pendingNames.push(data.name);
		var t = this;
		ajax({
			url: "topology/" + this.id + "/create_element",
			data: data,
			successFn: function(data) {
				t.pendingNames.remove(data.name);
				t.elements[data.id] = obj;
				obj.setBusy(false);
				obj.updateData(data);
				if (callback) callback(obj);
				t.editor.triggerEvent({component: "element", object: obj, operation: "create", phase: "end", attrs: data});
				t.onUpdate();
			},
			errorFn: function(error) {
		 		new errorWindow({error:error});
				obj.paintRemove();
				t.pendingNames.remove(data.name);
				t.editor.triggerEvent({component: "element", object: obj, operation: "create", phase: "error", attrs: data});
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
			t.editor.triggerEvent({component: "connection", object: obj, operation: "create", phase: "begin", attrs: data});
			data.elements = [el1.id, el2.id];
			ajax({
				url: "connection/create",
				data: data,
				successFn: function(data) {
					t.connections[data.id] = obj;
					obj.updateData(data);
					t.editor.triggerEvent({component: "connection", object: obj, operation: "create", phase: "end", attrs: data});
					t.onUpdate();
					el1.onConnected();
					el2.onConnected();
				},
				errorFn: function(error) {
			 		new errorWindow({error:error});
					obj.paintRemove();
					t.editor.triggerEvent({component: "connection", object: obj, operation: "create", phase: "error", attrs: data});
				}
			});
		};
		el1 = el1.getConnectTarget(callback);
		el2 = el2.getConnectTarget(callback);
		data = data || {};
		obj = this.loadConnection(copy(data, true), [el1, el2]);
		return obj;
	},
	onOptionChanged: function(name) {
		if (this.settingOptions) return;
		this.modify_value("_" + name, this.editor.options[name]);
		this.onUpdate();
	},
	action_delegate: function(action, options) {
		var options = options || {};
		if ((action=="destroy"||action=="stop") && !options.noask && this.editor.options.safe_mode && ! confirm("Do you want to " + action + " this topology?")) return;
		this.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "begin", action: action});
		var ids = 0;
		var t = this;
		var cb = function() {
			ids--;
			if (ids <= 0 && options.callback) options.callback();
			t.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "end", action: action});
		}
		for (var id in options.elements||this.elements) {
			var el = this.elements[id];
			if (el.busy) continue;
			if (el.parent) continue;
			if (el.actionEnabled(action)) {
				ids++;
				el.action(action, {
					noask: true,
					callback: cb,
					noUpdate: options.noUpdate
				});
			}
		}
		if (ids <= 0 && options.callback) options.callback();
		this.onUpdate();
	},
	_twoStepPrepare: function(callback) {
		var vmids = {};
		var rest = {};
		for (var id in this.elements) {
			var element = this.elements[id];
			switch (element.data.type) {
				case 'openvz':
				case 'kvmqm':
				case 'repy':
					vmids[id] = element;
					break;
				default:
					rest[id] = element;
			}
		}
		var t = this;
		this.action_delegate("prepare", {
			elements: vmids,
			callback: function() {
				t.action_delegate("prepare", {
					elements: rest,
					callback: callback
				})
			}
		})
	},
	action_start: function() {
		var t = this;
		this._twoStepPrepare(function(){
			t.action_delegate("start", {});
		});
	},
	action_stop: function() {
		this.action_delegate("stop");
	},
	action_prepare: function() {
		this._twoStepPrepare();
	},
	action_destroy: function() {
		var t = this;
		if (this.editor.options.safe_mode && !confirm("Are you sure you want to completely destroy this topology?")) return;
		this.action_delegate("stop", {
			callback: function(){
				t.action_delegate("destroy", {noask: true});
			}, noask: true
		});
	},
	remove: function() {
		if (this.editor.options.safe_mode && !confirm("Are you sure you want to completely remove this topology?")) return;
		var t = this;
		var removeTopology = function() {
			t.editor.triggerEvent({component: "topology", object: t, operation: "remove", phase: "begin"});
			ajax({
				url: "topology/"+t.id+"/remove",
				successFn: function() {
					t.editor.triggerEvent({component: "topology", object: t, operation: "remove", phase: "end"});
					window.location = "/topology";
				}
			});			
		}
		this.action_delegate("stop", {noask: true, noUpdate: true, callback: function() {
			t.action_delegate("destroy", {noask: true, noUpdate: true, callback: function() {
				if (t.elementCount()) {
					for (var elId in t.elements) {
						if (t.elements[elId].parent) continue;
						t.elements[elId].remove(function(){
							if (! t.elementCount()) removeTopology();		
						}, false);
					}
				} else removeTopology();				
			}});			
		}});
	},
	showDebugInfo: function() {
		var t = this;
		ajax({
			url: 'topology/'+this.id+'/info',
		 	data: {},
		 	successFn: function(result) {
		 		var win = new Window({
		 			title: "Debug info",
		 			width: 500,
		 			buttons: {
		 				Close: function() {
		 					win.hide();
		 				}
					} 
		 		});
		 		div = $('<div></div>');
		 		new PrettyJSON.view.Node({
		 			data: result,
		 			el: div
		 		});
		 		win.add(div);
		 		win.show();
		 	},
		 	errorFn: function(error) {
		 		new errorWindow({error:error});
		 	}
		});
	},
	showUsage: function() {
  		window.open('/topology/'+this.id+'/usage', '_blank', 'innerHeight=450,innerWidth=650,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
		this.editor.triggerEvent({component: "topology", object: this, operation: "usage-dialog"});
	},
	notesDialog: function() {
		var dialog = $("<div/>");
		var ta = $('<textarea cols=60 rows=20 class="notes"></textarea>');
		ta.text(this.data._notes || "");
		dialog.append(ta);
		var openWithEditor_html = $('<input type="checkbox" name="openWithEditor">Open Window with Editor</input>');
		var openWithEditor = openWithEditor_html[0];
		if (this.data._notes_autodisplay) {
			openWithEditor.checked = true;
		}
		dialog.append($('<br/>'))
		dialog.append(openWithEditor_html);
		var t = this;
		dialog.dialog({
			autoOpen: true,
			draggable: true,
			resizable: true,
			height: "auto",
			width: 550,
			title: "Notes for Topology",
			show: "slide",
			hide: "slide",
			modal: true,
			buttons: {
				Save: function() {
		        	dialog.dialog("close");
			      	t.modify_value("_notes", ta.val());
			      	t.modify_value("_notes_autodisplay", openWithEditor.checked)
			    },
		        Close: function() {
		        	dialog.dialog("close");
		        }				
			}
		});
	},
	renameDialog: function() {
		var t = this;
		windowOptions = {
			title: "Rename Topology",
			width: 550,
			inputname: "newname",
			inputlabel: "New Name:",
			inputvalue: t.data.name,
			onChangeFct: function () {
				if(this.value == '') { 
					$('#rename_topology_window_save').button('disable');
				} else { 
					$('#rename_topology_window_save').button('enable');
				}
			},
			buttons: [
				{ 
					text: "Save",
					id: "rename_topology_window_save",
					click: function() {
						t.rename.hide();
						if(t.rename.element.getValue() != '') {
							t.modify_value("name", t.rename.element.getValue());
						}
						t.rename = null;
					}
				},
				{
					text: "Cancel",
					click: function() {
						t.rename.hide();
						t.rename = null;
					}
				}
			],
		};
		this.rename = new InputWindow(windowOptions);
		this.rename.show();
	},
	renewDialog: function() {
		var t = this;
		var dialog, timeout;
		dialog = new AttributeWindow({
			title: "Topology Timeout",
			width: 500,
			height: 400,
			buttons: [
						{ 
							text: "Save",
							click: function() {
								t.action("renew", {params:{
									"timeout": parseFloat(timeout.getValue())
								}});
								dialog.remove();
							}
						},
						{
							text: "Close",
							click: function() {
								dialog.remove();
							}
						}
					],
		});
		var choices = {};
		var timeout_settings = t.editor.options.timeout_settings;
		for (var i = 0; i < timeout_settings.options.length; i++) choices[timeout_settings.options[i]] = formatDuration(timeout_settings.options[i]);
		var timeout_val = t.data.timeout - new Date().getTime()/1000.0;
		var text = timeout_val > 0 ? ("Your topology will time out in " + formatDuration(timeout_val)) : "Your topology has timed out. You must renew it to use it.";
		if (timeout_val < timeout_settings.warning) text = '<b style="color:red">' + text + '</b>';
		dialog.addText("<center>"  + text + "</center>");
		timeout = dialog.add(new ChoiceElement({
			name: "timeout",
			label: "New timeout",
			choices: choices,
			value: timeout_settings["default"],
			help_text: "After this time, your topology will automatically be stopped. Timeouts can be extended arbitrarily."
		}));
		dialog.show();		
	},
	initialDialog: function() {
		var t = this;
		var dialog, name, description, timeout;
		dialog = new AttributeWindow({
			title: "New Topology",
			width: 500,
			closable: false,
			buttons: [
						{ 
							text: "Save",
							disabled: true,
							id: "new_topology_window_save",
							click: function() {
								if (name.getValue() && timeout.getValue()) {
									t.modify({
										"name": name.getValue(),
										"_notes": description.getValue(),
										"_initialized": true
									});
									editor.workspace.updateTopologyTitle();
									t.action("renew", {params:{
										"timeout": parseFloat(timeout.getValue())
									}});
									dialog.remove();
									dialog = null;
								}
							}
						}
					],
		});
		name = dialog.add(new TextElement({
			name: "name",
			label: "Name",
			help_text: "The name for your topology",
			onChangeFct:  function () {
				if(this.value == '') { 
					$('#new_topology_window_save').button('disable');
				} else { 
					$('#new_topology_window_save').button('enable');
				}
			}
		}));
		var choices = {};
		var timeout_settings = t.editor.options.timeout_settings;
		for (var i = 0; i < timeout_settings.options.length; i++) choices[timeout_settings.options[i]] = formatDuration(timeout_settings.options[i]); 
		timeout = dialog.add(new ChoiceElement({
			name: "timeout",
			label: "Timeout",
			choices: choices,
			value: timeout_settings["default"],
			help_text: "After this time, your topology will automatically be stopped. Timeouts can be extended arbitrarily."
		}));
		description = dialog.add(new TextAreaElement({
			name: "description",
			label: "Description",
			help_text: "Description of the experiment. (Optional)",
			value: t.data._notes
		}));
		dialog.show();
	},
	name: function() {
		return this.data.name;
	},
	onUpdate: function() {
		this.checkNetworkLoops();
		var segments = this.getNetworkSegments();
		this.colorNetworkSegments(segments);
		this.editor.triggerEvent({component: "topology", object: this, operation: "update"});
	},
	getNetworkSegments: function() {
		var segments = [];
		for (var con in this.connections) {
			var found = false;
			for (var i=0; i<segments.length; i++)
			 if (segments[i].connections.indexOf(this.connections[con].id) >= 0)
			  found = true;
			if (found) continue;
			segments.push(this.connections[con].calculateSegment());
		}
		return segments;
	},
	checkNetworkLoops: function() {
		var maxCount = 1;
		this.loop_last_warn = this.loop_last_warn || 1;
		for (var i in  this.elements) {
			var el = this.elements[i];
			if (el.data.type != "external_network_endpoint") continue;
			if (! el.connection) continue; //can that happen?
			var segment = el.connection.calculateSegment([el.id], []);
			var count = 0;
			for (var j=0; j<segment.elements.length; j++) {
				var e = this.elements[segment.elements[j]];
				if (! e) continue; //brand new element
				if (e.data.type == "external_network_endpoint") count++;
			}
			maxCount = Math.max(maxCount, count);
		}
		if (maxCount > this.loop_last_warn) showError("Network segments must not contain multiple external network exits! This could lead to loops in the network and result in a total network crash.");
		this.loop_last_warn = maxCount;
	},
	colorNetworkSegments: function(segments) {
		var skips = 0;
		for (var i=0; i<segments.length; i++) {
			var cons = segments[i].connections;
			var num = (this.editor.options.colorify_segments && cons.length > 1) ? (i-skips) : NaN;
			if (cons.length == 1) skips++;
			for (var j=0; j<cons.length; j++) {
				var con = this.connections[cons[j]];
				if (! con) continue; //brand new connection
				con.setSegment(num);
			}
		}
	}
});


['right', 'longclick'].forEach(function(trigger) {
	$.contextMenu({
		selector: 'rect,circle', //filtering on classes of SVG objects does not work
		trigger: trigger,
		build: function(trigger, e) {
			return createComponentMenu(trigger[0].obj);
		}
	});	
});

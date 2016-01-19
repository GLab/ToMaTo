
var Component = Class.extend({
	init: function(topology, data, canvas) {
		this.topology = topology;
		this.editor = topology.editor;
		this.setData(data);
		this.canvas = canvas;
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
	actionEnabled: function(action) {
		return (action in this.caps.actions) && (! this.caps.actions[action].allowed_states || (this.caps.actions[action].allowed_states.indexOf(this.data.state) >= 0));
	},
	attrEnabled: function(attr) {
	    if (attr[0] == "_") return true;
	    if (!(attr in this.caps.attributes)) return false;
	    var cap = this.caps.attributes[attr];
	    if (cap.read_only) return false;
	    return (!cap.states_writable || cap.states_writable.indexOf(this.data.state) >= 0);
	},
	setData: function(data) {
		this.data = data;
		this.id = data.id;
		this.caps = this.editor.capabilities[this.component_type][this.data.type];
	},
	updateData: function(data) {
		if (data) this.setData(data);
		this.topology.onUpdate();
		this.paintUpdate();
	},
	triggerEvent: function(event) {
		event.component = this.component_type;
		event.object = this;
		this.editor.triggerEvent(event);
	},
	showDebugInfo: function() {
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/info',
		 	data: {},
		 	successFn: function(result) {
		 		var win = new Window({
		 			title: "Debug info",
		 			width: 500,
		 			buttons: {
		 				Close: function() {
		 					win.hide();
		 					win.remove();
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
  		window.open('../'+this.component_type+'/'+this.id+'/usage', '_blank', 'innerHeight=450,innerWidth=650,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
		this.triggerEvent({operation: "usage-dialog"});
	},
	configWindowSettings: function() {
		return {
			order: ["name"],
			ignore: ["id", "parent", "connection", "host_info", "host", "state", "debug", "type", "children", "topology","info_last_sync","info_next_sync"],
			unknown: true,
			special: {}
		}
	},
	showConfigWindow: function(showTemplate,callback) {
		
		if(showTemplate == null) showTemplate=true;
		
		var absPos = this.getAbsPos();
		var wsPos = this.editor.workspace.container.position();
		var t = this;
		var settings = this.configWindowSettings();
		
		var helpTarget = undefined;
		if ($.inArray(this.data.type,settings.supported_configwindow_help_pages)) {
			helpTarget = help_baseUrl+"/editor:configwindow_"+this.data.type;
		}
		
		console.log('opening config window for type '+this.data.type);
		
		this.configWindow = new AttributeWindow({
			title: "Attributes",
			width: 600,
			helpTarget:helpTarget,
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) {
						if (values[name] === t.data[name]) delete values[name];
						// Tread "" like null
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
		for (var i=0; i<settings.order.length; i++) {
			var name = settings.order[i];
			if(showTemplate || !(name == 'template')) {
				if (settings.special[name]) this.configWindow.add(settings.special[name]);
				else if (this.caps.attributes[name]) {
				    var info = this.caps.attributes[name];
				    info.name = name;
				    this.configWindow.autoAdd(info, this.data[name], this.attrEnabled(name));
				}
			}
		}
		if (settings.unknown) {
			for (var name in this.caps.attributes) {
				if (settings.order.indexOf(name) >= 0) continue; //do not repeat ordered fields
				if (settings.ignore.indexOf(name) >= 0) continue;
				if (settings.special[name]) this.configWindow.add(settings.special[name]);
				else if (this.caps.attributes[name]) {
				    var info = this.caps.attributes[name];
				    info.name = name;
				    this.configWindow.autoAdd(info, this.data[name], this.attrEnabled(name));
				}
			}
		}
		this.configWindow.show();
		this.triggerEvent({operation: "attribute-dialog"});
	},
	updateSynchronous: function(fetch, callback, hide_errors) {
		this._update(fetch, callback, hide_errors, true);
	},
	update: function(fetch, callback, hide_errors) {
		this._update(fetch, callback, hide_errors, false);
	},
	_update: function(fetch, callback, hide_errors, synchronous) {
		var t = this;
		this.triggerEvent({operation: "update", phase: "begin"});
		ajax({
			url: this.component_type+'/'+this.id+'/info',
			data: {fetch: fetch},
		 	successFn: function(result) {
		 		t.updateData(result);
				t.triggerEvent({operation: "update", phase: "end"});
				if (callback) callback();
		 	},
		 	errorFn: function(error) {
		 		if (!hide_errors) new errorWindow({error:error});
				t.triggerEvent({operation: "update", phase: "error"});
		 	},
		 	synchronous: synchronous
		});
	},
	updateDependent: function() {
	},
	modify: function(attrs) {
		this.setBusy(true);
		for (var name in attrs) {
			if (this.attrEnabled(name)) this.data[name] = attrs[name];
			else delete attrs[name];
		}
		this.triggerEvent({operation: "modify", phase: "begin", attrs: attrs});
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/modify',
		 	data: attrs,
		 	successFn: function(result) {
		 		t.updateData(result);
		 		t.setBusy(false);
				t.triggerEvent({operation: "modify", phase: "end", attrs: attrs});
		 	},
		 	errorFn: function(error) {
		 		new errorWindow({error:error});
		 		t.update();
		 		t.setBusy(false);
				t.triggerEvent({operation: "modify", phase: "error", attrs: attrs});
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
		this.triggerEvent({operation: "action", phase: "begin", action: action, params: params});
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/action',
		 	data: {action: action, params: params},
		 	successFn: function(result) {
		 		t.updateData(result[1]);
		 		t.setBusy(false);
		 		if (options.callback) options.callback(t, result[0], result[1]);
				t.triggerEvent({operation: "action", phase: "end", action: action, params: params});
				if (! options.noUpdate) t.updateDependent();
				editor.rextfv_status_updater.add(t, 5000);
		 	},
		 	errorFn: function(error) {
		 		new errorWindow({error:error});
		 		t.update();
		 		t.setBusy(false);
				t.triggerEvent({operation: "action", phase: "error", action: action, params: params});
				editor.rextfv_status_updater.add(t, 5000);
		 	}
		});
	},
	onConnected: function() {
	}
});

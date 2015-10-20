


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
			ignore: ["id", "parent", "connection", "host_info", "host", "state", "debug", "type", "children", "topology"],
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
	update: function(fetch, callback, hide_errors) {
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
		 	}
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
				editor.rextfv_status_updater.add(t, 30);
		 	},
		 	errorFn: function(error) {
		 		new errorWindow({error:error});
		 		t.update();
		 		t.setBusy(false);
				t.triggerEvent({operation: "action", phase: "error", action: action, params: params});
				editor.rextfv_status_updater.add(t, 5);
		 	}
		});
	},
	onConnected: function() {
	}
});



var Connection = Component.extend({
	init: function(topology, data, canvas) {
		this.component_type = "connection";
		data.type = data.type || "bridge";
		this._super(topology, data, canvas);
		this.elements = [];
		this.segment = -1;
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
	isRemovable: function() {
		return this.actionEnabled("(remove)");
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
		var diff = {x: pos1.x - pos2.x, y: pos1.y - pos2.y};
		var length = Math.sqrt(diff.x * diff.x + diff.y * diff.y);
		var norm = {x: diff.x/length, y: diff.y/length};
		pos1 = {x: pos1.x - norm.x * settings.childElementDistance, y: pos1.y - norm.y * settings.childElementDistance};
		pos2 = {x: pos2.x + norm.x * settings.childElementDistance, y: pos2.y + norm.y * settings.childElementDistance};
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
		$(this.handle.node).attr("class", "tomato connection");
		this.handle.node.obj = this;
		var t = this;
		$(this.handle.node).click(function() {
			t.onClicked();
		})
		this.paintUpdate();
		for (var i=0; i<this.elements.length; i++) this.elements[i].paintUpdate();
	},
	paintRemove: function(){
		this.path.remove();
		this.handle.remove();
	},
	setSegment: function(segment){
		this.segment = segment;
		this.paintUpdate();
	},
	paintUpdate: function(){
		var colors = ["#2A4BD7", "#AD2323", "#1D6914", "#814A19", "#8126C0", "#FFEE33", "#FF9233", "#29D0D0", "#9DAFFF", "#81C57A", "#FFCDF3"];
		var color = colors[this.segment % colors.length] || "#505050";
		var attrs = this.data;
		var le = attrs && attrs.emulation && (attrs.delay_to || attrs.jitter_to || attrs.lossratio_to || attrs.duplicate_to || attrs.corrupt_to
				         || attrs.delay_from || attrs.jitter_from || attrs.lossratio_from || attrs.duplicate_from || attrs.corrupt_from);
		var bw = 10000000;
		if (attrs && attrs.emulation) bw = Math.min(attrs.bandwidth_to, attrs.bandwidth_from); 
		this.path.attr({stroke: color});
		this.path.attr({"stroke-width": bw < 10000 ? 1 : ( bw > 10000 ? 4 : 2.5 )});
		this.path.attr({path: this.getPath()});
		var pos = this.getAbsPos();
		this.handle.attr({x: pos.x-5, y: pos.y-5, transform: "R"+this.getAngle()});
		this.handle.conditionalClass("removable", this.isRemovable());
	},
	calculateSegment: function(els, cons) {
		if (! els) els = [];
		if (! cons) cons = [];
		if (cons.indexOf(this.id) >= 0) return {elements: els, connections: cons};
		cons.push(this.id);
		for (var i=0; i < this.elements.length; i++) {
			var res = this.elements[i].calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		return {elements: els, connections: cons};
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
	captureDownloadable: function() {
		return this.actionEnabled("download_grant") && this.data.capturing && this.data.capture_mode == "file";
	},
	downloadCapture: function() {
		this.action("download_grant", {callback: function(con, res) {
			var name = con.topology.data.name + "_capture_" + con.id + ".pcap";
			var url = "http://" + con.data.host_info.address + ":" + con.data.host_info.fileserver_port + "/" + res + "/download?name=" + encodeURIComponent(name);
			window.location.href = url;
		}})
	},
	viewCapture: function() {
		this.action("download_grant", {params: {limitSize: 1024*1024}, callback: function(con, res) {
			var url = "http://" + con.data.host_info.address + ":" + con.data.host_info.fileserver_port + "/" + res + "/download";
			window.open("http://www.cloudshark.org/view?url="+url, "_newtab");
		}})
	},
	liveCaptureEnabled: function() {
		return this.actionEnabled("download_grant") && this.data.capturing && this.data.capture_mode == "net";
	},
	liveCaptureInfo: function() {
		var host = this.data.host_info.address;
		var port = this.data.capture_port;
		var cmd = "wireshark -k -i <( nc "+host+" "+port+" )";
		new Window({
			title: "Live capture Information", 
			content: '<p>Host: '+host+'<br />Port: '+port+"</p><p>Start live capture via: <pre>"+cmd+"</pre></p>", 
			autoShow: true,
			width: 600
		});
	},
	showConfigWindow: function() {
		var absPos = this.getAbsPos();
		var wsPos = this.editor.workspace.container.position();
		var t = this;
		this.configWindow = new ConnectionAttributeWindow({
			title: "Attributes",
			width: 500,
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) if (values[name] === t.data[name]) delete values[name];
					t.modify(values);		
					t.configWindow.remove();
					t.configWindow = null;
				},
				Cancel: function() {
					t.configWindow.remove();
					t.configWindow = null;
				} 
			}
		}, this);
		this.configWindow.show();
		this.triggerEvent({operation: "attribute-dialog"});
	},
	remove: function(callback, ask) {
		if (this.busy) return;
		if (ask && this.editor.options.safe_mode && ! confirm("Do you want to delete this connection?")) return;
		this.setBusy(true);
		this.triggerEvent({operation: "remove", phase: "begin"});
		var t = this;
		ajax({
			url: 'connection/'+this.id+'/remove',
		 	successFn: function(result) {
		 		t.paintRemove();
		 		delete t.topology.connections[t.id];
		 		for (var i=0; i<t.elements.length; i++) delete t.elements[i].connection;
		 		t.setBusy(false);
		 		if (callback) callback(t);
		 		t.topology.onUpdate();
				t.triggerEvent({operation: "remove", phase: "end"});
				for (var i=0; i<t.elements.length; i++) 
					if (t.elements[i].isRemovable() && t.topology.elements[t.elements[i].id])
						t.elements[i].remove();
		 	},
		 	errorFn: function(error) {
		 		new errorWindow({error:error});
		 		t.setBusy(false);
				t.triggerEvent({operation: "remove", phase: "error"});
		 	}
		});
	},
	name: function() {
		return this.fromElement().name() + " &#x21C4; " + this.toElement().name();
	},
	name_vertical: function() {
		return this.fromElement().name() + "<br/>&#x21C5;<br/>" + this.toElement().name();
	}
});


var Element = Component.extend({
	init: function(topology, data, canvas) {
		this.component_type = "element";
		this._super(topology, data, canvas);
		this.children = [];
		this.connection = null;
	},
	rextfvStatusSupport: function() {
		return this.data.rextfv_supported;
	},
	openRexTFVStatusWindow: function() {
		window.open('../element/'+this.id+'/rextfv_status', '_blank', "innerWidth=350,innerheight=420,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
		this.triggerEvent({operation: "rextfv-status"});
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
		if (! this.caps.children) return false;
		for (var ch in this.caps.children)
			if (this.caps.children[ch].indexOf(this.data.state) >= 0)
				return true;
		return false;
	},
	isRemovable: function() {
		return this.actionEnabled("(remove)");
	},
	isEndpoint: function() {
		return true;
	},
	getUsedAddress: function() {
		if (this.data.use_dhcp) return "dhcp";
		if (! this.data.ip4address) return null;
		res = /10.0.([0-9]+).([0-9]+)\/[0-9]+/.exec(this.data.ip4address);
		if (! res) return res;
		return [parseInt(res[1]), parseInt(res[2])];
	},
	getAddressHint: function() {
		var segs = this.topology.getNetworkSegments();
		for (var i=0; i < segs.length; i++) {
			var seg = segs[i];
			if (seg.elements.indexOf(this.id)>=0) break;
		}
		//Determine major usage counts in segment
		var usedMajors = {};
		for (var i=0; i < seg.elements.length; i++) {
			var el = this.topology.elements[seg.elements[i]];
			if (!el || !el.data) continue; //Element is being created
			if (el.data.type == "external_network_endpoint") return "dhcp";
			var addr = el.getUsedAddress();
			if (! addr) continue;
			if (addr == "dhcp")	usedMajors.dhcp = (usedMajors.dhcp || 0) + 1;
			else usedMajors[addr[0]] = (usedMajors[addr[0]] || 0) + 1;
		}
		//Find the most common major
		var major = null;
		var majorCount = 0;
		for (var m in usedMajors) {
			if (usedMajors[m] > majorCount) {
				major = m;
				majorCount = usedMajors[m]; 
			}
		}
		if (major == "dhcp") return "dhcp";
		if (! major) {
			//If no major in segment so far, find free global major
			var usedMajors = {};
			for (var i=0; i < segs.length; i++) {
				var seg = segs[i];
				for (var j=0; j < seg.elements.length; j++) {
					var el = this.topology.elements[seg.elements[j]];
					if (!el || !el.data) continue; //Element is being created
					var addr = el.getUsedAddress();
					if (! addr || addr == "dhcp") continue;
					usedMajors[addr[0]] = (usedMajors[addr[0]] || 0) + 1; 
				}
			}
			var major = 0;
			while (usedMajors[major]) major++;
			return [major, 1];
		} else {
			//Find free minor for the major
			major = parseInt(major);
			var usedMinors = {};
			for (var j=0; j < seg.elements.length; j++) {
				var el = this.topology.elements[seg.elements[j]];
				if (!el || !el.data) continue; //Element is being created
				var addr = el.getUsedAddress();
				if (! addr || addr == "dhcp") continue;
				if (addr[0] == major) usedMinors[addr[1]] = (usedMinors[addr[1]] || 0) + 1; 
			}
			var minor = 1;
			while (usedMinors[minor]) minor++;
			return [major, minor];			
		}
	},
	calculateSegment: function(els, cons) {
		if (! els) els = [];
		if (! cons) cons = [];
		if (els.indexOf(this.id) >= 0) return {elements: els, connections: cons};
		els.push(this.id);
		if (this.connection) {
			var res = this.connection.calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		if (this.isEndpoint()) return {elements: els, connections: cons};
		for (var i=0; i < this.children.length; i++) {
			var res = this.children[i].calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		if (this.parent) {
			var res = this.parent.calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		return {elements: els, connections: cons};
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
		if (! this.data._pos) {
			this.data._pos = {x: Math.random(), y: Math.random()};
			this.modify_value("_pos", this.data._pos);
		}
		return this.data._pos;
	},
	setPos: function(pos) {
		if (this.editor.options.fixed_pos) return;
		this.data._pos = {x: Math.min(1, Math.max(0, pos.x)), y: Math.min(1, Math.max(0, pos.y))};
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
		this.triggerEvent({operation: "console-dialog"});
	},
	openConsoleNoVNC: function() {
	    window.open('../element/'+this.id+'/console_novnc', '_blank', "innerWidth=760,innerheight=440,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
		this.triggerEvent({operation: "console-dialog"});
	},
	openVNCurl: function() {
		var host = this.data.host_info.address;
		var port = this.data.vncport;
		var passwd = this.data.vncpassword;
		var link = "vnc://:" + passwd + "@" + host + ":" + port;
	    window.open(link, '_self');
		this.triggerEvent({operation: "console-dialog"});
	},
	showVNCinfo: function() {
		var host = this.data.host_info.address;
		var port = this.data.vncport;
		var wport = this.data.websocket_port;
		var passwd = this.data.vncpassword;
		var link = "vnc://:" + passwd + "@" + host + ":" + port;
 		var win = new Window({
 			title: "VNC info",
 			content: '<p>Link: <a href="'+link+'">'+link+'</a><p>Host: '+host+"</p><p>Port: "+port+"</p><p>Websocket-Port: "+wport+"</p><p>Password: <pre>"+passwd+"</pre></p>",
 			autoShow: true,
 			width: 500,
 		});
		this.triggerEvent({operation: "console-dialog"});
	},
	consoleAvailable: function() {
		return this.data.vncpassword && this.data.vncport && this.data.host && this.data.state == "started";
	},
	downloadImage: function() {
		this.action("download_grant", {callback: function(el, res) {
			var name = el.topology.data.name + "_" + el.data.name;
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
			var url = "http://" + el.data.host_info.address + ":" + el.data.host_info.fileserver_port + "/" + res + "/download?name=" + encodeURIComponent(name);
			window.location.href = url;
		}})
	},
	downloadRexTFV: function() {
		this.action("rextfv_download_grant", {callback: function(el, res) {
			var name = el.topology.data.name + "_" + el.data.name + '_rextfv.tar.gz';
			var url = "http://" + el.data.host_info.address + ":" + el.data.host_info.fileserver_port + "/" + res + "/download?name=" + encodeURIComponent(name);
			window.location.href = url;
		}})
	},
	downloadLog: function() {
		this.action("download_log_grant", {callback: function(el, res) {
			var name = el.topology.data.name + "_" + el.data.name + '.log';
			var url = "http://" + el.data.host_info.address + ":" + el.data.host_info.fileserver_port + "/" + res + "/download?name=" + encodeURIComponent(name);
			window.location.href = url;
		}})
	},
	changeTemplate: function(tmplName,action_callback) {
		this.action("change_template", {
			params:{
				template: tmplName
				},
			callback: action_callback
			}
		);
	},
	uploadFile: function(window_title, grant_action, use_action) {
		if (window.location.protocol == 'https:') { //TODO: fix this.
			showError("Upload is currently not available over HTTPS. Load this page via HTTP to do uploads.");
			return;
		}
		this.action(grant_action, {callback: function(el, res) {
			var url = "http://" + el.data.host_info.address + ":" + el.data.host_info.fileserver_port + "/" + res + "/upload";
			var iframe = $('<iframe id="upload_target" name="upload_target">Test</iframe>');
			// iframe.load will be triggered a moment after iframe is added to body
			// this happens in a seperate thread so we cant simply wait for it (esp. on slow Firefox)
			iframe.load(function(){ 
				iframe.off("load");
				iframe.load(function(){
					iframe.remove();
					this.info.remove();
					this.info = null;	
					el.action(use_action);
					$('#upload_from').remove();
					iframe.remove();
				});
				var t = this;							
				var div = $('<div/>');
				this.upload_form = $('<form method="post" id="upload_form" enctype="multipart/form-data" action="'+url+'" target="upload_target">\
								<div class="input-group">\
				                    <span class="btn btn-primary btn-file input-group-btn">\
				                        Browse <input type="file" name="upload" onChange="javascript: $(\'#upload_window_upload\').button(\'enable\'); $(this).parents(\'.input-group\').find(\':text.form-control\').val(this.value.replace(/\\\\/g, \'/\').replace(/.*\\//, \'\'));"/>\
				                    </span>\
									<input type="text" class="form-control" readonly>\
								</div>\
						</form>');
				div.append(this.upload_form);
				this.info = new Window({
					title: window_title, 
					content: div, 
					autoShow: true, 
					width:300,
					buttons: [{
						text: "Upload",
						id: "upload_window_upload",
						disabled: true,
						click: function() {		
							t.upload_form.css("display","none");
							$('#upload_window_upload').button("disable");
							$('#upload_window_cancel').button("disable");
							t.upload_form.submit();
							div.append($('<div style="text-align:center;"><img src="../img/loading_big.gif" /></div>'));
						},
					},
					{
						text: "Cancel",
						id: "upload_window_cancel",
						click: function() {
							t.info.hide();
							t.info.remove();
							t.info = null;
						},
					}]										
				});
			});
			iframe.css("display", "none");
			$('body').append(iframe);			
		}});
	},
	uploadImage: function() {
		this.uploadFile("Upload Image","upload_grant","upload_use");	
	},
	uploadRexTFV: function() {
		this.uploadFile("Upload Executable Archive","rextfv_upload_grant","rextfv_upload_use");
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
	updateDependent: function() {
		for (var i = 0; i < this.children.length; i++) {
			this.children[i].update();
			this.children[i].updateDependent();
		}
		if (this.connection) {
			this.connection.update();
			this.connection.updateDependent();			
		}
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
		this.triggerEvent({operation: "remove", phase: "begin"});
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
			 		t.topology.onUpdate();
					t.triggerEvent({operation: "remove", phase: "end"});
			 	},
			 	errorFn: function(error) {
			 		new errorWindow({error:error});
			 		t.setBusy(false);
					t.triggerEvent({operation: "remove", phase: "error"});
			 	}
			});			
		}
		for (var i=0; i<this.children.length; i++) this.children[i].remove(waiter);
		if (this.connection) this.connection.remove();
		waiter(this);
	},
	name: function() {
		var name = this.data.name;
		if (this.parent) name = this.parent.name() + "." + name;
		return name;
	}
});

var UnknownElement = Element.extend({
	paint: function() {
		var pos = this.getAbsPos();
		this.circle = this.canvas.circle(pos.x, pos.y, 15).attr({fill: "#CCCCCC"});
		this.innerText = this.canvas.text(pos.x, pos.y, "?").attr({"font-size": 25});
		this.text = this.canvas.text(pos.x, pos.y+22, this.data.type + ": " + this.data.name);
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
		this.iconSize = {x: 32, y:32};
		this.busy = false;
		editor.rextfv_status_updater.add(this, 1);
	},
	iconUrl: function() {
		return "img/" + this.data.type + "32.png";
	},
	isMovable: function() {
		return this._super() && !this.busy;
	},
	setBusy: function(busy) {
		this._super(busy);
		this.paintUpdate();
	},
	updateStateIcon: function() {
		
		//set 'host has problems' icon if host has problems
		if (this.data.host_info && this.data.host_info.problems && this.data.host_info.problems.length != 0) {
			this.errIcon.attr({'title':'The Host for this device has problems. Contact an Administrator.'});
			this.errIcon.attr({'src':'/img/error.png'});
		} else {
			this.errIcon.attr({'title':''});
			this.errIcon.attr({'src':'/img/pixel.png'})
		}
		
		if (this.busy) {
			this.stateIcon.attr({src: "img/loading.gif", opacity: 1.0});
			this.stateIcon.attr({title: "Action Running..."});
			this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
			this.rextfvIcon.attr({title: ""});
			return;			
		}

		//set state icon
		switch (this.data.state) {
			case "started":
				this.stateIcon.attr({src: "img/started.png", opacity: 1.0});
				this.stateIcon.attr({title: "State: Started"});
				break;
			case "prepared":
				this.stateIcon.attr({src: "img/prepared.png", opacity: 1.0});
				this.stateIcon.attr({title: "State: Prepared"});
				break;
			case "created":
			default:
				this.stateIcon.attr({src: "img/pixel.png", opacity: 0.0});
				this.stateIcon.attr({title: "State: Created"});
				break;
		}
		
		//set RexTFV icon
		if (this.rextfvStatusSupport() && this.data.state=="started") {
			rextfv_stat = this.data.rextfv_run_status;
			if (rextfv_stat.readable) {
				if (rextfv_stat.isAlive) {
					this.rextfvIcon.attr({src: "img/loading.gif", opacity: 1.0});
					this.rextfvIcon.attr({title: "Executable Archive: Running"});
				} else {
					if (rextfv_stat.done) {
						this.rextfvIcon.attr({src: "img/tick.png", opacity: 1.0});
						this.rextfvIcon.attr({title: "Executable Archive: Done"});
					} else {
						this.rextfvIcon.attr({src: "img/cross.png", opacity: 1.0});
						this.rextfvIcon.attr({title: "Executable Archive: Unknown. Probably crashed."});
					}
				}
			} else {
				this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
				this.rextfvIcon.attr({title: ""});
			}
		} else {
			this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
			this.rextfvIcon.attr({title: ""});
		}
		
	},
	getRectObj: function() {
		return this.rect[0];
	},
	paint: function() {
		var pos = this.canvas.absPos(this.getPos());
		this.icon = this.canvas.image(this.iconUrl(), pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2-5, this.iconSize.x, this.iconSize.y);
		this.text = this.canvas.text(pos.x, pos.y+this.iconSize.y/2, this.data.name);
		this.stateIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2-10, pos.y+this.iconSize.y/2-15, 16, 16);
		this.errIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2, pos.y-this.iconSize.y/2-10, 16, 16);
		this.rextfvIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2, pos.y-this.iconSize.y/2+8, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		this.updateStateIcon();
		//hide icon below rect to disable special image actions on some browsers
		this.rect = this.canvas.rect(pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2-5, this.iconSize.x, this.iconSize.y + 10).attr({opacity: 0.0, fill:"#FFFFFF"});
		this.enableDragging(this.rect);
		this.enableClick(this.rect);
		this.rect.node.obj = this;
		this.rect.conditionalClass("tomato", true);
		this.rect.conditionalClass("element", true);
		this.rect.conditionalClass("selectable", true);
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
		if (! this.icon) return;
		var pos = this.getAbsPos();
		this.icon.attr({src: this.iconUrl(), x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2-5});
		this.stateIcon.attr({x: pos.x+this.iconSize.x/2-10, y: pos.y+this.iconSize.y/2-15});
		this.errIcon.attr({x: pos.x+this.iconSize.x/2, y: pos.y-this.iconSize.y/2-10});
		this.rextfvIcon.attr({x: pos.x+this.iconSize.x/2, y: pos.y-this.iconSize.y/2+8});
		this.rect.attr({x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2-5});
		this.text.attr({x: pos.x, y: pos.y+this.iconSize.y/2, text: this.data.name});
		this.updateStateIcon();
		$(this.rect.node).attr("class", "tomato element selectable");
		this.rect.conditionalClass("connectable", this.isConnectable());
		this.rect.conditionalClass("removable", this.isRemovable());
	}
});

var VPNElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconSize = {x: 32, y:16};
	},
	iconUrl: function() {
		return dynimg(32,"vpn",this.data.mode,null);
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
		return this.topology.createElement({type: "tinc_endpoint", parent: this.data.id}, callback);
	}
});

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

var VMElement = IconElement.extend({
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	iconUrl: function() {
		return this.getTemplate() ? this.getTemplate().iconUrl() : this._super(); 
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	isEndpoint: function() {
		var default_ = true;
		if (this.data && this.data.type == "repy") {
			default_ = false;
			var tmpl = this.getTemplate();
			if (tmpl && tmpl.subtype == "device") default_ = true;
		}
		return (this.data && this.data._endpoint != null) ? this.data._endpoint : default_;
	},
	getTemplate: function() {
		return this.editor.templates.get(this.data.type, this.data.template);
	},
	showTemplateWindow: function(callback_before_finish,callback_after_finish) {
		var window = new TemplateWindow({
			element: this,
			width: 400,
			callback_after_finish: callback_after_finish,
			callback_before_finish: callback_before_finish
		});
		window.show();
	},
	configWindowSettings: function() {
		var config = this._super();
		config.order = ["name", "site", "profile", "template", "_endpoint"];
		config.ignore.push("info_last_sync");
		
		var profileInfo = {};
		var profiles = this.editor.profiles.getAllowed(this.data.type);
		var profile_helptext = null;
		if (!editor.allowRestrictedProfiles)
			profile_helptext = 'If you need more performance, contact your administrator.';
		
		for (var i=0; i<profiles.length; i++) {
			var info = $('<div class="hoverdescription" style="display: inline;"></div>');
			var d = $('<div class="hiddenbox"></div>');
			var p = $('<p style="margin:4px; border:0px; padding:0px; color:black;"></p>');
			var desc = $('<table></table>');
			p.append(desc);
			d.append(p);
			
			var prof = profiles[i];
			
			info.append('<img src="/img/info.png" />');

			if (prof.description) {
				desc.append($('<tr><th><img src="/img/info.png" /></th><td style="background:white; white-space:pre !important; padding-bottom:0.3cm;">'+prof.description+'</td></tr>'));
			}
			
			if (prof.cpus) {
				desc.append($('<tr><th>CPUs</th><td style="background:white; white-space:nowrap !important;">'+prof.cpus+'</td></tr>'));
			}
			
			if (prof.ram) {
				desc.append($('<tr><th>RAM</th><td style="background:white; white-space:nowrap !important;">'+prof.ram+' MB</td></tr>'));
			}
			
			if (prof.diskspace) {
				desc.append($('<tr><th>Disk</th><td style="background:white; white-space:nowrap !important;">'+prof.diskspace+' MB</td></tr>'));
			}
			
			if (prof.restricted) {
				info.append('<img src="/img/lock_open.png" />');
				desc.append($('<tr><th><img src="/img/lock_open.png" /></th><td style="min-width:4.8cm; padding-top:0.3cm;">This profile is restricted; you have access to restricted profiles.</td></tr>'));
			}
			
			info.append(d);
			profileInfo[prof.name] = info;
		}
		
		
		var siteInfo = {};
		var sites = this.editor.sites;
		
		for (var i=0; i<sites.length; i++) {
			var info = $('<div class="hoverdescription" style="display: inline;"></div>');
			var d = $('<div class="hiddenbox"></div>');
			var p = $('<p style="margin:4px; border:0px; padding:0px; color:black;"></p>');
			var desc = $('<table></table>');
			p.append(desc);
			d.append(p);
			
			site = sites[i];
			
			info.append('<img src="/img/info.png" />');
			
			if (this.data.host_info && this.data.host_info.site && this.data.site == null) {
				info.append('<img src="/img/automatic.png" />'); //TODO: insert a useful symbol for "automatic" here and on the left column one line below
				desc.append($('<tr><th><img src="/img/automatic.png" /></th><td>This site has been automatically selected by the backend.</td></tr>'))
			}

			if (site.description) {
				desc.append($('<tr><th><img src="/img/info.png" /></th><td style="background:white;">'+site.description+'</td></tr>'));
			}
			
			var hostinfo_l = '<tr><th><img src="/img/server.png" /></th><td style="background:white;"><h3>Hosted By:</h3>';
			var hostinfo_r = '</td></tr>';
			if (site.organization.homepage_url) {
				hostinfo_l = hostinfo_l + '<a href="' + site.organization.homepage_url + '">';
				hostinfo_r = '</a>' + hostinfo_r;
			}
			if (site.organization.image_url) {
				hostinfo_l = hostinfo_l + '<img style="max-width:8cm;max-height:8cm;" src="' + site.organization.image_url + '" title="' + site.organization.label + '" />';
			} else {
				hostinfo_l = hostinfo_l + site.organization.label;
			}
			desc.append($(hostinfo_l + hostinfo_r));
			
			info.append(d);
			siteInfo[site.name] = info;
		}
		
		config.special.template = new TemplateElement({
			label: "Template",
			name: "template",
			value: this.data.template || this.caps.attributes.template["default"],
			custom_template: this.data.custom_template,
			disabled: (this.data.state == "started"),
			type: this.data.type,
			call_element: this
		});
		config.special.site = new ChoiceElement({
			label: "Site",
			name: "site",
			info: siteInfo,
			choices: createMap(this.editor.sites, "name", function(site) {
				return (site.label || site.name) + (site.location ? (", " + site.location) : "");
			}, {"": "Any site"}),
			value: (this.data.host_info && this.data.host_info.site) || this.data.site || this.caps.attributes.site["default"],
			disabled: !this.attrEnabled("site")
		});
		config.special.profile = new ChoiceElement({
			label: "Performance Profile",
			name: "profile",
			info: profileInfo,
			choices: createMap(this.editor.profiles.getAllowed(this.data.type), "name", "label"),
			value: this.data.profile || this.caps.attributes.profile["default"],
			disabled: !this.attrEnabled("profile"),
			help_text: profile_helptext
		});
		config.special._endpoint = new ChoiceElement({
			label: "Segment seperation",
			name: "_endpoint",
			choices: {true: "Seperates segments", false: "Connects segments"},
			value: this.isEndpoint(),
			inputConverter: Boolean.parse
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
		var mag = settings.childElementDistance / Math.sqrt(magSquared);
		return {x: ppos.x + (xd * mag), y: ppos.y + (yd * mag)};
	},
	isEndpoint: function() {
		return this.parent.isEndpoint();
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
	},
	updateData: function(data) {
		this._super(data);
		if (this.parent && ! this.connection && this.isRemovable()) this.remove();
	}
});

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

var SwitchPortElement = ChildElement.extend({
	configWindowSettings: function() {
		var config = this._super();
		config.order.remove("name");
		config.ignore += ["name", "kind", "peers"];
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

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

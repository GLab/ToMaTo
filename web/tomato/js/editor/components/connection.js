
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

/********************************************************************************
 * Browser quirks:
 * - IE8 does not like a comma after the last function in a class
 * - IE8 does not like colors defined as words, so only traditional #RRGGBB colors
 * - IE8 does not like texts with specified fonts, etc.
 * - Firefox opens new tabs/windows when icons are clicked with shift or ctrl key
 *   hold, so all icons are overlayed with a transparent rectangular
 * - Opera zooms in when ctrl is hold while pressing the left mouse button and
 *   reacts sometimes strangely when alt key is hold.
 * - IE8 does not support auto-sizing of dialogs, so dialogs look awful.
 * - IE8 does not correctly support transparency in svg but transparent images can
 * 	 be used
 ********************************************************************************/ 

var NetElement = Class.extend({
	init: function(editor){
		this.editor = editor;
		this.selected = false;
		this.editor.addElement(this);
		this.attributes = {};
	},
	checkRemove: function(){
		return true;
	},
	remove: function(){
		this.editor.removeElement(this);
		if (this.selectionFrame) this.selectionFrame.remove();
		if (this.getElementName()) this.editor.ajaxModify([this.modification("delete", {})], function(res) {});
	},
	paint: function(){
	},
	paintUpdate: function(){
		if (this.selected) {
			var rect = this.getRect();
			rect = {x: rect.x-5, y: rect.y-5, width: rect.width+10, height: rect.height+10};
			if (!this.selectionFrame) this.selectionFrame = this.editor.g.rect(rect.x, rect.y, rect.width, rect.height).attr({stroke:this.editor.glabColor, "stroke-width": 2});
			this.selectionFrame.attr(rect);
		} else {
			if (this.selectionFrame) this.selectionFrame.remove();
			this.selectionFrame = false;
		}
	},
	getX: function() {
		return this.getPos().x;
	},
	getY: function() {
		return this.getPos().y;
	},
	getWidth: function() {
		return this.getSize().x;
	},
	getHeight: function() {
		return this.getSize().y;
	},
	getRect: function() {
		return {x: this.getX()-this.getWidth()/2, y: this.getY()-this.getHeight()/2, width: this.getWidth(), height: this.getHeight()};
	},
	setSelected: function(isSelected) {
		this.selected = isSelected;
		this.paintUpdate();
	},
	isSelected: function() {
		return this.selected;
	},
	onClick: function(event) {
		if (!this.editor.editable) {
			this.form.toggle();
			return;
		}
		if (event.shiftKey) this.setSelected(!this.isSelected());
		else {
			var oldSelected = this.isSelected();
			var sel = this.editor.selectedElements();
			for (var i = 0; i < sel.length; i++) sel[i].setSelected(false);
			this.setSelected(!oldSelected | sel.length>1);
		}
	},
	modification: function(type, attr) {
		return {"type": this.getElementType() + "-" + type, "element": this.getElementName(), "subelement": this.getSubElementName(), "properties": attr};
	},
	action: function(action) {
		return {"element_type": this.getElementType(), "element_name": this.getElementName(), "action": action, "attrs": {}};
	},
	setAttribute: function(name, value) {
		this.attributes[name]=value;
		var attr = {};
		attr[name]=value;
		this.editor.ajaxModify([this.modification("configure", attr)]);
	},
	getAttribute: function(name, deflt) {
		return this.attributes[name] ? this.attributes[name] : deflt;
	},
	setAttributes: function(attrs) {
		this.attributes = {};
		for (var key in attrs) this.setAttribute(key, attrs[key]);
		if (this.form && this.form.reload) this.form.reload();
	},
	setCapabilities: function(capabilities) {
		this.capabilities = capabilities;
		if (this.form && this.form.reload) this.form.reload();
	},
	setResources: function(resources) {
		this.resources = resources;
		if (this.form && this.form.reload) this.form.reload();
	},
	getElementType: function() {
		return "";
	},
	getElementName: function() {
		return "";
	},
	getSubElementName: function() {
		return "";
	},
	stateAction: function(action) {
		var t = this;
		this.editor.ajaxAction(this.action(action), function() {
			t.editor.reloadTopology();			
		});
	}
});

var IconElement = NetElement.extend({
	init: function(editor, name, iconsrc, iconsize, pos) {
		this.name = name;
		this._super(editor);
		this.iconsrc = iconsrc;
		this.iconsize = iconsize;
		this.pos = pos;
		this.paletteItem = false;
	},
	_dragMove: function (dx, dy) {
		var p = this.parent;
		if (! p.editor.editable) return false;
		if (p.paletteItem) p.shadow.attr({x: p.opos.x + dx-p.iconsize.x/2, y: p.opos.y + dy-p.iconsize.y/2});
		else {
			var sel = p.editor.selectedElements();
			if (sel.length == 0 || sel.indexOf(p) < 0) p.move({x: p.opos.x + dx, y: p.opos.y + dy});
			else for (var i = 0; i < sel.length; i++) if(sel[i].isDevice || sel[i].isConnector) sel[i].move({x: sel[i].opos.x + dx, y: sel[i].opos.y + dy});
		}
	}, 
	_dragStart: function () {
		var p = this.parent;
		if (! p.editor.editable) return false;
		var sel = p.editor.selectedElements();
		if (sel.length == 0 || sel.indexOf(p) < 0) p.opos = p.pos;
		else for (var i = 0; i < sel.length; i++) if(sel[i].isDevice || sel[i].isConnector) sel[i].opos = sel[i].pos;
		if (p.paletteItem) p.shadow = p.icon.clone().attr({opacity:0.5});
	},
	_dragStop: function () {
		var p = this.parent;
		if (! p.editor.editable) return false;
		if (p.paletteItem) {
			var pos = {x: p.shadow.attr("x")+p.iconsize.x/2, y: p.shadow.attr("y")+p.iconsize.y/2};
			if (pos.x != p.opos.x || pos.y != p.opos.y) {
				var tr =p.editor.ajaxModifyBegin();
				var element = p.createAnother(pos);
				element.move(element.correctPos(pos));
				if (tr) p.editor.ajaxModifyCommit();
			}
			p.shadow.remove();
		}
		if (p.pos != p.opos) {
			var tr = p.editor.ajaxModifyBegin();
			var sel = p.editor.selectedElements();
			if (sel.length == 0 || sel.indexOf(p) < 0) {
				p.move(p.correctPos(p.pos));
				p.lastMoved = new Date();
				p.setAttribute("_pos", (p.pos.x-p.editor.paletteWidth)+","+p.pos.y);
			} else for (var i = 0; i < sel.length; i++) if(sel[i].isDevice || sel[i].isConnector) {
				sel[i].move(sel[i].correctPos(sel[i].pos));
				sel[i].lastMoved = new Date();
				sel[i].setAttribute("_pos", (sel[i].pos.x-sel[i].editor.paletteWidth)+","+sel[i].pos.y);
			}
			if(tr) p.editor.ajaxModifyCommit();
		}
	},
	_click: function(event){
		var p = this.parent;
		if (p.lastMoved && p.lastMoved.getTime() + 100 > new Date().getTime()) return;
		p.onClick(event);
	},
	_dblclick: function(event){
		var p = this.parent;
		p.form.toggle();
	},
	paint: function(){
		this._super();
		if (this.text) this.text.remove();
		this.text = this.editor.g.text(this.pos.x, this.pos.y+this.iconsize.y/2+6, this.name);
		if (! isIE) this.text.attr(this.editor.defaultFont);
		this.text.parent = this;
		if (this.icon) this.icon.remove();
		this.icon = this.editor.g.image(basepath+this.iconsrc, this.pos.x-this.iconsize.x/2, this.pos.y-this.iconsize.y/2, this.iconsize.x, this.iconsize.y);
		this.icon.parent = this;
		this.stateIcon = this.editor.g.image(basepath+"images/pixel.png", this.pos.x+5, this.pos.y+5, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		var r = this.getRect();
		if (this.rect) this.rect.remove();
		this.rect = this.editor.g.rect(r.x, r.y, r.width, r.height).attr({opacity:0, fill:"#FFFFFF"});
		this.rect.parent = this;
		this.rect.drag(this._dragMove, this._dragStart, this._dragStop);
		this.rect.click(this._click);    
		this.rect.dblclick(this._dblclick);
	},
	getRectObj: function() {
		return this.rect[0];
	},
	paintUpdate: function() {
		this.icon.attr({x: this.pos.x-this.iconsize.x/2, y: this.pos.y-this.iconsize.y/2, src: basepath+this.iconsrc});
		this.stateIcon.attr({x: this.pos.x+5, y: this.pos.y+5});
		this.text.attr({x: this.pos.x, y: this.pos.y+this.iconsize.y/2+6, text: this.name});
		this.rect.attr(this.getRect());
		this._super(); //must be at end, so rect has already been updated
	},
	setAttribute: function(name, value) {
		if (name == "name") {
			this.editor.elementNames.remove(this.name);
			this.editor.ajaxModify([this.modification("rename", {name: value})], function(res) {});
			this.name = value;
			this.attributes[name] = value;
			this.paintUpdate();
			this.editor.elementNames.push(value);
		} else if (name == "state") {
			this.attributes[name] = value;
			switch (value) {
				case "started":
				case "prepared":
					this.stateIcon.attr({src: basepath+"images/"+value+".png"});
					this.stateIcon.attr({opacity: 1.0});
					break;
				default:
					this.stateIcon.attr({src: basepath+"images/pixel.png", opacity: 0.0});
			}
		} else this._super(name, value);
	},
	remove: function(){
		this._super();
		if (this.icon) this.icon.remove();
		if (this.text) this.text.remove();
		if (this.rect) this.rect.remove();
		if (this.stateIcon) this.stateIcon.remove();
	},
	correctPos: function(pos) {
		if (pos.x + this.iconsize.x/2 > this.editor.g.width) pos.x = this.editor.g.width - this.iconsize.x/2;
		if (pos.y + this.iconsize.y/2 + 11 > this.editor.g.height) pos.y = this.editor.g.height - this.iconsize.y/2 - 11;
		if (pos.x - this.iconsize.x/2 < this.editor.paletteWidth) pos.x = this.editor.paletteWidth + this.iconsize.x/2;
		if (pos.y - this.iconsize.y/2 < 0) pos.y = this.iconsize.y/2;
		return pos;
	},
	move: function(pos) {
		pos.x = pos.x || 0;
		pos.y = pos.y || 0;
		this.pos = pos;
		this.paintUpdate();
	},
	getPos: function() {
		return this.pos;
	},
	getSize: function() {
		return {x: Math.max(this.text.getBBox().width,this.iconsize.x), y: this.iconsize.y + this.text.getBBox().height};
	},
	getRect: function() {
		return compoundBBox([this.text, this.icon]);
	},
	createAnother: function(pos) {
	},
	setSelected: function(isSelected) {
		this._super(isSelected & !this.paletteItem);
	},
	getElementName: function() {
		return this.name;
	}
});
	
var Topology = IconElement.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/topology.png", {x: 32, y: 32}, pos);
		this.paletteItem = true;
		this.paint();
		this.isTopology = true;
		this.warnings = [];
		this.errors = [];
		this.form = new TopologyWindow(this);
	},
	paint: function() {
		this._super();
		this.stateIcon = this.editor.g.image(basepath+"images/pixel.png", this.pos.x+5, this.pos.y+5, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		this.stateIcon.parent = this;
		this.stateIcon.click(this._click);
	},
	paintUpdate: function() {
		this._super();
		if (this.errors.length>0) {
			this.stateIcon.attr({src: basepath+"images/error.png"});
			this.stateIcon.attr({opacity: 1.0});		    
		} else if (this.warnings.length>0) {
			this.stateIcon.attr({src: basepath+"images/warning.png"});
			this.stateIcon.attr({opacity: 1.0});
		} else this.stateIcon.attr({opacity: 0.0});
	},
	setAttribute: function(name, value) {
		if (name == "state") return;
		if (name == "name") {
			this.editor.ajaxModify([this.modification("rename", {name: value})], function(res) {});
			this.attributes[name]=value;
		} else this._super(name, value);
	},
	_dragStart: function () {
	},
	_dragMove: function (dx, dy) {
	},
	_dragStop: function () {
	},
	getElementType: function () {
		return "topology";
	},
	setPermission: function(user, role) {
		log("Permission:" + user + "=" + role);
		var t = this;
		var data = {"permission": $.toJSON({user:user, role:role})};
		this.editor._ajax("top/"+topid+"/permission", data, function(){
			t.editor.reloadTopology(function(){
				t.form.reload();				
			});
		});
	}
});

var Connection = NetElement.extend({
	init: function(editor, con, dev) {
		this._super(editor);
		this.con = con;
		this.dev = dev;
		this.paint();
		this.isConnection = true ;
		this.iface = false;
		this.name = "connection";
		this.form = new ConnectionWindow(this);		
	},
	checkRemove: function(){
		return this.con.checkModifyConnections() && this.dev.checkModifyConnections();
	},	
	connect: function(iface) {
		this.iface = iface;
		this.attributes["interface"] = this.getSubElementName();
		this.editor.ajaxModify([this.modification("create", this.attributes)], function(res) {});
	},
	getElementType: function () {
		return "connection";
	},
	getElementName: function () {
		if (this.con) return this.con.name;
		else return "";
	},
	getSubElementName : function() {
		if (this.dev && this.iface) return this.dev.name + "." + this.iface.name;
		else return "";
	},
	getIPHint: function() {
		return "dhcp";
	},	
	getPos: function(){
		return {x: (this.con.getX()+this.dev.getX())/2, y: (this.con.getY()+this.dev.getY())/2};
	},
	getSize: function() {
		return {x: 16, y: 16};
	},
	getPath: function(){
		return "M"+this.con.getX()+" "+this.con.getY()+"L"+this.dev.getX()+" "+this.dev.getY();
	},
	paintUpdate: function(){
		this._super();
		this.path.attr({path: this.getPath()});
		this.handle.attr({x: this.getX()-8, y: this.getY()-8});
	},
	paint: function(){
		this._super();
		if (this.path) this.path.remove();
		this.path = this.editor.g.path(this.getPath());
		this.path.toBack();
		if (this.handle) this.handle.remove();
		this.handle = this.editor.g.rect(this.getX()-8, this.getY()-8, 16, 16).attr({fill: "#A0A0A0"});
		this.handle.parent = this;
		this.handle.drag(this._dragMove, this._dragStart, this._dragStop);
		this.handle.click(this._click);
		this.handle.dblclick(this._dblclick);
	},
	getRectObj: function(){
		return this.handle[0];
	},
	remove: function(){
		this._super();
		if (this.path) this.path.remove();
		if (this.handle) this.handle.remove();
		if (this.con) this.con.removeConnection(this);
		if (this.iface) {
			var tmp = this.iface;
			delete this.iface;
			tmp.remove();
		}
		delete this.con;
		delete this.dev;
	},
	_click: function(event){
		var p = this.parent;
		p.onClick(event);
	},
	_dblclick: function(event){
		var p = this.parent;
		p.form.toggle();
	}
});

var EmulatedConnection = Connection.extend({
	init: function(editor, dev, con){
		this._super(editor, dev, con);
		this.handle.attr({fill: this.editor.glabColor});
		this.form = new EmulatedConnectionWindow(this);
		this.IPHintNumber = this.con.nextIPHintNumber++;
		// not using setAttribute to avoid direct modify call 
		this.attributes["bandwidth"] = "10000";
		this.attributes["delay"] = "0";
		this.attributes["lossratio"] = "0.0";
	},
	getIPHint: function() {
		if (this.con.isRouted()) return {ipv4: "10."+this.con.IPHintNumber+"."+this.IPHintNumber+".1/24",
			ipv6: "fd01:ab1a:b1ab:"+this.con.IPHintNumber.toString(16)+":"+this.IPHintNumber.toString(16)+"::1/80"};
		else return {ipv4: "10."+this.con.IPHintNumber+".0."+this.IPHintNumber+"/24", 
			ipv6: "fd01:ab1a:b1ab:"+this.con.IPHintNumber.toString(16)+":"+this.IPHintNumber.toString(16)+"::1/64"};
	},
	connect: function(iface) {
		this._super(iface);
		if (! this.getAttribute("gateway4")) this.setAttribute("gateway4", "10."+this.con.IPHintNumber+"."+this.IPHintNumber+".254/24");
		if (! this.getAttribute("gateway6")) this.setAttribute("gateway6", "fd01:ab1a:b1ab:"+this.con.IPHintNumber.toString(16)+":"+this.IPHintNumber.toString(16)+":FFFF:FFFF:FFFF/80");
		if (! this.dev.getAttribute("gateway4")) this.dev.setAttribute("gateway4", "10."+this.con.IPHintNumber+"."+this.IPHintNumber+".254");
		if (! this.dev.getAttribute("gateway6")) this.dev.setAttribute("gateway6", "fd01:ab1a:b1ab:"+this.con.IPHintNumber.toString(16)+":"+this.IPHintNumber.toString(16)+":FFFF:FFFF:FFFF");
	},
	downloadSupported: function() {
		return this.capabilities && this.capabilities.action && this.capabilities.action.download_capture && Boolean.parse(this.capabilities.action.download_capture);
	},
	liveCaptureSupported: function() {
		return this.capabilities && this.capabilities.other && this.capabilities.other.live_capture && Boolean.parse(this.capabilities.other.live_capture);
	},
	showLiveCaptureInfo: function() {
		var host = this.getAttribute("capture_host");
		var port = this.getAttribute("capture_port");
		var cmd = "wireshark -k -i <( nc "+host+" "+port+" )";
		this.editor.infoMessage("Live capture Information", '<p>Host: '+host+'<p>Port: '+port+"</p><p>Start live capture via: <pre>"+cmd+"</pre></p>");
	},
	downloadCapture: function(btn) {
		btn.setEditable(false);
		btn.setContent("Preparing download ...");
		btn.setFunc(function(){
			return false;
		});
		var t = this;
		this.editor._ajax("top/"+topid+"/download_capture_uri/"+this.getElementName()+"/"+this.getSubElementName(), {}, function(msg) {
			btn.setEditable(true);
			btn.setContent("Download capture");
			btn.setFunc(function(){
				window.location.href=msg;				
			});
		});
	},
	viewCapture: function(btn) {
		var t = this;
		this.editor._ajax("top/"+topid+"/download_capture_uri/"+this.getElementName()+"/"+this.getSubElementName(), {"onlyLatest": true}, function(msg) {
			window.open("http://www.cloudshark.org/view?url="+escape(unescape(msg)), "_newtab");
		});
	}
});

var Interface = NetElement.extend({
	init: function(editor, dev, con, fixedName){
		this._super(editor);
		this.dev = dev;
		this.con = con;
		this.paint();
		this.isInterface = true;
		if (fixedName) this.name = fixedName;
		else this.name = this.proposedName();
		this.form = new InterfaceWindow(this);
		this.editor.ajaxModify([this.modification("create", {name: this.name})], function(res) {});
	},
	proposedName: function() {
		existingNames = [];
		for (var i=0; i < this.dev.interfaces.length; i++) existingNames.push(this.dev.interfaces[i].name);
		var base = "eth";
		var num = 0;
		while (existingNames.indexOf(base+num)>=0) num++;
		return base+num;
	},
	getElementType: function () {
		return "interface";
	},
	getElementName: function () {
		return this.dev.name;
	},
	getSubElementName : function() {
		return this.name;
	},
	getPos: function() {
		var xd = this.con.getX() - this.dev.getX();
		var yd = this.con.getY() - this.dev.getY();
		var magSquared = (xd * xd + yd * yd);
		var mag = 14.0 / Math.sqrt(magSquared);
		return {x: this.dev.getX() + (xd * mag), y: this.dev.getY() + (yd * mag)};
	},
	getSize: function() {
		return {x: 16, y: 16};
	},
	paint: function(){
		if (this.circle) this.circle.remove();
		this.circle = this.editor.g.circle(this.getX(), this.getY(), 8).attr({fill: "#CDCDB3"});
		this.circle.parent = this;
		this.circle.click(this._click);
		this.circle.dblclick(this._dblclick);
	},
	paintUpdate: function(){
		this._super();
		this.circle.attr({cx: this.getX(), cy: this.getY()});
	},
	getRectObj: function(){
		return this.circle[0];
	},
	remove: function(){
		this._super();
		if (this.circle) this.circle.remove();
		if (this.dev) this.dev.removeInterface(this);
		delete this.con;
		delete this.dev;
	},
	setAttribute: function(name, value){
		if (name == "name") {
			this.form.setTitle(value);
			this.editor.ajaxModify([this.modification("rename", {name: value})], function(res) {});
			this.name = value;
			this.attributes[name] = value;
		} else this._super(name, value);
	},
	_click: function(event) {
		var p = this.parent;
		p.onClick(event);
	},
	_dblclick: function(event){
		var p = this.parent;
		p.form.toggle();
	}
});

var ConfiguredInterface = Interface.extend({
	init: function(editor, dev, con, fixedName){
		this._super(editor, dev, con, fixedName);
		this.form = new ConfiguredInterfaceWindow(this);
		var ipHint = con.getIPHint();
		this.setAttribute("use_dhcp", ipHint == "dhcp");
		if (ipHint != "dhcp" ) {
			this.setAttribute("ip4address", ipHint.ipv4);
			this.setAttribute("ip6address", ipHint.ipv6);
		}
	}
});

var Connector = IconElement.extend({
	init: function(editor, name, iconsrc, iconsize, pos) {
		this._super(editor, name, iconsrc, iconsize, pos);
		this.connections = [];
		this.paint();
		this.isConnector = true;
		this.IPHintNumber = this.editor.nextIPHintNumber++;
		this.nextIPHintNumber = 1;
		this.editor.ajaxModify([this.modification("create", {type: this.baseName(), _pos:(pos.x-editor.paletteWidth)+","+pos.y, name: name})], function(res) {});
	},
	getElementType: function () {
		return "connector";
	},
	getElementName: function () {
		return this.name;
	},
	nextName: function() {
		return this.editor.getNameHint(this.baseName());
	},
	checkRemove: function(){
		if (! this.capabilities.modify["delete"]) {
			this.editor.errorMessage("Cannot delete element", "The element " + this.getElementName() + " cannot be deleted in its current state");
			return false;
		} else return true;
	},	
	checkModifyConnections: function(){
		if (! this.capabilities.modify.connections) {
			this.editor.errorMessage("Cannot modify connections", "The element " + this.getElementName() + " cannot be connected or disconnected in its current state");
			return false;
		} else return true;
	},		
	remove: function(){
		var cons = this.connections.slice(0);
		for (var i = 0; i < cons.length; i++) cons[i].remove();
		this._super();
	},
	move: function(pos) {
		this._super(pos);
		for (var i = 0; i < this.connections.length; i++) {
			this.connections[i].paintUpdate();
			this.connections[i].dev.paintUpdateInterfaces();
		}    
	},
	onClick: function(event) {
		if (event.ctrlKey || event.altKey) {
			var tr = this.editor.ajaxModifyBegin();
			var selectedElements = this.editor.selectedElements();
			for (var i = 0; i < selectedElements.length; i++) {
				var el = selectedElements[i];
				this.editor.connect(this, el);
			}
			if (tr) this.editor.ajaxModifyCommit();
		} else this._super(event);
	},
	isConnectedWith: function(dev) {
		for (var i = 0; i < this.connections.length; i++) if (this.connections[i].dev == dev) return true;
		return false;
	},
	externalAccessSupported: function() {
		return this.capabilities && this.capabilities.other && this.capabilities.other.external_access;
	},
	showExternalAccessInfo: function() {
		var host = this.getAttribute("external_access_host");
		var port = this.getAttribute("external_access_port");
		var passwd = this.getAttribute("external_access_password");
		this.editor.infoMessage("External access information for " + this.name, '<p>Config file vtund.conf: <br/><pre>client {\n  password '+passwd+';\n  type ether;\n  proto udp;\n  up {\n    ip "link set %% up";\n  }\n}</pre><p>Command: <pre>vtund -f vtund.conf -P '+port+' client '+host+'</pre></p>');
	},
	createConnection: function(dev) {
		var con = new Connection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	},
	removeConnection: function(con) {
		this.connections.remove(con);
	},
	getConnection: function(ifname) {
		for (var i=0; i < this.connections.length; i++) {
			var el = this.connections[i];
			if (el.getSubElementName() == ifname) return el;
		}
	}
});

var ExternalConnector = Connector.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/external.png", {x: 32, y: 32}, pos);
		this.form = new ExternalConnectorWindow(this);
		this.setAttribute("network_type", "internet");
	},
	nextIPHint: function() {
		return "dhcp";
	},
	setAttribute: function(name, value) {
		this._super(name, value);
		if (name == "network_type") {
			var type = value.split(".")[0];
			if (type=="openflow" || type=="internet") this.iconsrc="images/"+type+".png";
			else this.iconsrc="images/external.png";
			this.paintUpdate();
		}
	},
	baseName: function() {
		return "external";
	},
	createAnother: function(pos) {
		return new ExternalConnector(this.editor, this.nextName(), pos);
	}
});

var VPNConnector = Connector.extend({
	init: function(editor, name, pos) {
		if (!pos) { //called with 2 parameters
			pos = name;
			name = this.nextName();
		}
		this._super(editor, name, "images/switch.png", {x: 32, y: 16}, pos);
		this.form = new VPNConnectorWindow(this);
		this.setAttribute("mode", "switch");
	},
	nextIPHint: function() {
		return "10."+this.IPHintNumber+"."+(this.nextIPHintNumber++)+".1/24";
	},
	setAttribute: function(name, value) {
		this._super(name, value);
		if (name == "mode") {
			this.iconsrc="images/"+value+".png";
			this.paintUpdate();
		}
	},
	isRouted: function() {
		return this.getAttribute("mode") == "router";
	},
	baseName: function() {
		return "vpn";
	},
	createAnother: function(pos) {
		return new VPNConnector(this.editor, this.nextName(), pos);
	},
	createConnection: function(dev) {
		var con = new EmulatedConnection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	}
});

var Device = IconElement.extend({
	init: function(editor, name, iconsrc, iconsize, pos) {
		this._super(editor, name, iconsrc, iconsize, pos);
		this.interfaces = [];
		this.paint();
		this.isDevice = true;
		this.editor.ajaxModify([this.modification("create", {type: this.baseName(), _pos:(pos.x-editor.paletteWidth)+","+pos.y, name: name})], function(res) {});
	},
	getElementType: function () {
		return "device";
	},
	getElementName: function () {
		return this.name;
	},
	nextName: function() {
		return this.editor.getNameHint(this.baseName());
	},
	checkRemove: function(){
		if (! this.capabilities.modify["delete"]) {
			this.editor.errorMessage("Cannot delete element", "The element " + this.getElementName() + " cannot be deleted in its current state");
			return false;
		} else return true;
	},		
	checkModifyConnections: function(){
		if (! this.capabilities.modify.connections) {
			this.editor.errorMessage("Cannot modify connections", "The element " + this.getElementName() + " cannot be connected or disconnected in its current state");
			return false;
		} else return true;
	},		
	remove: function(){
		var ifs = this.interfaces.slice(0);
		for (var i = 0; i < ifs.length; i++) {
			if(ifs[i].con) ifs[i].con.remove();
			else ifs[i].remove();
		}
		this._super();
	},
	move: function(pos) {
		this._super(pos);
		for (var i = 0; i < this.interfaces.length; i++) this.interfaces[i].con.paintUpdate();
		this.paintUpdateInterfaces();   
	},
	paint: function() {
		this._super();
		for (var i = 0; i < this.interfaces.length; i++) this.interfaces[i].paint();    
	},
	paintUpdateInterfaces: function() {
		for (var i = 0; i < this.interfaces.length; i++) this.interfaces[i].paintUpdate();
	},
	onClick: function(event) {
		if (event.ctrlKey || event.altKey) {
			var tr = this.editor.ajaxModifyBegin();
			var selectedElements = this.editor.selectedElements();
			for (var i = 0; i < selectedElements.length; i++) {
				var el = selectedElements[i];
				this.editor.connect(el, this);
			}
			if (tr) this.editor.ajaxModifyCommit();
		} else this._super(event);
	},
	isConnectedWith: function(con) {
		for (var i = 0; i < this.interfaces.length; i++) if (this.interfaces[i].con.con == con) return true;
		return false;
	},
	createInterface: function(con, fixedName) {
		var iface = new Interface(this.editor, this, con, fixedName);
		this.interfaces.push(iface);
		return iface;
	},
	removeInterface: function(iface) {
		this.interfaces.remove(iface);
	},
	getInterface: function(ifname) {
		for (var i=0; i < this.interfaces.length; i++) {
			var el = this.interfaces[i];
			if (el.name == ifname) return el;
		}
	},
	consoleSupported: function() {
		return this.capabilities && this.capabilities.other && this.capabilities.other.console;
	},
	downloadSupported: function() {
		return this.capabilities && this.capabilities.action && this.capabilities.action.download_image;
	},
	uploadSupported: function() {
		return this.capabilities && this.capabilities.action && this.capabilities.action.upload_image_prepare;
	},
	showConsole: function() {
		var url = "/top/console?" + $.param({topology: this.editor.topology.getAttribute("name"), device: this.name, host: this.getAttribute("host"), port: this.getAttribute("vnc_port"), password: this.getAttribute("vnc_password")});
		var console = window.open(url, '_blank', "innerWidth=745,innerheight=400,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
	},
	showVNCinfo: function() {
		var host = this.getAttribute("host");
		var port = this.getAttribute("vnc_port");
		var passwd = this.getAttribute("vnc_password");
		var link = "vnc://" + host + ":" + port;
		this.editor.infoMessage("VNC Information for " + this.name, '<p>Link: <a href="'+link+'">'+link+'</a><p>Host: '+host+"</p><p>Port: "+port+"</p><p>Password: <pre>"+passwd+"</pre></p>");
	},
	uploadImage: function() {
		var t = this;
		this.editor._ajax("top/"+topid+"/upload_image_uri/"+this.name, {}, function(grant) {
			var div = $('<div/>');
			var iframe = $('<iframe id="upload_target" name="upload_target"/>');
			iframe.css("display", "none");
			$('body').append(iframe);
			div.append('<form method="post" enctype="multipart/form-data" action="'+grant.upload_url+'" target="upload_target"><input type="file" name="upload"/><br/><input type="submit" value="upload"/></form>');
			iframe.load(function(){
				var html = $(frames["upload_target"].document).find("html").find("body").html();
				var msg = $.parseJSON(html);
				if (! msg) return;
				iframe.remove();
				info.remove();
				if (! Boolean.parse(msg.success)) editor.errorMessage("Request failed", "<p><b>Error message:</b> " + msg.output + "</p><p>This page will be reloaded to refresh the editor.</p>").bind("dialogclose", function(){
					window.location.reload();
				});
				else t.editor.followTask(msg.output);
			});
			var info = t.editor.infoMessage("Upload image", div);
		});		
	},
	downloadImage: function(btn) {
		btn.setEditable(false);
		btn.setContent("Preparing download ...");
		btn.setFunc(function(){
			return false;
		});
		var t = this;
		this.editor._ajax("top/"+topid+"/download_image_uri/"+this.name, {}, function(msg) {
			btn.setEditable(true);
			btn.setContent("Download image");
			btn.setFunc(function(){
				window.location.href=msg;				
			});
		});
	}
});

var OpenVZDevice = Device.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/openvz.png", {x: 32, y: 32}, pos);
		this.form = new OpenVZDeviceWindow(this);
		this.setAttribute("root_password", "glabroot");
	},
	baseName: function() {
		return "openvz";
	},
	createAnother: function(pos) {
		return new OpenVZDevice(this.editor, this.nextName(), pos);
	},
	createInterface: function(con, fixedName) {
		var iface = new ConfiguredInterface(this.editor, this, con, fixedName);
		this.interfaces.push(iface);
		return iface;
	}
});

var KVMDevice = Device.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/kvm.png", {x: 32, y: 32}, pos);
		this.form = new KVMDeviceWindow(this);
	},
	baseName: function() {
		return "kvm";
	},
	createAnother: function(pos) {
		return new KVMDevice(this.editor, this.nextName(), pos);
	}
});

var ProgDevice = Device.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/prog.png", {x: 32, y: 32}, pos);
		this.form = new ProgDeviceWindow(this);
	},
	baseName: function() {
		return "prog";
	},
	createAnother: function(pos) {
		return new ProgDevice(this.editor, this.nextName(), pos);
	}
});

var Editor = Class.extend({
	init: function(size, editable) {
		this.div = $("#editor");
		this.g = Raphael(this.div[0], size.x, size.y);
		this.editable = editable;
		this.size = size;
		this.paletteWidth = editable ? 60 : 0;
		this.glabColor = "#911A20";
		this.defaultFont = {"font-size":12, "font": "Verdana"};
		this.elements = [];
		this.elementNames = [];
		this.elementNums = {};
		this.hostGroups = [];
		this.templatesOpenVZ = [];
		this.templatesKVM = [];
		this.templatesProg = [];
		this.externalNetworks = {};
		this.nextIPHintNumber = 0;
		this.isLoading = false;
		if (editable) this.paintPalette();
		this.topology = new Topology(this, "Topology", {x: 30+this.paletteWidth, y: 20});
		this.wizardForm = new WizardWindow(this);
		this.paintBackground();
		this.checkBrowser();
		this.busy = false;
	},
	analyze: function() {
		var top = this.topology;
		top.warnings = [];
		top.errors = [];
		//check timeouts
		var now = new Date();
		var stop = new Date(top.getAttribute("stop_timeout"));
		var destroy = new Date(top.getAttribute("destroy_timeout"));
		var remove = new Date(top.getAttribute("remove_timeout"));
		var day = 1000 * 60 * 60 * 24;
		if (stop < now) top.warnings.push("Topology has been stopped at " + top.getAttribute("stop_timeout") + " due to timeout"); 
		else if ((stop-now) < 7 * day) top.warnings.push("Topology will be stopped at " + top.getAttribute("stop_timeout") + " due to timeout");
		if (destroy < now) top.warnings.push("Topology has been destroyed at " + top.getAttribute("destroy_timeout") + " due to timeout"); 
		else if ((destroy-now) < 7 * day) top.warnings.push("Topology will be destroyed at " + top.getAttribute("stop_timeout") + " due to timeout");
		if ((remove-now) < 7 * day) top.warnings.push("Topology will be removed at " + top.getAttribute("stop_timeout") + " due to timeout");
		this.elements.forEach(function(el){
			if (el.paletteItem) return;
			if (el.isDevice) {
				if (el.interfaces.length == 0) top.warnings.push("Connectivity warning: " + el.name + " has no connections"); 
				//check attributes
				if (el.getAttribute("gateway4") && ! pattern.ip4.test(el.getAttribute("gateway4")))
					top.errors.push("Config error: " + el.name + " has an invalid IPv4 gateway address");
				if (el.getAttribute("gateway6") && ! pattern.ip6.test(el.getAttribute("gateway6")))
					top.errors.push("Config error: " + el.name + " has an invalid IPv6 gateway address");
				el.interfaces.forEach(function(iface){
					var con = iface.con.con;
					//check attributes
					if (iface.getAttribute("ip4address") && ! pattern.ip4net.test(iface.getAttribute("ip4address")))
						top.errors.push("Config error: " + el.name + "." + iface.name + " has an invalid IPv4 address/prefix");
					if (iface.getAttribute("ip6address") && ! pattern.ip6net.test(iface.getAttribute("ip6address")))
						top.errors.push("Config error: " + el.name + "." + iface.name + " has an invalid IPv6 address/prefix");
					//check for state mismatch
					var elstate = el.getAttribute("state");
					var constate = con.getAttribute("state");
					if (elstate == "started" && constate != "started") top.warnings.push("Communication problem: " + el.name + " is started but " + con.name + " is " + constate );
				});
			}
			if (el.isConnector) {
				if (el.connections.length == 0) top.warnings.push("Connectivity warning: " + el.name + " has no connections"); 
				el.connections.forEach(function(con){
					//check attributes
					if (con.getAttribute("bandwidth")) {
						var val = con.getAttribute("bandwidth");
						if (! pattern.float.test(val)) top.errors.push("Config error: " + el.name + " <-> " + con.getSubElementName() + " has an invalid bandwidth");
						var val = parseFloat(val);
						if (val > 1000000) top.warnings.push("Config warning: " + el.name + " <-> " + con.getSubElementName() + " has more than 1 Gbit/s bandwidth configured");
						if (val < 10) top.warnings.push("Config warning: " + el.name + " <-> " + con.getSubElementName() + " has less than 10 kbit/s bandwidth configured");
					}
					if (con.getAttribute("delay")) {
						var val = con.getAttribute("delay");
						if (! pattern.float.test(val)) top.errors.push("Config error: " + el.name + " <-> " + con.getSubElementName() + " has an invalid delay");
						var val = parseFloat(val);
						if (val > 10000) top.warnings.push("Config warning: " + el.name + " <-> " + con.getSubElementName() + " has more than 10 seconds delay configured");
						if (val < 0) top.errors.push("Config error: " + el.name + " <-> " + con.getSubElementName() + " has a negative delay configured");
					}
					if (con.getAttribute("lossratio")) {
						var val = con.getAttribute("lossratio");
						if (! pattern.float.test(val)) top.errors.push("Config error: " + el.name + " <-> " + con.getSubElementName() + " has an invalid packet loss ratio");
						var val = parseFloat(val);
						if (val >= 0.9) top.warnings.push("Config warning: " + el.name + " <-> " + con.getSubElementName() + " has more than 90% packet loss configured");
						if (val >= 1.0) top.errors.push("Config warning: " + el.name + " <-> " + con.getSubElementName() + " has 100% or more packet loss configured");
						if (val < 0) top.errors.push("Config error: " + el.name + " <-> " + con.getSubElementName() + " has a negative packet loss ratio configured");
					}
					if (con.getAttribute("gateway4") && ! pattern.ip4net.test(con.getAttribute("gateway4")))
						top.errors.push("Config error: " + el.name + " <-> " + con.getSubElementName() + " has an invalid IPv4 gateway/network address");
					if (con.getAttribute("gateway6") && ! pattern.ip6net.test(con.getAttribute("gateway6")))
						top.errors.push("Config error: " + el.name + " <-> " + con.getSubElementName() + " has an invalid IPv6 gateway/network address");
				});
			}
		});
		top.paintUpdate();
		if (top.warnings.length>0 || top.errors.length>0) {
			top.form.tabs.select("analysis");
			if (! top.poppedUp) top.form.show();
		}
		top.poppedUp = true;			
	},
	checkBrowser: function() {
		if (! $.support.ajax) this.errorMessage("Browser incompatibility", "Your browser does not support ajax, so you will not be able to use this editor.");
	},
	showIframe: function(title, url){
		var div = $('<div style="text-align:center;"/>') ;
		div.append('<iframe src="'+url+'" style="border:0;width:'+(this.size.x-100)+';height:'+(this.size.y-100)+';"/><br/>');
		div.append($('<div>close</div>').button().click(function(){
			msg.dialog("close");
		}));
		var msg = this.infoMessage(title, div);
	},
	_layoutClick: function(event){
		var p = this.parent;
		var div = $("<div/>") ;
		div.append("<p>The editor will automatically layout your topology.<br/>his might take some time, please be patient.</p>");
		div.append($("<div>Begin automatic layout</div>").button().click(function(){
			p.springForceLayout();
			msg.dialog("close");
		}));
		var msg = p.infoMessage("Auto-Layout", div);
	},
	infoMessageBig: function(title, message) {
		var div = $('<div/>').dialog({autoOpen: false, draggable: false, modal: true,
			resizable: false, height:"auto", width:"auto", maxHeight: this.size.y, maxWidth: this.size.x, title: title, 
			position:{my: "center center", at: "center center", of: this.div}});
		div.css({overflow: "scroll", "max-width": this.size.x-100, "max-height": this.size.y-100});
		div.append(message);
		div.dialog("open");
		return div; 
	},
	infoMessage: function(title, message) {
		var div = $('<div/>').dialog({autoOpen: false, draggable: false, modal: true,
			resizable: false, height:"auto", width:"auto", title: title, 
			position:{my: "center center", at: "center center", of: this.div}});
		div.append(message);
		div.dialog("open");
		return div; 
	},
	errorMessage: function(title, message) {
		var div = $('<div/>').dialog({autoOpen: false, draggable: false, modal: true,
			resizable: false, height:"auto", width:"auto", title: title, 
			position:{my: "center center", at: "center center", of: this.div},
			dialogClass: "ui-state-error"});
		div.append(message);
		div.dialog("open");
		return div; 
	},
	followTask: function(task, onSuccess) {
		followTask = {t: this, task: task, onSuccess: onSuccess, closable: false};
		followTask.dialog = this.infoMessage("Task", "");
		followTask.dialog.bind("dialogbeforeclose", function() {return followTask.closable;});
		followTask.progress = $("<div/>");
		followTask.progress.progressbar({value: 0});
		followTask.info = $("<div/>");
		followTask.details = $("<div/>");
		followTask.dialog.append(followTask.info);
		followTask.dialog.append(followTask.progress);
		followTask.dialog.append(followTask.details);
		followTask.update = function() {
			followTask.t._ajax("task/"+followTask.task, null, function(output){
				followTask.dialog.dialog("option", "title", "Task " + output.name);
				followTask.progress.progressbar("value", output.tasks_done*100/output.tasks_total);
				followTask.info.empty();
				followTask.info.append("<b>Status: " + output.status + (output.active ? (" (" +output.tasks_done+"/"+output.tasks_total+")") : "") + "</b><br/>");
				followTask.details.empty();
				followTask.details.append("Started: " + output.started + "<br/>" );
				followTask.details.append("Duration: " + output.duration + "<br/>" );
				if (output.finished) followTask.details.append("Finished: " + output.finished + "<br/>" );
				followTask.details.append($("<a href=/task/"+output.id+" target=_task>View details</a><br/>").button());
				followTask.dialog.dialog("option", "position", {my: "center center", at: "center center", of: followTask.t.div});
				switch (output.status) {
					case "waiting":
					case "running":
					case "reversing":
						window.setTimeout("followTask.update()", 500);
						break;
					case "succeeded":
						followTask.closable = true;
						followTask.dialog.dialog("close");
				 		var fT = followTask;
				 		followTask.t.reloadTopology();
				 		delete followTask;
				 		if (fT.onSuccess) fT.onSuccess();
				 		break;
				 	case "aborted":
				 	case "failed":
						followTask.closable = true;
						followTask.dialog.bind("dialogclose", function(){
							window.location.reload();						
						});
				 		break;
				}
			});			
		};
		followTask.update();
	},
	ajaxModifyBegin: function() {
		if (this.ajaxModifyTransaction) return false;
		this.ajaxModifyTransaction = {mods:[], func:[]};
		return true;
	},
	ajaxModifyCommit: function() {
		if (!this.ajaxModifyTransaction) return false;
		if (this.busy) return false;
		this.ajaxModifyExecute(this.ajaxModifyTransaction);
		delete this.ajaxModifyTransaction;
	},
	_ajax: function(path, data, func) {
		log("AJAX " + path + " " + $.toJSON(data));
		try {
			return $.ajax({type: "POST", url:ajaxpath+path, async: true, data: data, complete: function(res){
				if (res.status == 200) {
					var msg = $.parseJSON(res.responseText);
					if (! msg.success) editor.errorMessage("Request failed", "<p><b>Error message:</b> " + msg.output + "</p><p>This page will be reloaded to refresh the editor.</p>").bind("dialogclose", function(){
						window.location.reload();						
					});
					else func(msg.output);
				} else editor.errorMessage("AJAX request failed", res.statusText);
			}});
		} catch (e) {
			editor.errorMessage("AJAX request failed", e);
		}
	},
	ajaxAction: function(action, func) {
		var data = {"action": $.toJSON(action)};
		var editor = this;
		this._ajax("top/"+topid+"/action", data, func);
	},
	ajaxModifyExecute: function(transaction) {
		var data = {"mods": $.toJSON(transaction.mods)};
		var editor = this;
		if (transaction.mods.length == 0) return;
		log("AJAX MOD SEND: " + transaction.mods.length);
		var func = function(output) {
			for (var i = 0; i < transaction.func.length; i++) transaction.func[i](output);
			log("reloading");
			editor.reloadTopology();
		};
		this.setBusy(true);
		this._ajax("top/"+topid+"/modify", data, func);
	},
	ajaxModify: function(mods, func) {
		if (this.isLoading) return;
		log("AJAX MOD:");
		for (var i = 0; i < mods.length; i++) log(mods[i]);
		if (this.ajaxModifyTransaction) {
			for (var i = 0; i < mods.length; i++) this.ajaxModifyTransaction.mods.push(mods[i]);
			if (func) this.ajaxModifyTransaction.func.push(func);
		} else this.ajaxModifyExecute({mods: mods, func:(func ? [func] : [])});
	},
	setBusy: function(busy) {
		if (this.busy == busy) return;
		this.busy = busy;
		if (busy) this.ajaxModifyBegin(); //topology becomes busy
		else this.ajaxModifyCommit(); //topology becomes unbusy
	},
	setHostGroups: function(groups) {
		this.hostGroups = groups;
	},
	setTemplatesOpenVZ: function(tpls) {
		this.templatesOpenVZ = tpls;
	},
	setTemplatesKVM: function(tpls) {
		this.templatesKVM = tpls;
	},
	setTemplatesProg: function(tpls) {
		this.templatesProg = tpls;
	},
	setExternalNetworks: function(enmap) {
		this.externalNetworks = enmap;
	},
	loadTopology: function() {
		var editor = this;
		this._ajax("top/"+topid+"/info", null, function(top){
			editor._loadTopology(top);
		});
	},
	_loadTopology: function(top) {
		this.isLoading = true;
		var editor = this;
		var dangling_interfaces_mods = [];
		var devices = {};
		var connectors = {};
		var connections = {};
		editor.topology.setAttributes(top.attrs);
		editor.topology.setCapabilities(top.capabilities);
		editor.topology.setResources(top.resources);
		editor.topology.permissions = top.permissions;
		editor.topology.finished_task = top.finished_task;
		this.setBusy(Boolean(top.running_task)); 
		var f = function(obj){
			var attrs = obj.attrs;
			var name = attrs.name;
			var pos = attrs._pos ? attrs._pos.split(",") : [0,0];
			var pos = {x: parseInt(pos[0])+editor.paletteWidth, y: parseInt(pos[1])};
			var type = attrs.type;
			var el;
			switch (type) {
				case "openvz":
					el = new OpenVZDevice(editor, name, pos);
					devices[name] = el;
					break;
				case "kvm": 
					el = new KVMDevice(editor, name, pos);
					devices[name] = el;
					break;
				case "prog": 
					el = new ProgDevice(editor, name, pos);
					devices[name] = el;
					break;
				case "vpn": 
					el = new VPNConnector(editor, name, pos);
					connectors[name] = el;
					break;
				case "external": 
					el = new ExternalConnector(editor, name, pos);
					connectors[name] = el;
					break;
			}
			el.setAttributes(attrs);
			el.setCapabilities(obj.capabilities);
			el.setResources(obj.resources);
		};
		for (var name in top.devices) f(top.devices[name]);
		for (var name in top.connectors) f(top.connectors[name]);
		for (var name in top.connectors) {
			var con = top.connectors[name];
			for (var ifname in con.connections) {
				var c = con.connections[ifname];
				var con_obj = connectors[con.attrs.name];
				var device_obj = devices[ifname.split(".")[0]];
				var c_obj = con_obj.createConnection(device_obj);
				c_obj.setAttributes(c.attrs);
				c_obj.setCapabilities(c.capabilities);
				connections[ifname] = c_obj;
			}
		}
		for (var name in top.devices) {
			var dev = top.devices[name];
			var dev_obj = devices[name];
			for (var ifname in dev.interfaces) {
				var iface = dev.interfaces[ifname];
				var con_obj = connections[name+"."+ifname];
				if (con_obj) {
					var iface_obj = dev_obj.createInterface(con_obj, ifname);
					con_obj.connect(iface_obj);
					iface_obj.setAttributes(iface.attrs);
					iface_obj.setCapabilities(iface.capabilities);
					iface_obj.name = ifname;
				} else dangling_interfaces_mods.push({type: "interface-delete", element: dev_obj.name, subelement: iface.attrs.name, properties: {}});
			}
		}
		this.analyze();
		this.isLoading = false;
		if (dangling_interfaces_mods.length > 0) this.ajaxModify(dangling_interfaces_mods, new function(res){});
		if (top.running_task) this.followTask(top.running_task);
	},
	reloadTopology: function(callback) {
		var editor = this;
		this._ajax("top/"+topid+"/info", null, function(top){
			editor._reloadTopology(top, callback);
		});
	},
	_reloadTopology: function(top, callback) {
		this.isLoading = true;
		this.topology.setAttributes(top.attrs);
		this.topology.setCapabilities(top.capabilities);		
		this.topology.setResources(top.resources);
		this.topology.permissions = top.permissions;
		this.topology.finished_task = top.finished_task;
		this.setBusy(Boolean(top.running_task)); 
		for (var name in top.devices) {
			var dev_obj = this.getElement("device", name);
			var dev = top.devices[name];
			dev_obj.setAttributes(dev.attrs);
			dev_obj.setCapabilities(dev.capabilities);
			dev_obj.setResources(dev.resources);
			for (var ifname in dev.interfaces) {
				var iface_obj = dev_obj.getInterface(ifname);
				var iface = dev.interfaces[ifname];
				iface_obj.setAttributes(iface.attrs);
				iface_obj.setCapabilities(iface.capabilities);
			}
		}
		for (var name in top.connectors) {
			var con_obj = this.getElement("connector", name);
			var con = top.connectors[name];
			con_obj.setAttributes(con.attrs);
			con_obj.setCapabilities(con.capabilities);
			con_obj.setResources(con.resources);
			for (var ifname in con.connections) {				
				var c_obj = con_obj.getConnection(ifname);
				var c = con.connections[ifname];
				c_obj.setAttributes(c.attrs);
				c_obj.setCapabilities(c.capabilities);
			}
		}
		this.analyze();
		this.isLoading = false;
		if (top.running_task) this.followTask(top.running_task);
		if (callback) callback();
	},
	getPosition: function () { 
		var pos = $("#editor").position();
		return {x: pos.left, y: pos.top};
	}, 
	paintPalette: function() {
		this.isLoading = true;
		var y = 25;
		this.g.path("M"+this.paletteWidth+" 0L"+this.paletteWidth+" "+this.g.height).attr({"stroke-width": 2, stroke: this.glabColor});
		this.icon = this.g.image(basepath+"images/glablogo.jpg", 1, 5, this.paletteWidth-6, 79/153*(this.paletteWidth-6));
		this.icon.parent = this;
		this.icon.click(this._iconClick);
		this.wizard = this.g.image(basepath+"images/wizard.png", this.paletteWidth/2-16, (y+=50)-16, 32, 32);
		this.wizardText = this.g.text(this.paletteWidth/2, y+=20, "Wizard");
		if (! isIE) this.wizardText.attr(this.defaultFont);
		this.wizardRect = this.g.rect(this.paletteWidth/2 -24, y-35, 48, 42).attr({fill:"#FFFFFF", opacity:0});
		this.wizardRect.parent = this;
		this.wizardRect.click(this._wizardClick);
		y+=5;
		this.openVZPrototype = new OpenVZDevice(this, "OpenVZ", {x: this.paletteWidth/2, y: y+=50});
		this.openVZPrototype.paletteItem = true;
		this.kvmPrototype = new KVMDevice(this, "KVM", {x: this.paletteWidth/2, y: y+=50});
		this.kvmPrototype.paletteItem = true;
		this.progPrototype = new ProgDevice(this, "Prog", {x: this.paletteWidth/2, y: y+=50});
		this.progPrototype.paletteItem = true;
		y+=40;
		this.externalPrototype = new ExternalConnector(this, "External", {x: this.paletteWidth/2, y: y+=50});
		this.externalPrototype.paletteItem = true;
		this.vpnPrototype = new VPNConnector(this, "VPN", {x: this.paletteWidth/2, y: y+=50});
		this.vpnPrototype.paletteItem = true;

		this.layout = this.g.image(basepath+"images/layout.png", this.paletteWidth/2 -16, this.size.y-100, 32, 32);
		this.layoutText = this.g.text(this.paletteWidth/2, this.size.y-63, "Layout");
		if (! isIE) this.layoutText.attr(this.defaultFont);
		this.layoutRect = this.g.rect(this.paletteWidth/2 -16, this.size.y-100, 32, 42).attr({fill:"#FFFFFF", opacity:0});
		this.layoutRect.parent = this;
		this.layoutRect.click(this._layoutClick);
		this.eraser = this.g.image(basepath+"images/eraser.png", this.paletteWidth/2 -16, this.size.y-50, 32, 32);
		this.eraserText = this.g.text(this.paletteWidth/2, this.size.y-13, "Remove");
		if (! isIE) this.eraserText.attr(this.defaultFont);
		this.eraserRect = this.g.rect(this.paletteWidth/2 -16, this.size.y-50, 32, 42).attr({fill:"#FFFFFF", opacity:0});
		this.eraserRect.parent = this;
		this.eraserRect.click(this._eraserClick);
		this.nextIPHintNumber = 0; //reset to 0
		this.isLoading = false;
		this.help = this.g.image(basepath+"images/help.png", this.size.x-24, 2, 22, 22);
		this.help.parent = this;
		this.help.click(this._helpClick);
	},
	paintBackground: function() {
		this.background = this.g.rect(this.paletteWidth, 0, this.size.x-this.paletteWidth, this.size.y);
		this.background.attr({fill: "#FFFFFF", opacity: 0});
		this.background.toBack();
		this.background.parent = this;
		if (this.editable) this.background.drag(this._dragMove, this._dragStart, this._dragStop);
		this.background.click(this._click);
		this.background.dblclick(this._dblclick);
	},
	_dragMove: function (dx, dy) {
		var p = this.parent;
		p.selectionFrame.attr({x: Math.min(p.opos.x, p.opos.x+dx), y: Math.min(p.opos.y, p.opos.y+dy), width: Math.abs(dx), height: Math.abs(dy)});
	}, 
	_dragStart: function (x, y) {
		var p = this.parent;
		var startPos = p.getPosition();
		p.opos = {x: x - startPos.x, y: y - startPos.y};
		if (p.selectionFrame) p.selectionFrame.remove();
		p.selectionFrame = p.g.rect(p.opos.x, p.opos.y, 0, 0);
		p.selectionFrame.attr({stroke:"#000000", "stroke-dasharray": "- ", "stroke-width": 2});
	},
	_dragStop: function () {
		var p = this.parent;
		var f = p.selectionFrame;
		p.selectAllInArea({x: f.attr("x"), y: f.attr("y"), width: f.attr("width"), height: f.attr("height")});
		if (f.attr("width") > 0 && f.attr("height") > 0) p.lastMoved = new Date();
		p.selectionFrame.remove();
	},
	_click: function(event){
		var p = this.parent;
		if (p.lastMoved && p.lastMoved.getTime() + 100 > new Date().getTime()) return;
		p.unselectAll();
	},
	_dblclick: function(event){
		var p = this.parent;
		p.topology.form.toggle();
	},
	_helpClick: function(event){
		var p = this.parent;
		p.showIframe("Editor help", basepath+"help.html");
	},
	_iconClick: function(event){
		var p = this.parent;
		p.showIframe("Editor info", basepath+"info.html");
	},
	_layoutClick: function(event){
		var p = this.parent;
		var div = $('<div style="text-align:center;"/>') ;
		div.append("<p>The editor will automatically layout your topology.<br/>This might take some time, please be patient.</p>");
		div.append($("<div>Begin automatic layout</div>").button().click(function(){
			p.springForceLayout();
			msg.dialog("close");
		}));
		var msg = p.infoMessage("Automatic Layout", div);
	},
	_eraserClick: function(event){
		var p = this.parent;
		var tr = p.ajaxModifyBegin();
		p.removeSelectedElements();
		if (tr) p.ajaxModifyCommit();
	},
	_wizardClick: function(event){
		var p = this.parent;
		p.wizardForm.toggle();
	},
	connect: function(connector, device, noCheck) {
		if (connector == device) return;
		if (connector.isConnector && device.isDevice) {
			if (device.isConnectedWith(con)) return;
			if (! noCheck && ! connector.checkModifyConnections() ) return;
			if (! noCheck && ! device.checkModifyConnections() ) return;
			var con = connector.createConnection(device);
			var iface = device.createInterface(con);
			con.connect(iface);
		} else if (connector.isDevice && device.isConnector ) this.connect(device, connector);
		else if (connector.isDevice && device.isDevice ) {
			if (! noCheck && ! connector.checkModifyConnections() ) return;
			if (! noCheck && ! device.checkModifyConnections() ) return;
			var middle = {x: (connector.getPos().x + device.getPos().x) / 2, y: (connector.getPos().y + device.getPos().y) / 2}; 
			var con = new VPNConnector(this, this.getNameHint("vpn"), middle);
			this.connect(con, connector, true);
			this.connect(con, device, true);
		} else this.errorMessage("Impossible connection", "Connectors cannot be connected with each others. Simple networks can be built by using only one connector. More complex networks can be built by using a device to do forward/route between the networks.");
	},
	disable: function() {
		this.disableRect = this.g.rect(0, 0, this.size.x,this.size.y).attr({fill:"#FFFFFF", opacity:.8});
	},
	enable: function() {
		if (this.disableRect) this.disableRect.remove();
	},
	selectedElements: function() {
		var sel = [];
		for (var i = 0; i < this.elements.length; i++) if (this.elements[i].isSelected()) sel.push(this.elements[i]);
		return sel;
	},
	unselectAll: function() {
		for (var i = 0; i < this.elements.length; i++) this.elements[i].setSelected(false);
	},
	selectAllInArea: function(area) {
		for (var i = 0; i < this.elements.length; i++) {
			var el = this.elements[i];
			var rect = el.getRect();
			var mid = {x: rect.x+rect.width/2, y: rect.y+rect.height/2};
			var isin = mid.x <= area.x + area.width && mid.x >= area.x && mid.y <= area.y + area.height && mid.y >= area.y;
			el.setSelected(isin);
		}
	},
	getNameHint: function(type) {
		var num = this.elementNums[type];
		if (!num) num = 1;
		while($.inArray(type+num, this.elementNames) >= 0) num++;
		this.elementNums[type]=num;
		return type+num;
	},
	addElement: function(el) {
		this.elements.push(el);
		if (el.name) this.elementNames.push(el.name);
	},
	getElement: function(type, name) {
		for (var i = 0; i < this.elements.length; i++) {
			var el = this.elements[i];
			if (el.getElementType() == type && el.getElementName() == name) return el;
		}
	},
	removeElement: function(el) {
		if (! el.checkRemove()) return;
		this.elements.remove(el);
		if (el.name) this.elementNames.remove(el.name);
	},
	removeSelectedElements: function() {
		var sel = this.selectedElements();
		for (var i = 0; i < sel.length; i++) {
			var el = sel[i];
			if (! el.checkRemove()) continue;
			if (el.isInterface) continue;
			el.remove();
		}
	},
	springForceLayout: function() {
		var damping = 0.7;
		var d = 100;
		var timestep = 0.25;
		var middle = new Vector({x: (this.size.x-this.paletteWidth)/2+this.paletteWidth, y: this.size.y/2});
		var els = [];
		for (var i=0; i<this.elements.length; i++) 
			if((this.elements[i].isDevice || this.elements[i].isConnector) && ! this.elements[i].paletteItem) els.push(this.elements[i]);
		for (var i=0; i<els.length;i++) els[i].velocity = new Vector({x: 0, y: 0});
		var totalForce = 0.0;
		var totalForceChange = 1.0;
		var r = 0;
		var start = new Date();
		while (totalForceChange > 0.001 && start.getTime() + 5000 > new Date().getTime()) {
			totalForceChange = totalForce;
			totalForce = 0.0;
			for (var i=0; i<els.length;i++) {
				var el = els[i];
				var elPos = new Vector(el.pos);
				var force = new Vector({x: 0.0, y: 0.0});
				for (var j=0; j<els.length;j++) if (i!=j) {
					var oPos = new Vector(els[j].pos);
					var path = oPos.clone().sub(elPos);
					var dist = path.length();
					if (dist == 0) continue;
					var dir = path.clone().div(dist);
					force.add(dir.clone().mult(d*d).div(-dist*dist));
					if (el.isConnectedWith(els[j])) force.add(dir.clone().mult(dist-d));
				}
				//force.add(middle.clone().sub(elPos).div(100));
				el.velocity.add(force.clone().mult(timestep)).mult(damping);
				el.move(el.correctPos(elPos.add(el.velocity.clone().mult(timestep)).c));
				totalForce += force.length();
			}
			totalForceChange = Math.abs(totalForce-totalForceChange);
			r++;
		}
		log("auto-layout took " + r + " rounds");
		var tr = this.ajaxModifyBegin();
		for (var i=0; i<els.length;i++) {
			delete els[i].velocity;
			els[i].setAttribute("_pos", (els[i].pos.x-this.paletteWidth)+","+els[i].pos.y);
		}
		if (tr) this.ajaxModifyCommit();
	}
});

var EditElement = Class.extend({
	init: function(name, listener) {
		this.name = name;
		this.changeListener = listener;
	},
	onChanged: function(value) {
		if (this.changeListener) this.changeListener(value, this);
		if (this.form && this.name) this.form.onChanged(this.name, value);
	},
	setValue: function(value) {
	},
	getValue: function() {
	},
	setEditable: function(editable) {
	},
	setForm: function(form) {
		this.form = form;
	},
	getInputElement: function() {
		return null;
	}
});

var TextField = EditElement.extend({
	init: function(name, dflt, listener) {
		this._super(name, listener);
		this.dflt = dflt;
		this.input = $('<input type="text" name="'+name+'" value="'+dflt+'" size=10/>');
		this.input[0].fld = this;
		this.input.change(function (){
			this.fld.onChanged(this.value);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setValue: function(value) {
		this.input[0].value = value;
	},
	getValue: function() {
		return this.input[0].value;
	},
	getInputElement: function() {
		return this.input;
	}
});

var NameField = TextField.extend({
	init: function(obj, listener) {
		this._super("name", obj.name, listener);
	}
});

var MagicTextField = TextField.extend({
	init: function(name, pattern, dflt, listener) {
		this._super(name, dflt, listener);
		this.pattern = pattern;
	},
	onChanged: function(value) {
		this._super(value);
		if (this.pattern.test(this.getValue())) this.input[0].style.color="";
		else this.input[0].style.color="red";
	}
});

var PasswordField = TextField.extend({
	init: function(name, dflt, listener) {
		this._super(name, dflt, listener);
		this.input[0].type = "password";
	}
});

var SelectField = EditElement.extend({
	init: function(name, options, dflt, listener) {
		this._super(name, listener);
		this.options = options;
		this.dflt = dflt;
		this.input = $('<select name="'+name+'"/>');
		this.setOptions(options);
		this.input[0].fld = this;
		this.input.change(function (){
			this.fld.onChanged(this.value);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setOptions: function(options) {
		var val = this.getValue();
		$(this.input).find("option").remove();
		if (options.indexOf(this.dflt) < 0) this.input.append($('<option value="'+this.dflt+'">'+this.dflt+'</option>'));
		for (var i = 0; i < options.length; i++) {
			var option = $('<option value="'+options[i]+'">'+options[i]+'</option>');
			if (options[i] == this.dflt) option.attr({selected: true});
			this.input.append(option);
		}
		if (val) this.setValue(val);
	},
	setValue: function(value) {
		var found = false;
		this.input.find("option").each(function(){
			$(this).attr({selected: false});
			if ( $(this).attr("value") == value ) found = $(this); 		
		});
		if (found) found.attr({selected: true});
		else this.input.append($('<option value="'+value+'" selected>'+value+'</option>'));
	},
	getValue: function() {
		return this.input[0].value;
	},
	getInputElement: function() {
		return this.input;
	}
});

var CheckField = EditElement.extend({
	init: function(name, dflt, listener) {
		this._super(name, listener);
		this.dflt = dflt;
		this.input = $('<input type="checkbox" name="'+name+'"/>');
		if (dflt) this.input.attr({checked: true});
		this.input[0].fld = this;
		this.input.change(function (){
			this.fld.onChanged(this.checked);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setValue: function(value) {
		this.input[0].checked = Boolean.parse(value);
	},
	getValue: function() {
		return this.input[0].checked;
	},
	getInputElement: function() {
		return this.input;
	}
});

var Button = EditElement.extend({
	init: function(name, content, func) {
		this._super(name);
		this.func = func;
		this.input = $('<div>'+content+'</div>');
		this.input.css({"vertical-align": "middle"});
		this.enabled = true;
		var t = this;
		this.input.button().click(function (){
			if (t.enabled) t.func(t);
		});
	},
	setEditable: function(editable) {
		this.input.button("option", "disabled", !editable);
		this.enabled = editable;
	},
	setValue: function(value) {
	},
	getValue: function() {
		return "";
	},
	setContent: function(content) {
		this.input.button('option', 'label', content);
	},
	setFunc: function(func) {
		this.func = func ;
	},
	getInputElement: function() {
		return this.input;
	}
});

var Tabs = Class.extend({
	init: function(listener) {
		this.div = $('<div/>').addClass('ui-tabs ui-widget ui-widget-content ui-corner-all');
		this.button_div = $('<ul/>').addClass('ui-tabs-nav ui-helper-reset ui-helper-clearfix ui-widget-header ui-corner-all');
		this.div.append(this.button_div);
		this.buttons = {};
		this.tabs = {};
		this.selection = null;
		this.listener = listener;
	},
	select: function(name) {
		for (t in this.tabs) {
			if (t == name) {
				this.tabs[t].show();
				this.buttons[t].addClass('ui-tabs-selected ui-state-active');
			} else {
				this.tabs[t].hide();
				this.buttons[t].removeClass('ui-tabs-selected');
				this.buttons[t].removeClass('ui-state-active');
			}
		}
		this.selection = name;
		if (this.listener) this.listener(name);
	},
	_addButton: function(title, name) {
		var t = this;
		var b = $('<li><a>'+title+'</a></li>').click(function(){
			t.select(name);
		}).addClass('ui-state-default ui-corner-top');
		this.buttons[name] = b;
		this.button_div.append(b);
	},
	addTab: function(name, title, div) {
		div.addClass('ui-tabs-panel ui-widget ui-widget-content ui-corner-bottom');
		div.hide();
		this.tabs[name] = div;
		this._addButton(title, name);
		this.div.append(div);
		if (! this.selection) this.select(name);
	},
	delTab: function(name) {
		if (! this.tabs[name]) return;
		this.tabs[name].detach();
		this.buttons[name].remove();
		delete this.tabs[name];
	},
	getSelection: function() {
		return this.selection;
	},
	getTab: function(name) {
		return this.tabs[name];
	},
	getDiv: function() {
		return this.div;
	}
});

var Window = Class.extend({
	init: function(title) {
		this.div = $('<div/>').dialog({autoOpen: false, draggable: false,
			resizable: false, height:"auto", width:"auto", title: title,
			show: "slide", hide: "slide", minHeight:50});
	},
	setTitle: function(title) {
		this.div.dialog("option", "title", title);
	},
	setPosition: function(position) {
		this.div.dialog({position: position});
	},
	show: function(position) {
		if (position) this.setPosition(position);
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

var ElementWindow = Window.extend({
	init: function(obj) {
		this._super(obj.name);
		this.obj = obj;
	},
	show: function() {
		this._super({my: "left top", at: "right top", of: this.obj.getRectObj(), offset: this.obj.getRect().width+5+" 0"});
	}
});

var AttributeForm = Class.extend({
	init: function(obj, div) {
		this.obj = obj;
		if (div) this.div = div;
		else this.div = $('<div/>');
		this.fields = {};
	},
	load: function() {
		for (var name in this.fields) {
			var val = this.obj.attributes[name];
			if (val != null) this.fields[name].setValue(val);
			var editable = this.obj.capabilities
			  && this.obj.capabilities.configure
			  && this.obj.capabilities.configure[name];
			if (name == "name") editable = this.obj.editor.topology && this.obj.editor.topology.capabilities && this.obj.editor.topology.capabilities.modify;
			this.fields[name].setEditable(editable);
		}
	},
	registerField: function(field) {
		field.setForm(this);
		this.fields[field.name]=field;
	},
	unregisterField: function(name) {
		if (this.getField(name)) delete this.fields[name];
	},
	getField: function(name) {
		return this.fields[name];
	},
	onChanged: function(name, value) {
		this.obj.setAttribute(name, value);
	},
	getDiv: function() {
		return this.table;
	}
});

var TableAttributeForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj, $('<table/>').addClass('ui-widget'));
		this.table = this.div;
	}, 
	addRow: function(desc, element) {
		var tr = $('<tr/>');
		tr.append($('<td>'+desc+'</td>'));
		tr.append($('<td/>').append(element));
		this.table.append(tr);
	},
	addField: function(field, desc) {
		this.registerField(field);
		this.addRow(desc, field.getInputElement());
	},
	removeField: function(name) {
		if (this.getField(name)) this.getField(name).getInputElement().remove();
		this.unregisterField(name);
	}
});

var NotesPanel = Class.extend({
	init: function(obj) {
		this.obj = obj;
		this.div = $('<div/>');
	},
	load: function() {
		this.div.empty();
		var t = this;
		var notes = this.obj.getAttribute("_notes", "");
		var textarea = $('<textarea style="width:100%;" rows=20>' + notes + '</textarea>');
		var changed = function(){
			log(textarea[0].value);
			t.obj.setAttribute("_notes", textarea[0].value);
		};
		textarea.change(changed);
		this.div.append(textarea);
		var center = $('<center/>');
		center.append(new Button("save", 'Save', changed).getInputElement());
		this.div.append(center);
	},
	getDiv: function() {
		return this.div;
	}
});

var ControlPanel = Class.extend({
	init: function(obj) {
		this.obj = obj;
		this.div = $('<div/>');
	},
	load: function() {
		this.div.empty();
		var state = this.obj.getAttribute('state');
		var t = this;
		var actionFunc = function(btn) {
			t.obj.stateAction(btn.name);
			t.load();
		};
		var destroyButton = new Button("destroy", '<img src="/static/icons/destroy.png" title="destroy">', actionFunc);
		var prepareButton = new Button("prepare", '<img src="/static/icons/prepare.png" title="prepare">', actionFunc);
		var stopButton = new Button("stop", '<img src="/static/icons/stop.png" title="stop">', actionFunc);
		var startButton = new Button("start", '<img src="/static/icons/start.png" title="start">', actionFunc);
		this.div.append(destroyButton.getInputElement());
		this.div.append(prepareButton.getInputElement());
		this.div.append(stopButton.getInputElement());
		this.div.append(startButton.getInputElement());
		var action = (this.obj.capabilities && this.obj.capabilities.action) ? this.obj.capabilities.action : {};
		destroyButton.setEditable(action.destroy);
		prepareButton.setEditable(action.prepare);
		stopButton.setEditable(action.stop);
		startButton.setEditable(action.start);
		if (! this.obj.isTopology) this.div.append('<p>State: ' + state + '</p>');
	},
	getDiv: function() {
		return this.div;
	}
});

var TopologyControlPanel = ControlPanel.extend({
	load: function() {
		this._super();
		var t = this;
		var attrs = this.obj.attributes;
		this.div.append('<p>Owner: '+attrs.owner+'</p>');
		if (this.obj.finished_task) this.div.append($("<a href=/task/"+this.obj.finished_task+" target=_task>Show last task</a><br/>").button());
	}	
});

var DeviceControlPanel = ControlPanel.extend({
	load: function() {
		this._super();
		var t = this;
		this.div.append('<p>Host: '+this.obj.attributes.host+'</p>');
		if (this.obj.consoleSupported()) {
			this.div.append(new Button("console", '<img src="'+basepath+'images/console.png"> open console', function(){
				t.obj.showConsole();
			}).getInputElement());
			this.div.append(new Button("vncinfo", 'VNC info', function(){
				t.obj.showVNCinfo();
			}).getInputElement());
		}
		if (this.obj.downloadSupported()) {
			this.div.append(this.downloadButton = new Button("download", 'Prepare image download', function(btn){
				t.obj.downloadImage(btn);
			}).getInputElement());
		}
		if (this.obj.uploadSupported()) {
			this.div.append(new Button("upload", 'Upload image', function(){
				t.obj.uploadImage();
			}).getInputElement());
		}
	}	
});

var ConnectorControlPanel = ControlPanel.extend({
	load: function() {
		this._super();
		var t = this;
		if (this.obj.externalAccessSupported()) {
			this.div.append(new Button("external_access_info", 'External access info', function(){
				t.obj.showExternalAccessInfo();
			}).getInputElement());
		}
	}	
});

var ResourcesPanel = Class.extend({
	init: function(obj) {
		this.obj = obj;
		this.div = $('<div/>');
	},
	load: function() {
		this.div.empty();
		var res = this.obj.resources;
		var t = this;
		var table = $('<table/>');
		if (res) {
			if (res.disk) table.append($('<tr><td>Disk space:</td><td>'+formatSize(res.disk)+'</td></tr>'));
			if (res.memory) table.append($('<tr><td>Memory:</td><td>'+formatSize(res.memory)+'</td></tr>'));
			if (res.traffic) table.append($('<tr><td>Traffic:</td><td>'+formatSize(res.traffic)+'</td></tr>'));
			if (res.external) table.append($('<tr><td>External slots:</td><td>'+res.external+'</td></tr>'));
			if (res.ports) table.append($('<tr><td>Ports:</td><td>'+res.ports+'</td></tr>'));
		}
		this.div.append(table);
	},
	getDiv: function() {
		return this.div;
	}
});

var AnalysisPanel = Class.extend({
	init: function(obj) {
		this.obj = obj;
		this.div = $('<div/>');
	},
	load: function() {
		this.div.empty();
		var t = this;
		var ul = $('<ul class="none">');
		for (var i = 0; i < this.obj.errors.length; i++) ul.append('<li class="error">'+this.obj.errors[i]+'</li>');
		for (var i = 0; i < this.obj.warnings.length; i++) ul.append('<li class="warning">'+this.obj.warnings[i]+'</li>');
		this.div.append((this.obj.errors == 0 && this.obj.warnings == 0) ? "<p>No errors or warnings</p>" : ul);
		this.div.append(new Button("check", 'Run again', function(){
			t.obj.editor.analyze();
			t.load();
		}).getInputElement());
	},
	getDiv: function() {
		return this.div;
	}
});

var PermissionsPanel = Class.extend({
	init: function(obj) {
		this.obj = obj;
		this.div = $('<div/>');
	},
	load: function() {
		this.div.empty();
		var t = this;
		var permissions = this.obj.permissions;
		var editable = this.obj.capabilities && this.obj.capabilities.permission_set;
		var table = $('<table><tr><th>User</th><th>Role</th><th>Actions</th></tr></table>');
		for (user in permissions) {
			var role = permissions[user];
			if (role == "owner" || ! editable) table.append(table_row([user, "<b>owner</b", ""]));
			else table.append(table_row([user, new SelectField(user, ["manager", "user"], role, function(role, select){
				t.obj.setPermission(select.name, role);
			}).getInputElement(), new Button(user, '<img src="'+basepath+'/images/user_delete.png"/>', function(btn){
				t.obj.setPermission(btn.name, null);
			}).getInputElement()]));
		}
		if (editable) {
			var user_input = new TextField("user", "");
			var role_input = new SelectField("role", ["manager", "user"], "user");
			table.append(table_row([user_input.getInputElement(), role_input.getInputElement(), new Button("add", '<img src="'+basepath+'/images/user_add.png"/>', function() {
				t.obj.setPermission(user_input.getValue(), role_input.getValue());
			}).getInputElement()]));
		}
		this.div.append(table);
	},
	getDiv: function() {
		return this.div;
	}
});

var TopologyWindow = ElementWindow.extend({
	init: function(obj) {
		this._super(obj);
		var t = this;
		this.tabs = new Tabs(function(name) {
			t.reload();
		});
		this.add(this.tabs.getDiv());
		this.attrs = new TableAttributeForm(obj);
		this.attrs.addField(new TextField("name", "Topology"), "name");
		this.tabs.addTab("attributes", "Attributes", this.attrs.getDiv());
		this.control = new TopologyControlPanel(obj);
		this.tabs.addTab("control", "Control", this.control.getDiv());
		this.resources = new ResourcesPanel(obj);
		this.tabs.addTab("resources", "Resources", this.resources.getDiv());
		this.permissions = new PermissionsPanel(obj);
		this.tabs.addTab("permissions", "Permissions", this.permissions.getDiv());
		this.analysis = new AnalysisPanel(obj);
		this.tabs.addTab("analysis", "Analysis", this.analysis.getDiv());
		this.notes = new NotesPanel(obj);
		this.tabs.addTab("notes", "Notes", this.notes.getDiv());
		this.tabs.select(this.obj.editor.editable ? "attributes" : "control");
	},
	reload: function() {
		if (this.control) this.control.load();
		if (this.resources) this.resources.load();
		if (this.attrs) this.attrs.load();
		if (this.permissions) this.permissions.load();
		if (this.analysis) this.analysis.load();
		if (this.notes) this.notes.load();
	},
	show: function() {
		if (this.obj.errors.length>0) this.tabs.select("analysis");
		this.reload();
		this._super();
	}
});

var DeviceWindow = ElementWindow.extend({
	init: function(obj) {
		this._super(obj);
		var t = this;
		this.tabs = new Tabs(function(name) {
			t.reload();
		});
		this.add(this.tabs.getDiv());
		this.attrs = new TableAttributeForm(obj);
		this.attrs.addField(new NameField(obj, function(name){
			t.setTitle(name);
		}), "name");
		this.attrs.addField(new SelectField("hostgroup", this.obj.editor.hostGroups, "auto"), "hostgroup");
		this.tabs.addTab("attributes", "Attributes", this.attrs.getDiv());
		this.control = new DeviceControlPanel(obj);
		this.tabs.addTab("control", "Control", this.control.getDiv());
		this.resources = new ResourcesPanel(obj);
		this.tabs.addTab("resources", "Resources", this.resources.getDiv());
		this.notes = new NotesPanel(obj);
		this.tabs.addTab("notes", "Notes", this.notes.getDiv());
		this.tabs.select(this.obj.editor.editable ? "attributes" : "control");
	},
	reload: function() {
		if (this.control) this.control.load();
		if (this.resources) this.resources.load();
		if (this.attrs) this.attrs.load();
		if (this.notes) this.notes.load();
	},
	show: function() {
		this.reload();
		this._super();
	}
});

var OpenVZDeviceWindow = DeviceWindow.extend({
	init: function(obj) {
		this._super(obj);
		this.attrs.addField(new SelectField("template", this.obj.editor.templatesOpenVZ, "auto"), "template");
		this.attrs.addField(new TextField("root_password", ""), "root&nbsp;password");
		this.attrs.addField(new MagicTextField("gateway4", pattern.ip4, ""), "gateway4");
		this.attrs.addField(new MagicTextField("gateway6", pattern.ip6, ""), "gateway6");
	}
});

var KVMDeviceWindow = DeviceWindow.extend({
	init: function(obj) {
		this._super(obj);
		this.attrs.addField(new SelectField("template", this.obj.editor.templatesKVM, "auto"), "template");
	}	
});

var ProgDeviceWindow = DeviceWindow.extend({
	init: function(obj) {
		this._super(obj);
		this.attrs.addField(new SelectField("template", this.obj.editor.templatesProg, "auto"), "template");
		this.attrs.addField(new TextField("args", ""), "arguments");
	}	
});

var ConnectorWindow = ElementWindow.extend({
	init: function(obj) {
		this._super(obj);
		var t = this;
		this.tabs = new Tabs(function(name) {
			t.reload();
		});
		this.add(this.tabs.getDiv());
		this.attrs = new TableAttributeForm(obj);
		this.attrs.addField(new NameField(obj, function(name){
			t.setTitle(name);
		}), "name");
		this.tabs.addTab("attributes", "Attributes", this.attrs.getDiv());
		this.control = new ConnectorControlPanel(obj);
		this.tabs.addTab("control", "Control", this.control.getDiv());
		this.resources = new ResourcesPanel(obj);
		this.tabs.addTab("resources", "Resources", this.resources.getDiv());
		this.notes = new NotesPanel(obj);
		this.tabs.addTab("notes", "Notes", this.notes.getDiv());
		this.tabs.select(this.obj.editor.editable ? "attributes" : "control");
	},
	reload: function() {
		if (this.control) this.control.load();
		if (this.resources) this.resources.load();
		if (this.attrs) this.attrs.load();
		if (this.notes) this.notes.load();
	},
	show: function() {
		this.reload();
		this._super();
	}
});

var ExternalConnectorWindow = ConnectorWindow.extend({
	init: function(obj) {
		this._super(obj);
		var t = this;
		this.attrs.addField(new SelectField("network_type", getKeys(this.obj.editor.externalNetworks), "", function(value) {
			t._typeChanged(value);
		}), "type");
		this.attrs.addField(new SelectField("network_group", [], "auto"), "group");
	},
	_typeChanged: function(value) {
		var group = this.attrs.fields.network_group;
		var options = this.obj.editor.externalNetworks[value];
		if (!options) options = [];
		group.setOptions(options);
	},
	show: function() {
		this._super();
		this._typeChanged();
	}
});

var VPNConnectorWindow = ConnectorWindow.extend({
	init: function(obj) {
		this._super(obj);
		this.attrs.addField(new SelectField("mode", ["hub", "switch", "router"], "switch"), "mode");
		this.attrs.addField(new CheckField("external_access"), "external&nbsp;access");
	}
});

var InterfaceWindow = ElementWindow.extend({
	init: function(obj) {
		this._super(obj);
		this.attrs = new TableAttributeForm(obj);
		this.attrs.addField(new NameField(obj), "name");
		this.add(this.attrs.getDiv());
	},
	show: function() {
		this.attrs.load();
		this._super();
	}
});

var ConfiguredInterfaceWindow = InterfaceWindow.extend({
	init: function(obj) {
		this._super(obj);
		this.attrs.addField(new CheckField("use_dhcp", false), "use&nbsp;dhcp");
		this.attrs.addField(new MagicTextField("ip4address", pattern.ip4net, ""), "ip4/prefix");		
		this.attrs.addField(new MagicTextField("ip6address", pattern.ip6net, ""), "ip6/prefix");		
	}
});

var ConnectionWindow = ElementWindow.extend({});

var EmulatedConnectionWindow = ConnectionWindow.extend({
	init: function(obj) {
		this._super(obj);
		this.attrs = new TableAttributeForm(obj);
		this.tabs = new Tabs();
		var fields = {};
		//link emulation
		this.le = $("<table/>").addClass('ui-widget');
		this.le.append(table_row(["", "<b>To connector</b>", "<b>From connector</b>", ""]));
		fields.bandwidth_to = new MagicTextField("bandwidth_to", pattern.float, "");
		fields.bandwidth_from = new MagicTextField("bandwidth_from", pattern.float, "");
		this.le.append(table_row(["bandwidth", fields.bandwidth_to.getInputElement(), fields.bandwidth_from.getInputElement(), "kbit/s"]));
		fields.delay_to = new MagicTextField("delay_to", pattern.float, "");
		fields.delay_from = new MagicTextField("delay_from", pattern.float, "");
		this.le.append(table_row(["delay", fields.delay_to.getInputElement(), fields.delay_from.getInputElement(), "ms"]));
		fields.jitter_to = new MagicTextField("jitter_to", pattern.float, "");
		fields.jitter_from = new MagicTextField("jitter_from", pattern.float, "");
		this.le.append(table_row(["jitter", fields.jitter_to.getInputElement(), fields.jitter_from.getInputElement(), "ms"]));
		//disabled because delay correlation is broken in netem
		//fields.delay_correlation_to = new MagicTextField("delay_correlation_to", pattern.float, "")
		//fields.delay_correlation_from = new MagicTextField("delay_correlation_from", pattern.float, "")
		//this.le.append(table_row(["delay&nbsp;correlation", fields.delay_correlation_to.getInputElement(), fields.delay_correlation_from.getInputElement(), "%"]))
		fields.distribution_to = new SelectField("distribution_to", ["uniform", "normal", "pareto", "paretonormal"], "uniform");
		fields.distribution_from = new SelectField("distribution_from", ["uniform", "normal", "pareto", "paretonormal"], "uniform");
		this.le.append(table_row(["delay&nbsp;distribution", fields.distribution_to.getInputElement(), fields.distribution_from.getInputElement(), ""]));
		fields.lossratio_to = new MagicTextField("lossratio_to", pattern.float, "");
		fields.lossratio_from = new MagicTextField("lossratio_from", pattern.float, "");
		this.le.append(table_row(["packet&nbsp;loss", fields.lossratio_to.getInputElement(), fields.lossratio_from.getInputElement(), "%"]));
		fields.lossratio_correlation_to = new MagicTextField("lossratio_correlation_to", pattern.float, "");
		fields.lossratio_correlation_from = new MagicTextField("lossratio_correlation_from", pattern.float, "");
		this.le.append(table_row(["loss&nbsp;correlation", fields.lossratio_correlation_to.getInputElement(), fields.lossratio_correlation_from.getInputElement(), "%"]));
		fields.duplicate_to = new MagicTextField("duplicate_to", pattern.float, "");
		fields.duplicate_from = new MagicTextField("duplicate_from", pattern.float, "");
		this.le.append(table_row(["duplication", fields.duplicate_to.getInputElement(), fields.duplicate_from.getInputElement(), "%"]));
		fields.corrupt_to = new MagicTextField("corrupt_to", pattern.float, "");
		fields.corrupt_from = new MagicTextField("corrupt_from", pattern.float, "");
		this.le.append(table_row(["corrupt&nbsp;packets", fields.corrupt_to.getInputElement(), fields.corrupt_from.getInputElement(), "%"]));
		this.tabs.addTab("link_emulation", "Link emulation", this.le);
		//packet capturing
		this.pc = $("<table/>").addClass('ui-widget');
		var t = this;
		this.captureField = new SelectField("", ["disabled", "to file", "via network"], "disabled", function(value){
			e = t.obj.editor;
			var tr = e.ajaxModifyBegin();
			t.obj.setAttribute("capture_to_file", value == "to file");
			t.obj.setAttribute("capture_via_net", value == "via network");
			if (tr) e.ajaxModifyCommit();
			t.attrs.fields["capture_filter"].setEditable(value!="disabled");
		});		
		this.attrs.registerField(this.captureField);
		this.captureFilterField = new TextField("capture_filter", "");
		this.attrs.registerField(this.captureFilterField);
		this.tabs.addTab("packet_capturing", "Packet capturing", this.pc);
		for (var f in fields) this.attrs.registerField(fields[f]);
		this.add(this.tabs.getDiv());
		//routing
		this.routing = $("<table/>").addClass('ui-widget');
		var fields = {};
		fields.gateway4 = new MagicTextField("gateway4", pattern.ip4net, "");
		this.attrs.registerField(fields.gateway4);
		this.routing.append(table_row(["gateway&nbsp;(ip4/prefix)", fields.gateway4.getInputElement()]));
		fields.gateway6 = new MagicTextField("gateway6", pattern.ip6net, "");
		this.attrs.registerField(fields.gateway6);
		this.routing.append(table_row(["gateway&nbsp;(ip6/prefix)", fields.gateway6.getInputElement()]));
	},
	show: function() {
		this.attrs.load();
		this.captureField.setEditable(true);
		if (Boolean.parse(this.obj.getAttribute("capture_to_file", "false")))
			this.captureField.setValue("to file");
		if (Boolean.parse(this.obj.getAttribute("capture_via_net", "false")))
			this.captureField.setValue("via network");
		this.pc.empty();
		this.pc.append(table_row(["capture&nbsp;packets", this.captureField.getInputElement()]));
		this.pc.append(table_row(["capture&nbsp;filter", this.captureFilterField.getInputElement()]));
		var t = this;
		if (this.obj.downloadSupported()) {
			this.pc.append(table_row([new Button("download", "Prepare capture download", function(btn){
				t.obj.downloadCapture(btn);
			}).getInputElement(), new Button("cloudshark", '<img height="40%" src="'+basepath+'/images/cloudshark.png"/>', function(btn){
				t.obj.viewCapture(btn);
			}).getInputElement()]));
		}
		if (this.obj.liveCaptureSupported()) {
			this.pc.append(table_row(["", new Button("livecapture", "live capture info", function(btn){
				t.obj.showLiveCaptureInfo();
			}).getInputElement()]));
		}
		var sel = this.tabs.getSelection();
		this.tabs.delTab("routing");
		if (this.obj.con.isRouted()) this.tabs.addTab("routing", "Routing", this.routing);
		this.tabs.select(sel);
		this._super();
	}
});

var WizardWindow = Window.extend({
	init: function(editor) {
		this.editor = editor;
		this.div = $('<div/>').dialog({autoOpen: false, draggable: false,
			resizable: false, height:"auto", width:"auto", title: "Topology Wizard",
			show: "slide", hide: "slide", position:{my: "center center", at: "center center", of: editor.div}});
		this.table = $('<table/>').attr({"class": "ui-widget"});
		this.div.append(this.table);
		this.fields = {};
		this.addField(new SelectField("type", ["Star", "Ring", "Full mesh", "Star around host", "Loose nodes"], "Star"), "Topology type");		
		this.addField(new MagicTextField("number", /^\d+$/, "5"), "Number of nodes");
		this.addField(new SelectField("device_type", ["OpenVZ", "KVM"], "OpenVZ"), "Device type");		
		this.addField(new SelectField("hostgroup", this.editor.hostGroups, "auto"), "Device hostgroup");
		this.addField(new SelectField("template", this.editor.templatesOpenVZ, "auto"), "Device template");		
		this.addField(new TextField("root_password", "glabroot"), "Root&nbsp;password");
		this.addField(new CheckField("internet", false), "Additional internet connection");
		this.addMultipleFields([new Button("create", "create", function(btn){
			btn.form.hide();
			btn.form._createClicked();
		})]);
	},
	create: function(nodes, region) {
		var tr = this.editor.ajaxModifyBegin();
		var middle = {x: region.x+region.width/2, y: region.y+region.height/2};
		var radius = {x: region.width/2, y: region.height/2};
		if (nodes.length == 0) {
			var number = this.fields.number.getValue();
			for (var i=0; i<number; i++) {
				var pos = {x: middle.x - Math.cos((i/number) * 2 * Math.PI - Math.PI / 2) * radius.x,
						   y: middle.y - Math.sin((i/number) * 2 * Math.PI - Math.PI / 2) * radius.y};
				switch (this.fields.device_type.getValue()) {
					case "OpenVZ":
						nodes[i] = new OpenVZDevice(this.editor, this.editor.getNameHint("openvz"), pos);
						nodes[i].setAttribute("root_password", this.fields.root_password.getValue());
						break;
					case "KVM":
						nodes[i] = new KVMDevice(this.editor, this.editor.getNameHint("kvm"), pos);
						break;
				}
				nodes[i].setAttribute("template", this.fields.template.getValue());
				nodes[i].setAttribute("hostgroup", this.fields.hostgroup.getValue());
			}
		}
		if (nodes.length > 1) {
			switch (this.fields.type.getValue()) {
				case "Star":
					var sw = new SwitchConnector(this.editor, this.editor.getNameHint("switch"), middle);
					for (var i=0; i<nodes.length; i++) this.editor.connect(sw, nodes[i]);
					break;
				case "Ring":
					for (var i=0; i<nodes.length; i++) this.editor.connect(nodes[i], nodes[(i+1)%nodes.length]);
					break;
				case "Full mesh":
					for (var i=0; i<nodes.length; i++) for (var j=i+1; j<nodes.length; j++) this.editor.connect(nodes[i], nodes[j]);
					break;
				case "Star around host":
					var nd = new KVMDevice(this.editor, this.editor.getNameHint("kvm"), middle);
					for (var i=0; i<nodes.length; i++) this.editor.connect(nd, nodes[i]);
					break;				
				case "Loose nodes":
					break;
			}
		}
		if (this.fields.internet.getValue()) {
			var internet = new ExternalConnector(this.editor, this.editor.getNameHint("internet"), {x: middle.x+50, y: middle.y+25});
			internet.setAttribute("type", "internet");
			for (var i=0; i<number; i++) this.editor.connect(internet, nodes[i]);
		}
		if (tr) this.editor.ajaxModifyCommit();
	},
	_createClicked: function() {
		var nodes = [];
		var selectedElements = this.editor.selectedElements();
		if (selectedElements.length > 0) {
			for (var i=0; i<selectedElements.length; i++) if(selectedElements[i].isDevice) nodes.push(selectedElements[i]);
			var rect = compoundBBox(nodes);
			this.create(nodes, rect);
		} else {
			var t = this;
			var container = $("<div/>");
			container.attr({style: "position: absolute;"});
			container.width(this.editor.size.x-this.editor.paletteWidth);
			container.height(this.editor.size.y);
			this.editor.div.append(container);
			container.position({my: "right top", at: "right top", of: $(this.editor.div), collision: "none"});
			var div = $("<div/>");
			div.attr({style: "border: 1px dashed black; text-align: center;"});
			div.resizable({containment: container, minWidth: 175, minHeight: 175}).draggable({containment: container});
			div.append("<p>Please select the region for the new topology, by positioning and resizing this frame.</p>");
			div.append($("<div>Create topology</div>").button().click(function(){
				var region = {};
				var offset = div.offset();
				region.x = offset.left - t.editor.getPosition().x + 20;
				region.y = offset.top - t.editor.getPosition().y + 20;
				region.width = div.width() - 40 ;
				region.height = div.height() - 40 ;
				container.remove();
				t.create([], region);
			}));
			div.append($("<div>cancel</div>").button().click(function(){
				container.remove();
			}));
			div.width(this.editor.size.x-this.editor.paletteWidth-50);
			div.height(this.editor.size.y-50);
			container.append(div);
			div.position({my: "center center", at: "center center", of: container});
		}
	},
	show: function() {
		var selNum = this.editor.selectedElements().length;
		var sel = selNum > 0;
		this.fields.number.setEditable(!sel);
		if (sel) this.fields.number.setValue(selNum);
		this.fields.device_type.setEditable(!sel);
		this.fields.root_password.setEditable(!sel);
		this._onTypeChange();
		this.fields.template.setEditable(!sel);
		this.fields.hostgroup.setOptions(this.editor.hostGroups);
		this.div.dialog("open");
	},
	_onTypeChange: function() {
		switch (this.fields.device_type.getValue()) {
			case "OpenVZ":
				this.fields.template.setOptions(this.editor.templatesOpenVZ);
				break;
			case "KVM":
				this.fields.template.setOptions(this.editor.templatesKVM);
				break;
		}
	},
	hide: function() {
		this.div.dialog("close");
	},
	toggle: function() {
		if (this.div.dialog("isOpen")) this.hide();
		else this.show();
	},
	addField: function(field, desc) {
		field.setForm(this);
		var tr = $('<tr/>');
		tr.append($('<td>'+desc+'</td>'));
		tr.append($('<td/>').append(field.getInputElement()));
		this.table.append(tr);
		this.fields[field.name]=field;
	},
	addMultipleFields: function(fields) {
		var tr = $('<tr/>');
		var td = $('<td/>');
		td.attr({colspan: "2", align: "center"});
		for (var i = 0; i < fields.length; i++) {
			var field = fields[i];
			field.setForm(this);
			this.fields[field.name]=field;
			td.append(field.getInputElement());
		}
		tr.append(td);
		this.table.append(tr);
	},
	onChanged: function(name, value) {
		if (name == "device_type" ) this._onTypeChange();
	}
});

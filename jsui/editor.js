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
 * - IE8 does not correctly support transparecy in svg but transparent images can
 * 	 be used
 ********************************************************************************/ 

var NetElement = Class.extend({
	init: function(editor){
		this.editor = editor;
		this.selected = false;
		this.editor.addElement(this);
		this.attributes = {};
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
	setAttribute: function(name, value) {
		this.attributes[name]=value;
		var attr = {};
		attr[name]=value;
		this.editor.ajaxModify([this.modification("configure", attr)]);
	},
	getAttribute: function(name) {
		return this.attributes[name];
	},
	setAttributes: function(attrs) {
		for (var key in attrs) this.setAttribute(key, attrs[key]);
	},
	getElementType: function() {
		return "";
	},
	getElementName: function() {
		return "";
	},
	getSubElementName: function() {
		return "";
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
				p.setAttribute("pos", (p.pos.x-p.editor.paletteWidth)+","+p.pos.y);
			} else for (var i = 0; i < sel.length; i++) if(sel[i].isDevice || sel[i].isConnector) {
				sel[i].move(sel[i].correctPos(sel[i].pos));
				sel[i].lastMoved = new Date();
				sel[i].setAttribute("pos", (sel[i].pos.x-sel[i].editor.paletteWidth)+","+sel[i].pos.y);
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
		this._super(name, value);
		if (name == "name") {
			this.editor.elementNames.remove(this.name);
			this.editor.ajaxModify([this.modification("rename", {name: value})], function(res) {});
			this.name = value;
			this.paintUpdate();
			this.editor.elementNames.push(value);
		} else if (name == "state") {
			switch (value) {
				case "started":
				case "prepared":
					this.stateIcon.attr({src: basepath+"images/"+value+".png"});
					this.stateIcon.attr({opacity: 1.0});
					break;
				default:
					this.stateIcon.attr({src: basepath+"images/pixel.png", opacity: 0.0});
			}
		}
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
		this.form = new TopologyForm(this);
	},
	setAttribute: function(name, value) {
		//ignore name changes
		this.attributes[name]=value;
		if (name == "name") this.editor.ajaxModify([this.modification("rename", {name: value})], function(res) {});
	},
	_dragStart: function () {
	},
	_dragMove: function (dx, dy) {
	},
	_dragStop: function () {
	},
	getElementType: function () {
		return "topology";
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
		this.form = new ConnectionForm(this);		
	},
	connect: function(iface) {
		this.iface = iface;
		this.editor.ajaxModify([this.modification("create", {"interface": this.getSubElementName()})], function(res) {});
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
		this.form = new EmulatedConnectionForm(this);
		this.IPHintNumber = this.con.nextIPHintNumber++;
	},
	getIPHint: function() {
		return "10."+this.con.IPHintNumber+".0."+this.IPHintNumber+"/24";
	}	
});

var EmulatedRouterConnection = EmulatedConnection.extend({
	init: function(editor, dev, con){
		this._super(editor, dev, con);
		this.form = new EmulatedRouterConnectionForm(this);
		this.setAttribute("gateway", "10."+this.con.IPHintNumber+"."+this.IPHintNumber+".254/24");
	},
	getIPHint: function() {
		return "10."+this.con.IPHintNumber+"."+this.IPHintNumber+".1/24";
	}	
});

var Interface = NetElement.extend({
	init: function(editor, dev, con){
		this._super(editor);
		this.dev = dev;
		this.con = con;
		this.paint();
		this.isInterface = true;
		this.name = "eth" + dev.interfaces.length;
		this.form = new InterfaceForm(this);
		this.editor.ajaxModify([this.modification("create", {name: this.name})], function(res) {});
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
	init: function(editor, dev, con){
		this._super(editor, dev, con);
		this.form = new ConfiguredInterfaceForm(this);
		var ipHint = con.getIPHint();
		this.setAttribute("use_dhcp", ipHint == "dhcp");
		if (ipHint != "dhcp" ) this.setAttribute("ip4address", ipHint);
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
		this.editor.ajaxModify([this.modification("create", {type: this.baseName(), pos:(pos.x-editor.paletteWidth)+","+pos.y, name: name})], function(res) {});
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
				if (el.isDevice && !this.isConnectedWith(el)) this.editor.connect(this, el);
			}
			if (tr) this.editor.ajaxModifyCommit();
		} else this._super(event);
	},
	isConnectedWith: function(dev) {
		for (var i = 0; i < this.connections.length; i++) if (this.connections[i].dev == dev) return true;
		return false;
	},
	createConnection: function(dev) {
		var con = new Connection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	},
	removeConnection: function(con) {
		this.connections.remove(con);
	}
});

var SpecialConnector = Connector.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/special.png", {x: 32, y: 32}, pos);
		this.form = new SpecialConnectorForm(this);
	},
	nextIPHint: function() {
		return "dhcp";
	},
	setAttribute: function(name, value) {
		this._super(name, value);
		if (name == "feature_type") {
			if (value=="openflow" || value=="internet") this.iconsrc="images/"+value+".png";
			else this.iconsrc="images/special.png";
			this.paintUpdate();
		}
	},
	baseName: function() {
		return "special";
	},
	createAnother: function(pos) {
		return new SpecialConnector(this.editor, this.nextName(), pos);
	}
});

var HubConnector = Connector.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/hub.png", {x: 32, y: 16}, pos);
		this.form = new HubConnectorForm(this);
	},
	baseName: function() {
		return "hub";
	},
	createAnother: function(pos) {
		return new HubConnector(this.editor, this.nextName(), pos);
	},
	createConnection: function(dev) {
		var con = new EmulatedConnection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	}
});

var SwitchConnector = Connector.extend({
	init: function(editor, name, pos) {
		if (!pos) { //called with 2 parameters
			pos = name;
			name = this.nextName();
		}
		this._super(editor, name, "images/switch.png", {x: 32, y: 16}, pos);
		this.form = new SwitchConnectorForm(this);
	},
	baseName: function() {
		return "switch";
	},
	createAnother: function(pos) {
		return new SwitchConnector(this.editor, this.nextName(), pos);
	},
	createConnection: function(dev) {
		var con = new EmulatedConnection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	}
});

var RouterConnector = Connector.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/router.png", {x: 32, y: 16}, pos);
		this.form = new RouterConnectorForm(this);
	},
	nextIPHint: function() {
		return "10."+this.IPHintNumber+"."+(this.nextIPHintNumber++)+".1/24";
	},
	baseName: function() {
		return "router";
	},
	createAnother: function(pos) {
		return new RouterConnector(this.editor, this.nextName(), pos);
	},
	createConnection: function(dev) {
		var con = new EmulatedRouterConnection(this.editor, this, dev);
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
		this.editor.ajaxModify([this.modification("create", {type: this.baseName(), pos:(pos.x-editor.paletteWidth)+","+pos.y, name: name})], function(res) {});
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
				if (el.isConnector && !this.isConnectedWith(el)) this.editor.connect(el, this);
				if (el.isDevice && el != this) this.editor.connect(el, this);
			}
			if (tr) this.editor.ajaxModifyCommit();
		} else this._super(event);
	},
	isConnectedWith: function(con) {
		for (var i = 0; i < this.interfaces.length; i++) if (this.interfaces[i].con.con == con) return true;
		return false;
	},
	createInterface: function(con) {
		var iface = new Interface(this.editor, this, con);
		this.interfaces.push(iface);
		return iface;
	},
	removeInterface: function(iface) {
		this.interfaces.remove(iface);
	}
});

var OpenVZDevice = Device.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/openvz.png", {x: 32, y: 32}, pos);
		this.form = new OpenVZDeviceForm(this);
	},
	baseName: function() {
		return "openvz";
	},
	createAnother: function(pos) {
		return new OpenVZDevice(this.editor, this.nextName(), pos);
	},
	createInterface: function(con) {
		var iface = new ConfiguredInterface(this.editor, this, con);
		this.interfaces.push(iface);
		return iface;
	}
});

var KVMDevice = Device.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/kvm.png", {x: 32, y: 32}, pos);
		this.form = new KVMDeviceForm(this);
	},
	baseName: function() {
		return "kvm";
	},
	createAnother: function(pos) {
		return new KVMDevice(this.editor, this.nextName(), pos);
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
		this.specialFeatures = {};
		this.nextIPHintNumber = 0;
		this.isLoading = false;
		if (editable) this.paintPalette();
		this.topology = new Topology(this, "Topology", {x: 30+this.paletteWidth, y: 20});
		this.wizardForm = new WizardForm(this);
		this.paintBackground();
		this.checkBrowser();
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
	infoMessage: function(title, message) {
		var div = $('<div/>').dialog({autoOpen: false, draggable: false, modal: true,
			resizable: false, height:"auto", width:"auto", title: title, 
			position:{my: "center center", at: "center center", of: editor.div}});
		div.append(message);
		div.dialog("open");
		return div; 
	},
	errorMessage: function(title, message) {
		var div = $('<div/>').dialog({autoOpen: false, draggable: false, modal: true,
			resizable: false, height:"auto", width:"auto", title: title, 
			position:{my: "center center", at: "center center", of: editor.div},
			dialogClass: "ui-state-error"});
		div.append(message);
		div.dialog("open");
		return div; 
	},
	ajaxModifyBegin: function() {
		if (this.ajaxModifyTransaction) return false;
		this.ajaxModifyTransaction = {mods:[], func:[]};
		return true;
	},
	ajaxModifyCommit: function() {
		if (!this.ajaxModifyTransaction) return false;
		this.ajaxModifyExecute(this.ajaxModifyTransaction);
		delete this.ajaxModifyTransaction;
	},
	ajaxModifyExecute: function(transaction) {
		var data = {"mods": $.toJSON(transaction.mods)};
		var editor = this;
		if (transaction.mods.length == 0) return;
		log("AJAX MOD SEND: " + transaction.mods.length);
		try {
			return $.ajax({type: "POST", url:ajaxpath+"top/"+topid+"/modify", async: true, data: data, complete: function(res){
				if (res.status == 200) {
					var msg = $.parseJSON(res.responseText);
					if (! msg.success) editor.errorMessage("Request failed", "<p><b>Error message:</b> " + msg.output + "</p><p>This page will be reloaded to refresh the editor.</p>").bind("dialogclose", function(){
						window.location.reload();						
					});
					for (var i = 0; i < transaction.func.length; i++) transaction.func[i](msg);
				} else editor.errorMessage("AJAX request failed", res.statusText);
			}});
		} catch (e) {
			editor.errorMessage("AJAX request failed", e);
		}
	},
	ajaxModify: function(mods, func) {
		if (this.isLoading) return;
		log("AJAX MOD:");
		for (var i = 0; i < mods.length; i++) log(mods[i]);
		if (this.ajaxModifyTransaction) {
			for (var i = 0; i < mods.length; i++) this.ajaxModifyTransaction.mods.push(mods[i]);
			if (func) this.ajaxModifyTransaction.func.push(func);
		} else this.ajaxModifyExecute({mods: mods, func:[func]});
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
	setSpecialFeatures: function(sfmap) {
		this.specialFeatures = sfmap;
	},
	loadTopologyURL: function(url) {
		var req = $.ajax({type: "GET", url: url, dataType: "xml"});
		var editor = this;
		req.success(function(xml) {
			editor.loadTopologyDOM(xml);
		});
	},
	loadTopologyDOM: function(xml) {
		this.isLoading = true;
		var editor = this;
		var dangling_interfaces_mods = [];
		$(xml).find("topology").each(function(){
			var attrs = getAttributesDOM(this);
			editor.topology.setAttributes(attrs);
			var devices = {};
			var connectors = {};
			var connections = {};
			var f = function(){
				var attrs = getAttributesDOM(this);
				var name = attrs["name"];
				var pos = attrs["pos"].split(",");
				var pos = {x: parseInt(pos[0])+editor.paletteWidth, y: parseInt(pos[1])};
				var type = attrs["type"];
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
					case "hub": 
						el = new HubConnector(editor, name, pos);
						connectors[name] = el;
						break;
					case "switch": 
						el = new SwitchConnector(editor, name, pos);
						connectors[name] = el;
						break;
					case "router": 
						el = new RouterConnector(editor, name, pos);
						connectors[name] = el;
						break;
					case "special": 
						el = new SpecialConnector(editor, name, pos);
						connectors[name] = el;
						break;
				}
				el.setAttributes(attrs);
			};
			$(this).find('device').each(f);
			$(this).find('connector').each(f);
			$(this).find('connection').each(function(){
				var attrs = getAttributesDOM(this);
				var con = connectors[$(this).parent().attr("name")];
				var ifname = attrs["interface"];
				var device = devices[ifname.split(".")[0]];
				var c = con.createConnection(device);
				c.setAttributes(attrs);
				connections[ifname] = c;
			});
			$(this).find('interface').each(function(){
				var attrs = getAttributesDOM(this);
				var device = devices[$(this).parent().attr("name")];
				var name = attrs["name"];
				var con = connections[device.name+"."+name];
				if (con) {
					var iface = device.createInterface(con);
					con.connect(iface);
					iface.setAttributes(attrs);
				} else dangling_interfaces_mods.push({type: "interface-delete", element: device.name, subelement: name, properties: {}});
			});
		});
		this.isLoading = false;
		if (dangling_interfaces_mods.length > 0) this.ajaxModify(dangling_interfaces_mods, new function(res){});
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
		y+=20;
		this.openVZPrototype = new OpenVZDevice(this, "OpenVZ", {x: this.paletteWidth/2, y: y+=50});
		this.openVZPrototype.paletteItem = true;
		this.kvmPrototype = new KVMDevice(this, "KVM", {x: this.paletteWidth/2, y: y+=50});
		this.kvmPrototype.paletteItem = true;
		y+=30;
		this.specialPrototype = new SpecialConnector(this, "Special", {x: this.paletteWidth/2, y: y+=50});
		this.specialPrototype.paletteItem = true;
		this.hubPrototype = new HubConnector(this, "Hub", {x: this.paletteWidth/2, y: y+=50});
		this.hubPrototype.paletteItem = true;
		this.switchPrototype = new SwitchConnector(this, "Switch", {x: this.paletteWidth/2, y: y+=40});
		this.switchPrototype.paletteItem = true;
		this.routerPrototype = new RouterConnector(this, "Router", {x: this.paletteWidth/2, y: y+=40});
		this.routerPrototype.paletteItem = true;
		y+=30;
		this.layout = this.g.image(basepath+"images/layout.png", this.paletteWidth/2 -16, this.size.y-120, 32, 32);
		this.layoutText = this.g.text(this.paletteWidth/2, this.size.y-83, "Layout");
		if (! isIE) this.layoutText.attr(this.defaultFont);
		this.layoutRect = this.g.rect(this.paletteWidth/2 -16, this.size.y-120, 32, 42).attr({fill:"#FFFFFF", opacity:0});
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
	connect: function(connector, device) {
		if (connector.isConnector && device.isDevice) {
			if (device.isConnectedWith(con)) return;
			var con = connector.createConnection(device);
			var iface = device.createInterface(con);
			con.connect(iface);
		} else if (connector.isDevice && device.isConnector ) this.connect(device, connector);
		else if (connector.isDevice && device.isDevice ) {
			var middle = {x: (connector.getPos().x + device.getPos().x) / 2, y: (connector.getPos().y + device.getPos().y) / 2}; 
			var con = new SwitchConnector(this, this.getNameHint("switch"), middle);
			this.connect(con, connector);
			this.connect(con, device);
		}
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
	removeElement: function(el) {
		this.elements.remove(el);
		if (el.name) this.elementNames.remove(el.name);
	},
	removeSelectedElements: function() {
		var sel = this.selectedElements();
		for (var i = 0; i < sel.length; i++) {
			var el = sel[i];
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
				force.add(middle.clone().sub(elPos).div(100));
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
			els[i].setAttribute("pos", (els[i].pos.x-this.paletteWidth)+","+els[i].pos.y);
		}
		if (tr) this.ajaxModifyCommit();
	}
});

var EditElement = Class.extend({
	init: function(name) {
		this.name = name;
	},
	onChanged: function(value) {
		this.form.onChanged(this.name, value);
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
	init: function(name, dflt) {
		this._super(name);
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
	init: function(obj) {
		this._super("name", obj.name);
	},
	onChanged: function(value) {
		this._super(value);
		this.form.div.dialog("option", "title", "Attributes of " + value);
	}
});

var MagicTextField = TextField.extend({
	init: function(name, pattern, dflt) {
		this._super(name, dflt);
		this.pattern = pattern;
	},
	onChanged: function(value) {
		this._super(value);
		if (this.pattern.test(this.getValue())) this.input[0].style.color="";
		else this.input[0].style.color="red";
	}
});

var PasswordField = TextField.extend({
	init: function(name, dflt) {
		this._super(name, dflt);
		this.input[0].type = "password";
	}
});

var SelectField = EditElement.extend({
	init: function(name, options, dflt) {
		this._super(name);
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
			$(this).attr({selected: $(this).attr("value") == value});
			found |= $(this).attr("value") == value; 		
		});
		if (!found) this.input.append($('<option value="'+value+'" selected>'+value+'</option>'));
	},
	getValue: function() {
		return this.input[0].value;
	},
	getInputElement: function() {
		return this.input;
	}
});

var CheckField = EditElement.extend({
	init: function(name, dflt) {
		this._super(name);
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
		this.input[0].checked = Boolean(value);
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
		this._super("button-"+name);
		this.func = func;
		this.input = $('<div>'+content+'<div/>');
		var t = this;
		this.input.button().click(function (){
			t.func(t);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setValue: function(value) {
	},
	getValue: function() {
		return "";
	},
	getInputElement: function() {
		return this.input;
	}
});

var AttributeForm = Class.extend({
	init: function(obj) {
		this.obj = obj;
		this.editor = obj.editor;
		this.div = $('<div/>').dialog({autoOpen: false, draggable: false,
			resizable: false, height:"auto", width:"auto", title: "Attributes of "+obj.name,
			show: "slide", hide: "slide"});
		this.table = $('<table/>').attr({"class": "ui-widget"});
		this.div.append(this.table);
		this.fields = {};
	},
	show: function() {
		this.div.dialog({position: {my: "left top", at: "right top", of: this.obj.getRectObj(), offset: this.obj.getRect().width+5+" 0"}});
		for (var name in this.fields) {
			var val = this.obj.attributes[name];
			if (val) this.fields[name].setValue(val);
			this.fields[name].setEditable(this.editor.editable);
		}
		this.div.dialog("open");
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
		this.obj.setAttribute(name, value);
	}
});

var TopologyForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new TextField("name", "Topology"), "name");
	}
});

var DeviceForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new NameField(obj), "name");
		this.addField(new SelectField("hostgroup", this.editor.hostGroups, "auto"), "hostgroup");
	}
});

var OpenVZDeviceForm = DeviceForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new SelectField("template", this.editor.templatesOpenVZ, "auto"), "template");
		this.addField(new TextField("root_password", "glabroot"), "root&nbsp;password");
		this.addField(new MagicTextField("gateway", /^\d+\.\d+\.\d+\.\d+$/, ""), "gateway");
	}
});

var KVMDeviceForm = DeviceForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new SelectField("template", this.editor.templatesKVM, "auto"), "template");
	}	
});

var ConnectorForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new NameField(obj), "name");
	}
});

var SpecialConnectorForm = ConnectorForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new SelectField("feature_type", getKeys(this.editor.specialFeatures), "auto"), "type");
		this.addField(new SelectField("hostgroup", [], "auto"), "hostgroup");
	},
	_featureChanged: function() {
		this.fields.hostgroup.setOptions(this.editor.specialFeatures[this.fields.feature_type.getValue()]);
	},
	onChanged: function(name, value) {
		this._super(name, value);
		if (name == "feature_type") this._featureChanged();
	}
});

var HubConnectorForm = ConnectorForm.extend({});

var SwitchConnectorForm = ConnectorForm.extend({});

var RouterConnectorForm = ConnectorForm.extend({});

var InterfaceForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new NameField(obj), "name");
	}
});

var ConfiguredInterfaceForm = InterfaceForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new CheckField("use_dhcp", false), "use&nbsp;dhcp");
		this.addField(new MagicTextField("ip4address", /^\d+\.\d+\.\d+\.\d+\/\d+$/, ""), "ip/prefix");		
	}
});

var ConnectionForm = AttributeForm.extend({});

var EmulatedConnectionForm = ConnectionForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new MagicTextField("bandwidth", /^\d+$/, "10000"), "bandwidth&nbsp;(in&nbsp;kb/s)");
		this.addField(new MagicTextField("delay", /^\d+$/, "0"), "latency&nbsp;(in&nbsp;ms)");
		this.addField(new MagicTextField("lossratio", /^\d+\.\d+$/, "0.0"), "packet&nbsp;loss");
		this.addField(new CheckField("capture", false), "capture&nbsp;packets");
	}
});

var EmulatedRouterConnectionForm = EmulatedConnectionForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new MagicTextField("gateway", /^\d+\.\d+\.\d+\.\d+\/\d+$/, ""), "gateway&nbsp;(ip/prefix)");
	}
});

var WizardForm = Class.extend({
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
			var internet = new SpecialConnector(this.editor, this.editor.getNameHint("internet"), {x: middle.x+50, y: middle.y+25});
			internet.setAttribute("feature_type", "internet");
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
			container.position({my: "right", at: "right", of: $(this.editor.div)});
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
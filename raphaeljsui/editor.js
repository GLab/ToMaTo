var NetElement = Class.extend({
  init: function(){
  },
  paint: function(){
  },
  paintUpdate: function(){
  },
  getX: function() {
    return this.getPos().x;
  },
  getY: function() {
    return this.getPos().y;
  }
});

var IconElement = NetElement.extend({
  init: function(name, iconsrc, iconsize, pos) {
    this._super();
    this.name = name;
    this.iconsrc = iconsrc;
    this.iconsize = iconsize;
    this.pos = pos;
  },
  paint: function(){
    this._super();
    if (this.text) this.text.remove();
    this.text = g.text(this.pos.x, this.pos.y+this.iconsize.y/2+5, this.name);
    if (this.icon) this.icon.remove();
    this.icon = g.image(this.iconsrc, this.pos.x-this.iconsize.x/2, this.pos.y-this.iconsize.y/2, this.iconsize.x, this.iconsize.y);
    this.icon.parent = this;
    this.icon.drag(function (dx, dy) {
      //move
      this.parent.move({x: this.opos.x + dx, y: this.opos.y + dy});
    }, function () {
      //start
      this.opos = this.parent.pos;
    }, function () {
      //stop
    });
  },
  paintUpdate: function() {
    this._super();
    this.icon.attr({x: this.pos.x-this.iconsize.x/2, y: this.pos.y-this.iconsize.y/2});
    this.text.attr({x: this.pos.x, y: this.pos.y+this.iconsize.y/2+5});
  },
  move: function(pos) {
    this.pos = pos;
    this.paintUpdate();
  },
  getPos: function() {
    return this.pos;
  }
});

var Connection = NetElement.extend({
  init: function(con, dev) {
    this._super();
    this.con = con;
    this.dev = dev;
    this.paint();
  },
  getPos: function(){
    return {x: (this.con.getX()+this.dev.getX())/2, y: (this.con.getY()+this.dev.getY())/2};
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
    this.path = g.path(this.getPath());
    if (this.handle) this.handle.remove();
    this.handle = g.rect(this.getX()-8, this.getY()-8, 16, 16).attr({fill: "#A0A0A0"});
    this.handle.parent = this;
    this.handle.drag(function (dx, dy) {
      //move
      this.shadow.attr({x: this.opos.x + dx -8, y: this.opos.y + dy -8});
    }, function () {
      //start
      this.opos = this.parent.getPos();
      this.shadow = this.clone().attr({opacity: .5});
    }, function () {
      //stop
      this.shadow.remove();
    });
  }
});

var Interface = NetElement.extend({
  init: function(dev, con){
    this._super();
    this.dev = dev;
    this.con = con;
    this.paint();
  },
  getPos: function() {
    xd = this.con.getX() - this.dev.getX();
    yd = this.con.getY() - this.dev.getY();
    magSquared = (xd * xd + yd * yd);
    mag = 14.0 / Math.sqrt(magSquared);
    return {x: this.dev.getX() + (xd * mag), y: this.dev.getY() + (yd * mag)};
  },
  paint: function(){
    if (this.circle) this.circle.remove();
    this.circle = g.circle(this.getX(), this.getY(), 8).attr({fill: "#CDCDB3"});
  },
  paintUpdate: function(){
    this._super();
    this.circle.attr({cx: this.getX(), cy: this.getY()});
  }
});

var Connector = IconElement.extend({
  init: function(name, pos) {
    this._super(name, "images/switch.png", {x: 32, y: 16}, pos);
    this.connections = [];
    this.paint();
  },
  move: function(pos) {
    this._super(pos);
    for (var i in this.connections) {
      this.connections[i].paintUpdate();
      this.connections[i].dev.paintUpdateInterfaces();
    }    
  },
  addConnection: function(con) {
    this.connections.push(con);
    this.paint();
  }
});

var Device = IconElement.extend({
  init: function(name, pos) {
    this._super(name, "images/computer.png", {x: 32, y: 32}, pos);
    this.interfaces = [];
    this.paint();
  },
  move: function(pos) {
    this._super(pos);
    for (var i in this.interfaces) this.interfaces[i].con.paintUpdate();
    this.paintUpdateInterfaces();   
  },
  paint: function() {
    this._super();
    for (var i in this.interfaces) this.interfaces[i].paint();    
  },
  paintUpdateInterfaces: function() {
    for (var i in this.interfaces) this.interfaces[i].paintUpdate();
  },
  addInterface: function(iface) {
    this.interfaces.push(iface);
  }
});

init = function(paper) {
  g = paper;
}

connect = function(connector, device) {
  con = new Connection(connector, device);
  connector.addConnection(con);
  iface = new Interface(device, con);
  device.addInterface(iface);
  device.paint();
}
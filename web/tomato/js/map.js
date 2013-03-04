var Site = Class.extend({
	init: function(map, name, displayName, pos) {
		this.map = map;
		this.name = name;
		this.displayName = displayName;
		this.pos = pos;
		this.marker = this.map.g.circle(this.pos.x, this.pos.y, 5).attr({fill: "#0000A0", title:this.displayName});
		this.name_tag = this.map.g.text(this.pos.x, this.pos.y+10, this.name).attr({"font-size":12, "font": "Verdana"});
		
		var f = function () {
			window.open('/link_stats/' + name, '_blank', 'innerHeight=450,innerWidth=600,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
		};
		this.marker.click(f);
		this.name_tag.click(f);
	}
});

var Window = Class.extend({
	init: function(title) {
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
	},
	add: function(div) {
		this.div.append(div);
	},
	getDiv: function() {
		return this.div;
	}
});


var Connection = Class.extend({
	init: function(map, src, dst, attrs) {
		this.map = map;
		this.src = src;
		this.dst = dst;
		this.attrs = attrs;
		var path = "M"+this.src.pos.x+" "+this.src.pos.y+"L"+this.dst.pos.x+" "+this.dst.pos.y;
		this.path = this.map.g.path(path).attr({"stroke-width": 4, stroke: this.getColor()});
		this.path.insertAfter(map.bg);
		var middle = {x: (this.src.pos.x + this.dst.pos.x)/2, y: (this.src.pos.y + this.dst.pos.y)/2};
		this.handle = this.map.g.rect(middle.x-4, middle.y-4, 8, 8).attr({fill: "#A0A0A0"});
		
		
		
		this.path.parent = this;
		this.handle.parent = this;
		var f = function () {
			window.open('/link_stats/' + src.name + "/" + dst.name, '_blank', 'innerHeight=450,innerWidth=600,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
		};
		this.handle.click(f);
	},
	getColor: function() {
		return this.attrs.color;
	}
});

var Map = Class.extend({
	init: function(size, background, coord_rect) {
		this.div = $("#map");
		this.link_details = $("#link_details");
		this.size = size;
		this.coord_rect = coord_rect;
		this.g = Raphael(this.div[0], size.x, size.y);
		this.sites = {}
		this.bg = this.g.image(background, 0, 0, this.size.x, this.size.y);
		this.connections=[];
	},
	getPos: function(pos) {
		var c = this.coord_rect;
		var x = (pos.long-c.west)*this.size.x/(c.east-c.west);
		var y = (pos.lat-c.north)*this.size.y/(c.south-c.north);
		return {x: Math.round(x), y: Math.round(y)};
	},
	addSite: function(name, displayName, pos) {
		var npos = this.getPos(pos);
		this.sites[name] = new Site(this, name, displayName, {x: npos.x, y: npos.y});
	},
	addConnection: function(a, b, attrs) {
		this.connections.push(new Connection(this, this.sites[a], this.sites[b], attrs));
	}
});
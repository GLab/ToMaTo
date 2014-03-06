function rgb2color(rgb) {
	for (var i = 0; i<3; i++) {
		rgb[i] = Math.round(rgb[i]*256).toString(16);
		if (rgb[i].length == 1) rgb[i] = "0" + rgb[i];
	}
	return "#" + rgb.join("") 
}

var Link = Class.extend({
	init: function(map, src, dst, data) {
		this.map = map;
		this.src = src;
		this.dst = dst;
		this.color = rgb2color(data.color);
	},
	_infoHtml: function() {
		var html = '<div id="content"><h4>Link from ' + this.src.name + ' to ' + this.dst.name + '</h4><div id="bodyContent">';
		html += this.src.name + ': ' + this.src.displayName + ' (' + this.src.location + ')<br/>';
		html += this.dst.name + ': ' + this.dst.displayName + ' (' + this.dst.location + ')<br/>';
		html += '<br/><a href="/link_stats/'+this.src.name+'/'+this.dst.name+'" target="_blank">Link statistics</a>';
		html += '</div></div>';
		return html;
	},
	render: function(map) {
		this.line = new google.maps.Polyline({
		    path: [this.src.coords, this.dst.coords],
		    geodesic: false,
		    strokeColor: this.color,
		    strokeOpacity: 1.0,
		    strokeWeight: 4,
		    map: map
		});
		this.infoWindow = new google.maps.InfoWindow({
		    content: this._infoHtml()
		});
		var t = this;
		google.maps.event.addListener(this.line, 'click', function() {
			if (t.map.current == t) {
				t.close();
				return;
			}
			t.map.closeCurrent(); 
			t.setVisible(true);
			var projection = map.getProjection();
			var start = projection.fromLatLngToPoint(t.src.coords);
			var end = projection.fromLatLngToPoint(t.dst.coords);
			var middle = projection.fromPointToLatLng(new google.maps.Point((start.x + end.x)/2, (start.y + end.y)/2));
			t.infoWindow.setPosition(middle);
		    t.infoWindow.open(t.map.map);
		    t.map.current = t;
		});
		google.maps.event.addListener(this.infoWindow, 'closeclick',function() {
			t.setVisible(false);
		});		
	},
	close: function() {
		this.map.current = null;
		this.setVisible(false);
		this.infoWindow.close();
	},
	setVisible: function(visible) {
		this.line.setMap(visible ? this.map.map : null);
	}
})

var Site = Class.extend({
	init: function(map, data) {
		this.map = map;
		this.geolocation = data.geolocation;
		this.location = data.location;
		this.name = data.name;
		this.description = data.description;
		this.displayName = data.displayName;
		this.organization = data.organization;
		this.coords = new google.maps.LatLng(this.geolocation.latitude, this.geolocation.longitude);
		this.links = [];
	},
	addLink: function(link) {
		this.links.push(link);
	},
	_infoHtml: function() {
		var html = '<div id="content"><h4>' + this.displayName + ', ' + this.location + ' (' + this.name + ')</h4><div id="bodyContent">';
		if (this.description) html += '<p>' + this.description + '</p>';
		html += '<p>Hosted by: <br/>';
		if (this.organization.image_url) html += '<img style="max-width:4cm; max-height:3cm;" src="'+this.organization.image_url+'" title="'+this.organization.description+'"/>';
		else html += this.organization.description;
		html += '<br /><a href="'+this.organization.homepage_url+'" target="_blank">'+this.organization.homepage_url+'</a></p>';
		html += '<p><a href="/link_stats/'+this.name+'" target="_blank">Statistics for intra-site traffic</a></p>'; 
		html += '</div></div>';
		return html;
	},
	render: function(map) {
		this.marker = new google.maps.Marker({
      		position: this.coords,
      		map: map,
      		icon: '/img/map_site_icon.png'
  		});
		this.infoWindow = new google.maps.InfoWindow({
		    content: this._infoHtml()
		});
		var t = this;
		google.maps.event.addListener(this.marker, 'click', function() {
			if (t.map.current == t) {
				t.close();
				return;
			}
			t.map.closeCurrent(); 
		    t.setLinksVisible(true);
		    t.infoWindow.open(t.map.map, t.marker);
		    t.map.current = t;
		});
		google.maps.event.addListener(this.infoWindow, 'closeclick',function() {
			t.setLinksVisible(false);
		});
	},
	close: function() {
		this.map.current = null;
		this.infoWindow.close();
		this.setLinksVisible(false);
	},
	setVisible: function(visible) {
		this.marker.setMap(visible ? this.map.map : null);
	},
	setLinksVisible: function(visible) {
		for (var i=0; i<this.links.length; i++) this.links[i].setVisible(visible);
	}
})

var Map = Class.extend({
	init: function(options) {
		this.options = options;
		this.sites = {};
		this.current = null;
		this.links = [];
		for (var i=0; i < options.sites.length; i++) this.sites[options.sites[i].name] = new Site(this, options.sites[i]);
		for (var i=0; i < options.links.length; i++) {
			var link_data = options.links[i];
			var src_site = this.sites[link_data.src];
			var dst_site = this.sites[link_data.dst];
			var link = new Link(this, src_site, dst_site, link_data);
			this.links.push(link);
			src_site.addLink(link);
			dst_site.addLink(link);
		}
		this.render();
	},
	render: function() {
		this.map = new google.maps.Map(this.options.canvas, {
			mapTypeId: google.maps.MapTypeId.ROADMAP,
			zoom: 3,
			center: new google.maps.LatLng(50, -55)
		});
		for (var name in this.sites) this.sites[name].render(this.map);
		for (var i=0; i<this.links.length; i++) {
			var link = this.links[i];
			link.render(this.map);
			link.setVisible(false);
		}
	},
	closeCurrent: function() {
		if (this.current) this.current.close();
	}
});


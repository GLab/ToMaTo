
var TemplateStore = Class.extend({
	init: function(data,editor) {
		this.editor = editor;
		data.sort(function(t1, t2){
			var t = t2.preference - t1.preference;
			if (t) return t;
			if (t1.name < t2.name) return -1;
			if (t2.name < t1.name) return 1;
			return 0;
		});
		this.types = {};
		for (var i=0; i<data.length; i++)
		  this.add(new Template(data[i]));
	},
	add: function(tmpl) {
		if (! this.types[tmpl.type]) this.types[tmpl.type] = {};
		this.types[tmpl.type][tmpl.name] = tmpl;
	},
	getAll: function(type) {
		if (! this.types[type]) return [];
		var tmpls = [];
		for (var name in this.types[type])
			tmpls.push(this.types[type][name]);
		return tmpls;
	},
	getAllowed: function(type) {
		var templates = this.getAll(type);
		if (!this.editor.allowRestrictedTemplates) {
			var templates_filtered = [];
			for (var i = 0; i<templates.length;i++) {
				if (!(templates[i].restricted))
					templates_filtered.push(templates[i]);
			}
			templates = templates_filtered;
		}
		return templates;
	},
	get: function(type, name) {
		if (! this.types[type]) return null;
		return this.types[type][name];
	},
	getCommon: function() {
		var common = [];
		for (var type in this.types)
		 for (var name in this.types[type])
		  if (this.types[type][name].showAsCommon && (!this.types[type][name].restricted || this.editor.allowRestrictedTemplates))
		   common.push(this.types[type][name]);
		return common;
	}
});


var ProfileStore = Class.extend({
	init: function(data,editor) {
		this.editor = editor;
		data.sort(function(t1, t2){
			var t = t2.preference - t1.preference;
			if (t) return t;
			if (t1.name < t2.name) return -1;
			if (t2.name < t1.name) return 1;
			return 0;
		});
		this.types = {};
		for (var i=0; i<data.length; i++)
		  this.add(new Profile(data[i]));
	},
	add: function(tmpl) {
		if (! this.types[tmpl.type]) this.types[tmpl.type] = {};
		this.types[tmpl.type][tmpl.name] = tmpl;
	},
	getAll: function(type) {
		if (! this.types[type]) return [];
		var tmpls = [];
		for (var name in this.types[type]) tmpls.push(this.types[type][name]);
		return tmpls;
	},
	getAllowed: function(type) {
		var profs = this.getAll(type);
		if (!this.editor.allowRestrictedProfiles) {
			var profs_filtered = [];
			for (var i = 0; i<profs.length;i++) {
				if (!(profs[i].restricted))
					profs_filtered.push(profs[i]);
			}
			profs = profs_filtered;
		}
		return profs;
	},
	get: function(type, name) {
		if (! this.types[type]) return null;
		return this.types[type][name];
	}
});

var NetworkStore = Class.extend({
	init: function(data,editor) {
		this.editor = editor;
		data.sort(function(t1, t2){
			var t = t2.preference - t1.preference;
			if (t) return t;
			if (t1.kind < t2.kind) return -1;
			if (t2.kind < t1.kind) return 1;
			return 0;
		});
		this.nets = [];
		for (var i=0; i<data.length; i++) {
		     net = data[i];
			 if (!net.icon) {
				 net.icon = this.getNetworkIcon(net.kind);
			 }
			 this.nets.push(net);
		}
	},
	getAll: function() {
		return this.nets;
	},
	getAllowed: function() {
		var allowedNets = this.getAll()
		if (!this.editor.allowRestrictedNetworks) {
			var nets_filtered = [];
			
			for (var i = 0; i<allowedNets.length;i++) {
				if (!(allowedNets[i].restricted)) {
					nets_filtered.push(allowedNets[i]);
				}
			}
			allowedNets = nets_filtered;
		}
		return allowedNets;
	},
	getCommon: function() {
		var common = [];
		for (var i = 0; i < this.nets.length; i++)
		 if (this.nets[i].show_as_common && (!this.nets[i].restricted || this.editor.allowRestrictedNetworks))
		   common.push(this.nets[i]);
		return common;
	},
	getNetworkIcon: function(kind) {
		return dynimg(32,"network",kind.split("/")[0],(kind.split("/")[1]?kind.split("/")[1]:null));
	}
});
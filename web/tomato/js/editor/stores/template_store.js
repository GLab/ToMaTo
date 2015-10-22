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



var VMElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.helpTarget = "http://tomato-lab.org/manuals/user/element/device/"+data.type+"#config"
	},
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	iconUrl: function() {
		if (this.data._custom_icon != undefined && this.data._custom_icon != null && this.data._custom_icon != "") {
			return this.data._custom_icon;
		}
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
		config.order = ["name", "site", "profile", "template", "tech", "_endpoint", "_custom_icon"];
		config.ignore.push("info_last_sync");
		config.ignore.push("args_doc");

		var tech_conf = editor.options.vm_element_config
		if (this.data.type in tech_conf) {
			var t_conf = tech_conf[this.data.type];

			choices = {"": "Automatic"};
			for (var tech in t_conf) {
				if (tech != "remove")
					choices[t_conf[tech]] = editor.options.tech_names[t_conf[tech]];
			}

			if (t_conf.length > 1) {
				config.ignore.remove("tech");
				config.special.tech = new ChoiceElement({
					label: "Tech",
					name: "tech",
					choices: choices,
					value: this.data.tech,
					disabled: !this.attrEnabled("tech")
				});
			} else {
				config.order.remove("tech");
			}
		}
		
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

		var tpl = this.data.template || this.caps.attributes.template["default"];
		if (!this.getTemplate()) tpl = this.caps.attributes.template["default"];
		config.special.template = new TemplateElement({
			label: "Template",
			name: "template",
			value: tpl,
			custom_template: this.data.custom_template,
			disabled: (this.data.state == "started"),
			type: this.data.type,
			call_element: this
		});
		topology_site = this.editor.topology.data.site
		config.special.site = new ChoiceElement({
			label: "Site",
			name: "site",
			info: siteInfo,
			choices: createMap(this.editor.sites, "name", function(site) {
				return (site.label || site.name) + (site.location ? (", " + site.location) : "");
			}, {"": topology_site ? "Topology Default ("+this.editor.sites_dict[topology_site].label+")" : "Any site"}),
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
		config.special._custom_icon = new TextElement({
			label: "Custom icon",
			name: "_custom_icon",
			value:this.data._custom_icon,
			hint: "URL to 32x32 PNG image"
		});
		config.special.args = new CommandTextElement({
			label: "Arguments",
			name: "args",
			value: this.data.args,
			args_doc: this.data.args_doc
		});
		return config;
	},
	getConnectTarget: function(callback) {
		return this.topology.createElement({type: this.data.type + "_interface", parent: this.data.id}, callback);
	}
});

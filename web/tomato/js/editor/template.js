
var Template = Class.extend({
	init: function(options) {
		this.classoptions = options;
		this.type = options.tech;
		this.subtype = options.subtype;
		this.name = options.name;
		this.label = options.label || options.name;
		this.description = options.description || "no description available";
		this.nlXTP_installed = options.nlXTP_installed || false;
		this.creation_date = options.creation_date;
		this.restricted = options.restricted;
		this.preference = options.preference;
		this.showAsCommon = options.show_as_common;
		this.icon = options.icon;
	},
	iconUrl: function() {
		return this.icon || dynimg(32,this.type,(this.subtype?this.subtype:null),(this.name?this.name:null));
	},
	menuButton: function(options) {
		var hb = '<p style="margin:4px; border:0px; padding:0px; color:black;"><table><tbody>'+
					'<tr><td><img src="/img/info.png"></td><td>'+this.description+'</td></tr>';
		if (!this.nlXTP_installed) {
			hb = hb + '<tr><td><img src="/img/error.png" /></td>'+
				'<td>No nlXTP guest modules are installed. Executable archives will not auto-execute and status '+
				'will be unavailable. <a href="'+help_baseUrl+'/rextfv/guestmodules" target="_help">More Info</a></td></tr>';
		}
		hb = hb + "</tbody></table></p>";
		return Menu.button({
			name: options.name || (this.type + "-" + this.name),
			label: options.label || this.label || (this.type + "-" + this.name),
			icon: this.iconUrl(),
			toggle: true,
			toggleGroup: options.toggleGroup,
			small: options.small,
			func: options.func,
			hiddenboxHTML: hb
		});
	},
	labelForCommon: function() {
		var label = this.label.replace(/[ ]*\(.*\)/, "");
		switch (this.type) {
			case "kvmqm":
				label += " (KVM)";
				break;
			case "openvz":
				label += " (OpenVZ)";
				break;
			case "repy":
				label += " (Repy)";
				break;
		}
		return label;
	},
	infobox: function() {
		var restricted_icon = "/img/lock_open.png";
		var restricted_text = "You have the permission to use this restricted template.";
		if (!editor.allowRestrictedTemplates) {
			restricted_icon = "/img/lock.png";
			restricted_text = "This template is restricted. Contact an administrator if you want to get access to restricted templates.";
		}
		
		var info = $('<div class="hoverdescription" style="display: inline; white-space:nowrap;"></div>');
		var d = $('<div class="hiddenbox"></div>');
		var p = $('<p style="margin:4px; border:0px; padding:0px; color:black; min-width:8.5cm;"></p>');
		var desc = $('<table></table>');
		p.append(desc);
		d.append(p);
		
		if (this.description || this.creation_date) {

			info.append('<img src="/img/info.png" />');
		
			if (this.description) {
				desc.append($('<tr><th><img src="/img/info.png" /></th><td style="background:white; white-space:pre !important;">'+this.description+'</td></tr>'));
			}
			
			if (this.creation_date) {
				desc.append($('<tr><th><img src="/img/calendar.png" /></th><td style="background:white; white-space:nowrap !important;">'+new Date(1000*this.creation_date).toDateString()+'</td></tr>'));
			}
			
		} else {
			info.append('<img src="/img/invisible16.png" />');
		}
		
		if (!this.nlXTP_installed) {
			desc.append($('<tr><th><img src="/img/warning16.png" /></th><td style="background:white; padding-top:0.5cm; padding-bottom:0.5cm;">No nlXTP guest modules are installed. Executable archives will not auto-execute and status will be unavailable. <a href="'+help_baseUrl+'/ExecutableArchives#guest-modules" target="_help">More Info</a></td></tr>'));
			info.append('<img src="/img/warning16.png" />');
		} else {
			info.append('<img src="/img/invisible16.png" />');
		}
		
		if (this.restricted) {
			desc.append($('<tr><th><img src="'+restricted_icon+'" /></th><td style="background:white;">'+restricted_text+'</td></tr>'));
			info.append('<img src="'+restricted_icon+'" />');
		} else {
			info.append('<img src="/img/invisible16.png" />');
		}
		
		info.append(d);
		
		return info;
	}
});

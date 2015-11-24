var DefaultExecutableArchiveDetailWindow = Window.extend({
	init: function(options) {

		var t = this;
		options.buttons = [

		                    {
		                    	text: "Use Executable Archive",
		                    	click: function() {
		                			t.hide();
		                    		t.callback(t.getValue());
		                		}

		                    },
		                    {
		                    	text: "Cancel",
		                    	click: function() {
		                			t.hide();
		                		}
		                    }];

		this._super(options);
		this.element = options.element;
		this.archive = options.archive;
		this.has_alternatives = false;
		var windowTitle = "Select Archive to use for "+this.element.data.name;
		if (editor.options.show_ids) windowTitle = windowTitle + ' ['+this.element.data.id+']'
		this.setTitle(windowTitle);
		if (options.disabled == undefined || options.disabled == null) {
			this.disabled = false;
		} else {
			this.disabled = options.disabled;
		}

		if (options.callback != undefined && options.callback != null) {
			this.callback = options.callback;
		} else {
			this.callback = function(value) {};
		}



		this.value = this.archive.default_archive;
		this.choices = [];
		var default_entry = {
			isDefault: true,
			url: this.archive.default_archive,
			label: "Default",
			description: "Use this if the others don't fit.",
			tech: null,
			template: null,
			icon: '/img/tick.png'
		};
		this.choices.push(default_entry);
		var techs = Object.keys(this.archive.alternatives);
		var found_matching = false;
		for (var i = 0; i<techs.length; i++) {
			var tech = techs[i];
			var alts = Object.keys(this.archive.alternatives[tech]);
			for (var j = 0; j<alts.length; j++) {
				template = alts[j];
				alt_entry = this.archive.alternatives[tech][template];
				if ((editor.templates.types[tech] != undefined) && (editor.templates.types[tech][template] != undefined)) {
					var tech_label = null;
					var tech_icon = '/img/'+tech+'16.png';
					switch (tech) {
						case "kvmqm":
							tech_label = " KVM";
							break;
						case "openvz":
							tech_label = " OpenVZ";
							break;
						case "repy":
							tech_label = " Repy";
							break;
					}
					template_label = editor.templates.types[tech][template].label + " - " + tech_label;
					this.has_alternatives = true;
					var isDefault = false;
					if (!found_matching) {
						if ((tech == this.element.data.type) && (template == this.element.data.template)) {
							default_entry.isDefault = false
							found_matching = true;
							isDefault = true;
							this.value = alt_entry.url;
						}
					}
					this.choices.push({
						isDefault: isDefault,
						url: alt_entry.url,
						label: template_label,
						tech: tech,
						template: template,
						icon: tech_icon,
						description: alt_entry.description
					});
				}
			}
		}

		var table = this.getList();

		this.div.append($('<div style="margin-bottom:0.5cm; margin-top:0.5cm;"><table style="vertical-align:top;"><tr><td style="vertical-align:top; font-size: 10pt; white-space:normal; font-style:italic;">Please select the version that best fits the current disk image.</td></tr></table></div>'));
		this.div.append(table);
	},
	getValue: function() {
		return this.value;
	},
	get_infobox(item) {
		if (item.description) {
			return $('\
				<div class="hoverdescription" style="display: inline; white-space:nowrap;">\
					<img src="/img/info.png"/>\
					<div class="hiddenbox">\
						<p style="margin:4px; border:0px; padding:0px; color:black; min-width:8.5cm;">\
							<table>\
								<tr><th><img src="/img/info.png" /></th>\
								<td style="background:white; white-space:pre !important;">'+item.description+'</td></tr>\
							</table>\
						</p>\
					</div>\
				</div>\
			');
		} else {
			return $('<div></div>');
		}
	},
	getList: function() {
		var form = $('<form class="form-horizontal"></form>');
		var ths = this;
		var winID = Math.random();

		//build template list entry
		var div_formgroup = $('<div class="form-group"></div>');
		for(var i=0; i<this.choices.length; i++) {
			var alt = this.choices[i];


			var div_option = $('<div class="col-sm-10" />');
			var div_radio = $('<div class="radio"></div>');
			div_option.append(div_radio);
			var radio = $('<input type="radio" name="template" value="'+alt.url+'" id="'+winID+alt.tech+":"+alt.template+'" />');

			if (this.disabled) {
				radio.prop("disabled",true);
			} else {
				radio.change(function() {
					ths.value = this.value;
				});
			}

			console.log(this.element);
			if (alt.isDefault) {
				radio.prop("checked",true);
			}

			var radiolabel = $('<label for="'+winID+alt.tech+":"+alt.template+'"><img src="'+alt.icon+'"/> '+alt.label+'</label>');
			radiolabel.click( function(){
				$(this).children('input').attr('checked', 'checked');
			});
			div_radio.append(radiolabel);
			radiolabel.prepend(radio);
			var div_info = $('<div class="col-sm-2" />');
			div_info.append(this.get_infobox(alt));

			div_formgroup.append(div_option);
			div_formgroup.append(div_info);

			form.append(div_formgroup);
		}

		return form;
	}
});

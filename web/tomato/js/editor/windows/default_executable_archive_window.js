var DefaultExecutableArchiveWindow = Window.extend({
	init: function(options) {

		var t = this;
		options.buttons = [

		                    {
		                    	text: "Continue",
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

		this.disable_restricted = false;
		//this.disable_restricted = !(editor.allowRestrictedTemplates);  fixme: add mechanism for restricted default archives



		this.value = null;
		this.choices = editor.web_resources.executable_archives;

		var table = this.getList();

		this.div.append(table);
	},
	getValue: function() {
		return this.value;
	},
	getList: function() {
		var form = $('<form class="form-horizontal"></form>');
		var ths = this;
		var winID = Math.random();
		var something_selected = false;

		//build template list entry
		var div_formgroup = $('<div class="form-group"></div>');
		for(var i=0; i<this.choices.length; i++) {
			var archive = this.choices[i];


			var div_option = $('<div class="col-md-10" />');
			var div_radio = $('<div class="radio"></div>');
			div_option.append(div_radio);
			var radio = $('<input type="radio" name="template" value="'+archive.name+'" id="'+winID+archive.name+'" />');

			if (this.disabled) {
				radio.prop("disabled",true);
			} else {
				radio.change(function() {
					ths.value = this.value;
				});
			}

			if (!something_selected) {
				radio.prop("checked",true);
				this.value = archive.name;
				something_selected = true;
			}

			if (this.disable_restricted && archive.restricted) {
				radio.prop("disabled",true);
			}

			var radiolabel = $('<label for="'+winID+archive.name+'"><img src="'+archive.icon+'"/> '+archive.label+'</label>');
			radiolabel.click( function(){
				$(this).children('input').attr('checked', 'checked');
			});
			div_radio.append(radiolabel);
			radiolabel.prepend(radio);
			var div_info = $('<div class="col-md-2" />');
			//div_info.append(archive.infobox());  // fixme: generate infoboxes

			div_formgroup.append(div_option);
			div_formgroup.append(div_info);

			form.append(div_formgroup);
		}

		return form;
	}
});

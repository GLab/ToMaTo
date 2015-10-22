var TemplateWindow = Window.extend({
	init: function(options) {
		
		var t = this;
		options.buttons = [ 

		                    {
		                    	text: "Save",
		                    	click: function() {
		                			t.hide();
		                    		t.callback_before_finish(t.getValue());
		                			t.save();
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
		var windowTitle = "Change Template for "+this.element.data.name;
		if (editor.options.show_ids) windowTitle = windowTitle + ' ['+this.element.data.id+']'
		this.setTitle(windowTitle);
		if (options.disabled == undefined || options.disabled == null) {
			this.disabled = false;
		} else {
			this.disabled = options.disabled;
		}
		
		this.callback = function(value) {};
		if (options.callback_after_finish != undefined && options.callback_after_finish != null) {
			this.callback_after_finish = options.callback_after_finish;
		} else {
			this.callback_after_finish = function(value) {};
		}
		
		if (options.callback_before_finish != undefined && options.callback_before_finish != null) {
			this.callback_before_finish = options.callback_before_finish;
		} else {
			this.callback_before_finish = function(value) {};
		}
		
		this.disable_restricted = !(editor.allowRestrictedTemplates);
		
		
		
		this.value = this.element.data.template;
		this.choices = editor.templates.getAll(this.element.data.type);
		
		var table = this.getList();
		
		
		this.div.append($('<div style="margin-bottom:0.5cm; margin-top:0.5cm;"><table style="vertical-align:top;"><tr><th style="vertical-align:top;">Warning:</th><td style="vertical-align:top; font-size: 10pt; white-space:normal; font-style:italic;">You will lose all data on this device if you change the template.</td></tr></table></div>'));
		this.div.append(table);
	},
	getValue: function() {
		return this.value;
	},
	save: function() {
		var t = this;
		this.element.changeTemplate(
			this.getValue(),
			function(){
				t.callback_after_finish(t.getValue());
			}
		);
	},
	getList: function() {
		var form = $('<form class="form-horizontal"></form>');
		var ths = this;
		var winID = Math.random();

		//build template list entry
		var div_formgroup = $('<div class="form-group"></div>');
		for(var i=0; i<this.choices.length; i++) {
			var t = this.choices[i];

			
			var div_option = $('<div class="col-md-10" />');
			var div_radio = $('<div class="radio"></div>');
			div_option.append(div_radio);
			var radio = $('<input type="radio" name="template" value="'+t.name+'" id="'+winID+t.name+'" />');
			
			if (this.disabled) {
				radio.prop("disabled",true);
			} else {
				radio.change(function() {
					ths.value = this.value;
				});
			}
			
			if (this.disable_restricted && t.restricted) {
				radio.prop("disabled",true);
			}
			
			if (t.name == this.element.data.template) {
				radio.prop("checked",true);
			}
			
			var radiolabel = $('<label for="'+winID+t.name+'">'+t.label+'</label>');
			radiolabel.click( function(){
				$(this).children('input').attr('checked', 'checked');
			});
			div_radio.append(radiolabel);
			radiolabel.prepend(radio);
			var div_info = $('<div class="col-md-2" />');
			div_info.append(t.infobox());
			
			div_formgroup.append(div_option);
			div_formgroup.append(div_info);
			
			form.append(div_formgroup);
		}
		
		return form;
	}
});

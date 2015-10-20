
var FormElement = Class.extend({
	init: function(options) {
		this.options = options;
		this.name = options.name || options.label;
		this.label = options.label || options.name;
		if (options.callback) this.callback = options.callback;
		this.element = null;
	},
	getElement: function() {
		return this.element;
	},
	getLabel: function() {
		return this.label;
	},
	getName: function() {
		return this.name;
	},
	convertInput: function(value) {
		if (this.options.inputConverter) value = this.options.inputConverter(value);
		return value;
	},
	setEnabled: function(value) {
		this.element.attr({disabled: !value});
	},
	onChanged: function(value) {
		if (this.isValid(value)) {
			this.element.removeClass("invalid");
			this.element.addClass("valid");
		} else {
			this.element.removeClass("valid");
			this.element.addClass("invalid");
		}
		if (this.callback) this.callback(this, value);
	},
	isValid: function(value) {
		return true;
	}
});

var TextElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.pattern = options.pattern || /^.*$/;
		this.element = $('<div class="col-sm-12" />');
		this.textfield = $('<input class="form-control" type="'+(options.password ? "password" : "text")+'" name="'+this.name+'"/>');

		this.element.append(this.textfield);
		
		if (options.disabled) this.textfield.attr({disabled: true});
		if (options.onChangeFct) {
			this.textfield.change(options.onChangeFct);
			this.textfield.keypress(options.onChangeFct);
		}
		var t = this;
		this.textfield.change(function() {
			t.onChanged(this.value);
		});
		if (options.value != null) this.setValue(options.value);
	},
	getValue: function() {
		return this.convertInput(this.textfield[0].value);
	},
	setValue: function(value) {
		this.textfield[0].value = value;
	},
	isValid: function(value) {
		var val = value || this.getValue();
		return this.pattern.test(val);
	}
});

var TextAreaElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.element = $('<div class="col-sm-12">');
		this.textfield = $('<textarea class="form-control" name="'+this.name+'"></textarea>');
		
		this.element.append(this.textfield);
		
		if (options.disabled) this.textfield.attr({disabled: true});
		var t = this;
		this.textfield.change(function() {
			t.onChanged(this.value);
		});
		if (options.value != null) this.setValue(options.value);
	},
	getValue: function() {
		return this.convertInput(this.textfield[0].value);
	},
	setValue: function(value) {
		this.textfield[0].value = value;
	}
});

var CheckboxElement = FormElement.extend({
	init: function(options) {
		this._super(options);

		this.checkbox = $('<input class="form-element" type="checkbox" name="'+this.name+'"/>');
		this.element = $('<div class="col-sm-12">').append(this.checkbox);
		if (options.disabled) this.checkbox.attr({disabled: true});
		var t = this;
		this.checkbox.change(function() {
			t.onChanged(t.checkbox.prop("checked"));
		});
		if (options.value != null) this.setValue(options.value);
	},
	getValue: function() {
		return this.checkbox.prop("checked");
	},
	setValue: function(value) {
		this.checkbox.prop("checked", value);
	}
});

var ChoiceElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.infoboxes = options.info;
		this.showInfo = (this.infoboxes != undefined);
 
		this.select = $('<select class="form-control input-sm" name="'+this.name+'"/>');
		if (options.disabled) this.select.attr({disabled: true});
		var t = this;
		this.select.change(function() {
			t.onChanged(this.value);
		});
		this.choices = options.choices || {};
		this.setChoices(this.choices);
		if (options.value != null) { 
			
			this.setValue(options.value);
		}
		
		if (this.showInfo) {
			var choiceElement = $('<div class="col-sm-9" />');
			choiceElement.append(this.select);
			this.info = $('<div class="col-sm-3"></div>');
			this.element = $('<div />');
			this.element.append(choiceElement,this.info);
			
			var t = this;
			this.select.change(function(){
				t.updateInfoBox();
			});
			
			this.updateInfoBox();
		} else {
			this.element = $('<div class="col-sm-12" />');
			this.element.append(this.select);
		}
		
		
	},
	setChoices: function(choices) {
		this.select.find("option").remove();
		for (var name in choices) this.select.append($('<option value="'+name+'">'+choices[name]+'</option>'));
		this.setValue(this.getValue());
	},
	getValue: function() {
		return this.convertInput(this.select[0].value);
	},
	setValue: function(value) {
		var options = this.select.find("option");
		for (var i=0; i < options.length; i++) {
			$(options[i]).attr({selected: options[i].value == value + ""});
		}
	},
	updateInfoBox: function() {
		
		var escape_str = function(str) {
		    var tagsToReplace = {
		            '&': '&amp;',
		            '<': '&lt;',
		            '>': '&gt;',
		            '\n':'<br />'
		        };
		        return str.replace(/[&<>\n]/g, function(tag) {
		            return tagsToReplace[tag] || tag;
		        });
		    };
		
		this.info.empty();
		this.info.append(this.infoboxes[this.getValue()]);
	}
});

var TemplateElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.options = options;
		this.disabled = options.disabled;
		this.call_element = options.call_element;
		
		this.element = $('<div />');
		this.labelarea = $('<div class="col-sm-6"/>');
		this.changebuttonarea = $('<div class="col-sm-3"/>');
		this.infoarea = $('<div class="col-sm-3"/>');
		
		this.element.append(this.labelarea);
		this.element.append(this.changebuttonarea);
		this.element.append(this.infoarea);
		
		template = editor.templates.get(options.type,options.value);
		if (options.custom_template) {
			this.change_value(new DummyForCustomTemplate(template));
		} else {
			this.change_value(template);
		}
		
	},
	getValue: function() {
		return this.value;
	},
	
	change_value: function(template,loading) {
		this.value = template.name;
		this.template = template;
		var t = this;
		
		var changebutton = $('<button type="button" class="btn btn-primary"><span class="ui-button-text">Change</span></button>');
		changebutton.click(function() {
			t.call_element.showTemplateWindow(
				
				function(value) {
					t.change_value(
						editor.templates.get(
							t.options.type,value
						),
						true
					);
				},
					
				function(value) {
					t.change_value(
						editor.templates.get(
							t.options.type,value
						),
						false
					);
				}
				
			);
		})
		
		if (this.disabled || loading) {
			changebutton.prop("disabled",true);
		}
		
		this.labelarea.empty();
		this.changebuttonarea.empty();
		this.infoarea.empty();
		
		this.labelarea.append(this.template.label);
		this.changebuttonarea.append(changebutton);
		this.infoarea.append($(this.template.infobox()));
		
		if (loading) {
			this.labelarea.append($(' <img src="/img/loading.gif" />'));
		}
	}
});
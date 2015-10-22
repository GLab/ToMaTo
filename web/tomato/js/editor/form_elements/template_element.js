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

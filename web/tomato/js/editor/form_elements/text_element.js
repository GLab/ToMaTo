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

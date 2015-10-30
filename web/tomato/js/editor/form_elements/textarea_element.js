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

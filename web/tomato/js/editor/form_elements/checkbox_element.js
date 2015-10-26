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

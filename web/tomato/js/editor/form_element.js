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

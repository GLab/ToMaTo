
var AttributeWindow = Window.extend({
	init: function(options) {
		this._super(options);
		this.table = $('<form class="form-horizontal" role="form"></form>');
		this.div.append(this.table);
		this.elements = [];
		this.table.submit(function(evt) {
		  options.buttons[0].click();
		  evt.preventDefault();
		});
	},
	addText: function(text) {
		this.table.append("<p>"+text+"</p>");		
	},
	add: function(element) {
		this.elements.push(element);
		var tr = $('<div class="form-group"/>');
		tr.append($('<label for="'+element.getElement().name+'" class="col-sm-4 control-label" />').append(element.getLabel()));
		elem = $('<div class="col-sm-8" />')
		elem.append($('<p style="padding:0px; margin:0px;"></p>').append($(element.getElement())));
		tr.append(elem);
		this.table.append(tr);
		if (element.options.help_text) {
			var helptr = $('<div class="form-group" />');
			helptr.append($('<div class="col-sm-4 control-label" />'));
			helptr.append($('<p style="padding:0px; margin:0px;"></p>')
					.append($('<div class="col-sm-8" style="color:#888888;"></div>')
					.append($('<div class="col-sm-12" style="color:#888888;"></div>')
					.append(element.options.help_text))));
			this.table.append(helptr);
		}
		return element;
	},
	autoElement: function(info, value, enabled) {
		var el;
		var options = null;
		var type = null;
		if (info.read_only) enabled = false;
		if (info.type) type = info.type;
		if (info.options) options = info.options;
		var schema = null;
		if (info.value_schema) {
		    schema = info.value_schema;
		    if (schema.options && schema.options.length) options = schema.options;
		    if (schema.types) type = schema.types[0];
		}
		if (options) {
		    var choices = {};
		    for (var i=0; i<options.length; i++) {
		        if (schema && schema.options_desc) choices[options[i]] = schema.options_desc[i] || options[i];
		        else choices[options[i]] = options[i];
		    }
		    return new ChoiceElement({
			    label: info.label || info.name,
			    name: info.name,
			    choices: choices,
			    value: value || info["default"],
			    disabled: !enabled
		    });
		}
		if (jQuery.type(value)=="boolean") {
			return new CheckboxElement({
				label: info.label || info.name,
				name: info.name,
				value: value || info["default"],
				disabled: !enabled
			});
		}
		var converter = null;
		switch (type) {
			case "int":
				converter = parseInt;
				break;
			case "float":
				converter = parseFloat;
				break;
		}
		return new TextElement({
			label: info.label || info.name,
			name: info.name,
			value: value || info["default"],
			disabled: !enabled,
			inputConverter: converter
		});
	},
	autoAdd: function(info, value, enabled) {
		this.add(this.autoElement(info, value, enabled));
	},
	getValues: function() {
		var values = {};
		for (var i=0; i < this.elements.length; i++) values[this.elements[i].name] = this.elements[i].getValue();
		return values;
	}
});

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

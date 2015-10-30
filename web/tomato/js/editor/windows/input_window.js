var InputWindow = Window.extend({
	init: function(options) {
		this.element = new TextElement({name: options.inputname, onChangeFct: options.onChangeFct});
		this.element.setValue(options.inputvalue);
		this._super(options);
		var form = $('<form class="form-horizontal" role="form" />');
		var div = $('<div class="form-group"></div>');
		if(options.infotext) {
			var infotext = $('<div class="row"><div class="col-sm-12" style="margin-bottom:3pt;">'+options.infotext+'</div></div>');
			form.append(div.before(infotext));
		} else {
			form.append(div.before(infotext));
		}

		var label = $('<label for="newname" class="col-sm-4 control-label" />');
		label.append(options.inputlabel);
		div.append(label);
		div.append($('<div class="col-sm-8"/>').append(this.element.getElement()));
		
		this.add(form);
		this.setTitle(options.title);
	}
});

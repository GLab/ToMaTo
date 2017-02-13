var CommandTextElement = TextElement.extend({
	init: function(options){
		this._super(options);
		this.args_doc = options.args_doc;
		if (this.args_doc) {
			this.textfield.addClass("command-doc");
			this.element.append($('<pre class="command-doc">'+this.args_doc+'</pre>'));
		}
	}
});
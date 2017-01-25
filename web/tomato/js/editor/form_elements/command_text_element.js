var CommandTextElement = TextElement.extend({
	init: function(options){
		this._super(options);
		this.repy_doc = options.repy_doc
		this.element.append($('<pre>'+this.repy_doc+'</pre>'))
	}
});
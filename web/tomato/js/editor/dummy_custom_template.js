var DummyForCustomTemplate = Template.extend({
	init:function(original) {
		this._super(original.classoptions);
		this.subtype = "customimage";
		this.label = "Custom Image";
		this.description = "You have uploaded an own image. We cannot know anything about this. NlXTP modules may be missing.";
		this.nlXTP_installed = true;
		this.creation_date = undefined;
		this.restricted = false;
	}
})

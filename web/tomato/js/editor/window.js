var Window = Class.extend({
	init: function(options) {
		this.options = options;
		this.options.position = options.position || { my: "center center", at: "center center", of: "#editor" };
		var t = this;
		dialogOptions = {
			autoOpen: false,
			draggable: options.draggable != null ? options.draggable : true,
			resizable: options.resizable != null ? options.resizable : true,
			width: options.width || "",
			height: options.height || "auto",
			maxHeight:600,
			maxWidth:800,
			title: options.title,     
			autoResize: true,
			show: "slide",
			hide: "slide",
			minHeight:50,
			minWidth:250,
			modal: options.modal != null ? options.modal : true,
			buttons: options.buttons || {},
			closeOnEscape: false,
			close: function(event, ui) {
				if (!t.options.close_keep) {
					t.div.remove();
				}
			},
			open: function(event, ui) { 
				if (options.closable === false) $(".ui-dialog-titlebar-close").hide();
				t.setPosition(options.position);
			}
		};

		this.div = $('<div style="overflow:visible;"/>').dialog(dialogOptions);
		if (options.closeOnEscape != undefined)
			this.div.closeOnEscape = options.closeOnEscape;
		if (options.content) this.div.append($('<div style="min-height: auto;" />').append(options.content));

		

		
		this.helpButton = $('<div class="row" />');
		this.helpLinkPosition = $('<div class="col-md-1 col-md-offset-11" />');
		this.helpLink = $('<a><img style="cursor:pointer;" src="/img/help.png"></a></div>');
		
		this.helpLinkPosition.append(this.helpLink);
		
		var t = this;
		this.helpLink.click(function(){
			window.open(t.helpLinkTarget,'_help');
		});
		this.helpButton.append(this.helpLinkPosition);
		this.helpLinkTarget=help_baseUrl;

		this.div.append(this.helpButton);
		
		if(!options.helpTarget) {
			this.helpButton.hide();
		} else {
			this.helpLinkTarget = options.helpTarget;
		}
		
		if (options.autoShow) this.show();
		
	},
	setTitle: function(title) {
		this.div.dialog("option", "title", title);
	},
	setPosition: function(position) {
		this.div.dialog("option", "position", position);
	},
	show: function() {
		this.setPosition(this.options.position);
		this.div.dialog("open");
	},
	hide: function() {
		this.div.dialog("close");
	},
	remove: function() {
		var t = this;
		this.div.on("dialogclose", function() {
			t.div.dialog('destroy').remove();
		});
		this.div.dialog("close");
	},
	toggle: function() {
		if (this.div.dialog("isOpen")) this.hide();
		else this.show();
	},
	add: function(div) {
		this.div.append(div);
	},
	getDiv: function() {
		return this.div;
	}
});

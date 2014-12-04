// http://marijnhaverbeke.nl/uglifyjs

var settings = {
	childElementDistance: 25,
	commonPreferenceThreshold: 100,
	otherCommonElements: [
	                      {
	                  		label: "Switch",
	                		name: "vpn-switch",
	                		icon: "img/switch32.png",
	                		type: "tinc_vpn",
	                		attrs: {mode: "switch"}  
	                      }
	],
	supported_configwindow_help_pages: ['kvmqm','openvz','connection'],
}

var ignoreErrors = false;





var MenuGroup = Class.extend({
	init: function(name) {
		this.name = name;
		this.container = $('<li></li>');
		this.panel = $('<div></div>');
		this.container.append(this.panel);
		this.label = $('<h3><span>'+name+'</span></h3>');
		this.container.append(this.label);
	},
	addElement: function(element) {
		this.panel.append(element);
	},
	addStackedElements: function(elements) {
		var ul = $('<ul class="ui-ribbon-element ui-ribbon-list"></ul>');
		var count = 0;
		for (var i=0; i < elements.length; i++) {
			if (count >= 3) { //only 3 elements fit
				this.addElement(ul);
				ul = $('<ul class="ui-ribbon-element ui-ribbon-list"></ul>');
				count = 0;
			}			
			var li = $('<li></li>');
			li.append(elements[i]);
			ul.append(li);
			count++;
		}
		this.addElement(ul);
	}
});

var MenuTab = Class.extend({
	init: function(name) {
		this.name = name;
		this.div = $('<div id="menu_tab_'+name+'"></div>');
		this.link = $('<li><a href="'+window.location+'#menu_tab_'+name+'"><span><label>'+name+'</label></span></a></li>');
		this.panel = $('<ul></ul>');
		this.div.append(this.panel);
		this.groups = {};
	},
	addGroup: function(name) {
		var group = new MenuGroup(name);
		this.groups[name] = group;
		this.panel.append(group.container);
		return group;
	},
	getGroup: function(name) {
		return this.groups[name];
	}
});

var Menu = Class.extend({
	init: function(container) {
		this.container = container;
		this.tabs = {};
		this.tabLinks = $('<ul/>');
		this.container.append(this.tabLinks);
	},
	addTab: function(name) {
		var tab = new MenuTab(name);
		this.tabs[name] = tab;
		this.container.append(tab.div);
		this.tabLinks.append(tab.link);
		return tab;
	},
	getTab: function(name) {
		return this.tabs[name];
	},
	paint: function() {
		this.container.ribbon();
	}
});

Menu.button = function(options) {
	var html = $('<button class="ui-ribbon-element ui-ribbon-control ui-button"/>');
	if (options.toggle) {
		html.addClass("ui-button-toggle");
		if (options.toggleGroup) options.toggleGroup.add(html);
	}
	var icon = $('<span class="ui-button-icon ui-icon"></span>');
	if (options.small) {
		html.addClass("ui-ribbon-small-button");
		icon.addClass("icon-16x16");
	} else {
		html.addClass("ui-ribbon-large-button");
		icon.addClass("icon-32x32");
	}
	html.append(icon);
	html.append($('<span class="ui-button-label">'+options.label+'</span>'));
	if (options.func || options.toggle && options.toggleGroup) {
		html.click(function() {
			if (options.toggle && options.toggleGroup) options.toggleGroup.selected(this);
			if (options.func) options.func(this);	
		}); //must be done before call to button()
	}
	icon.css('background-image', 'url("'+options.icon+'")'); //must be done after call to button()
	html.button({tooltip: options.tooltip || options.label || options.name});
	html.attr("id", options.name || options.label);
	html.setChecked = function(value){
		this.toggleClass("ui-button-checked ui-state-highlight", value);
	}
	if (options.checked) html.setChecked(true);
	
	return html;
};

Menu.checkbox = function(options) {
	var html = $('<input type="checkbox" id="'+options.name+'"/><label for="'+options.name+'">'+options.label+'</label>');
	if (options.tooltip) html.attr("title", options.tooltip);
	if (options.func) html.click(function(){
		options.func(html.attr("checked"), html);
	});
	html.setChecked = function(value){
		this.attr("checked", value);
	}
	if (options.checked) html.setChecked(true);
	return html
};

var ToggleGroup = Class.extend({
	init: function() {
		this.buttons = [];
	},
	add: function(button) {
		this.buttons.push(button);
	},
	selected: function(button) {
		for (var i=0; i<this.buttons.length; i++)
			this.buttons[i].setChecked(this.buttons[i].attr("id") == $(button).attr("id"));
	}
});

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

var TextElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.pattern = options.pattern || /^.*$/;
		this.element = $('<div class="col-sm-12" />');
		this.textfield = $('<input class="form-control" type="'+(options.password ? "password" : "text")+'" name="'+this.name+'"/>');

		this.element.append(this.textfield);
		
		if (options.disabled) this.textfield.attr({disabled: true});
		if (options.onChangeFct) {
			this.textfield.change(options.onChangeFct);
			this.textfield.keypress(options.onChangeFct);
		}
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
	},
	isValid: function(value) {
		var val = value || this.getValue();
		return this.pattern.test(val);
	}
});

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

var CheckboxElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		
		this.element = $('<div class="col-sm-12">').append('<input class="form-element" type="checkbox" name="'+this.name+'"/>');
		if (options.disabled) this.element.attr({disabled: true});
		var t = this;
		this.element.change(function() {
			t.onChanged(this.checked);
		});
		if (options.value != null) this.setValue(options.value);
	},
	getValue: function() {
		return this.element[0].checked;
	},
	setValue: function(value) {
		this.element[0].checked = value;
	}
});

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
			this.element = $('<div class="col-sm-9" />');
			this.element.append(this.select);
			this.info = $('<div class="col-sm-3"></div>');
			this.element.after(this.info);
			
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

var TemplateElement = FormElement.extend({
	init: function(options) {
		this._super(options);
		this.options = options;
		this.disabled = options.disabled;
		this.call_element = options.call_element;
		
		this.element = $('<div style="display:none;"></div>');
		this.labelarea = $('<div class="col-sm-6"/>');
		this.changebuttonarea = $('<div class="col-sm-3"/>');
		this.infoarea = $('<div class="col-sm-3"/>');
		
		this.element.after(this.labelarea);
		this.element.after(this.changebuttonarea);
		this.element.after(this.infoarea);
		
		template = editor.templates.get(options.type,options.value);
		if (options.custom_template) {
			this.change_value(new DummyForCustomTemplate(template));
		} else {
			this.change_value(template);
		}
		
	},
	getValue: function() {
		return this.value;
	},
	
	change_value: function(template,loading) {
		this.value = template.name;
		this.template = template;
		var t = this;
		
		var changebutton = $('&nbsp;<button type="button" class="btn btn-primary"><span class="ui-button-text">Change</span></button>');
		changebutton.click(function() {
			t.call_element.showTemplateWindow(
				
				function(value) {
					t.change_value(
						editor.templates.get(
							t.options.type,value
						),
						true
					);
				},
					
				function(value) {
					t.change_value(
						editor.templates.get(
							t.options.type,value
						),
						false
					);
				}
				
			);
		})
		
		if (this.disabled || loading) {
			changebutton.prop("disabled",true);
		}
		
		this.labelarea.empty();
		this.changebuttonarea.empty();
		this.infoarea.empty();
		
		this.labelarea.append(this.template.label);
		this.changebuttonarea.append(changebutton);
		this.infoarea.append($(this.template.infobox()));
		
		if (loading) {
			this.labelarea.append($(' <img src="/img/loading.gif" />'));
		}
	}
});

var Window = Class.extend({
	init: function(options) {
		log(options);
		this.options = options;
		this.options.position = options.position || ['center',200];
		this.div = $('<div style="overflow:visible;"/>').dialog({
			autoOpen: false,
			draggable: options.draggable != null ? options.draggable : true,
			resizable: options.resizable != null ? options.resizable : true,
			height: options.height || "auto",
			width: options.width || "",
			maxHeight:600,
			maxWidth:800,
			title: options.title,
			show: "slide",
			hide: "slide",
			minHeight:50,
			minWidth:250,
			modal: options.modal != null ? options.modal : true,
			buttons: options.buttons || {},
			closeOnEscape: false,
			open: function(event, ui) { 
				if (options.closable === false) $(".ui-dialog-titlebar-close").hide(); 
			}
		});
		if (options.closeOnEscape != undefined)
			this.div.closeOnEscape = options.closeOnEscape;
		this.setPosition(options.position);
		if (options.content) this.div.append(options.content);
		if (options.autoShow) this.show();
		

		
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
		
	},
	setTitle: function(title) {
		this.div.dialog("option", "title", title);
	},
	setPosition: function(position) {
		this.div.dialog("option", "position", position);
	},
	show: function() {
		this.setPosition(this.position);
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
var showError = function(error) {
	
	if (ignoreErrors) return;
	switch(error.toLowerCase()) {
		case "over quota":
			var overquotastr = "You are over quota. If you are a newly registered user, please wait until your account has been approved. Otherwise, contact an administrator.";
			
			errorWindow({error: {originalResponse: overquotastr,},userErrorFlag: true});
			break;
		default:
			var errWindow = new errorWindow({error: { originalResponse: error,},userErrorFlag: true});
	}
}


var errorWindow = Window.extend({
	init: function(options) {
		var t = this;
		this.windowOptions = {title: "Error",
				modal: true,
				width: 600,
				autoShow: true,
				buttons: {
					Okay: function() {
						t.remove();
						t = null;
					}
				},
				userErrorFlag: false,
				error_message_appendix: editor.options.error_message_appendix,
			};
		
		//Copy error to new variable and remove it from the options dict
		var error = options.error;
		delete options.error;
		
		for (var key in options) {
			this.windowOptions[key] = options[key];
		}
		this._super(this.windowOptions);
		
		//Create the content of the error window
		this.errorContent = $('<div>');

		console.log(error);
		
		if(error.parsedResponse) {
			this.errorContent.after(this.addError(error.parsedResponse.error));
		} else {
			this.errorContent.after(this.addText(error.originalResponse));
		}
		
		if(!(editor.options.isDebugUser || editor.options.debug_mode) && !options.userErrorFlag) {
			this.errorContent.after('<p style="color: #a0a0a0">'+this.options.error_message_appendix+'</p>');
		}
		this.errorContent.after($('</div>'));
		this.div.append(this.errorContent);
	},

	addError: function(error) {
		//Show additional information for debug users like the errorcode, the errormessage and errordata for debugusers
		var content = $('');
		
		this.setTitle("Error: "+error.typemsg);
		
		var errorMessage = $('<p>'+error.errormsg+'</p>');
		content.after(errorMessage);
		
		if(editor.options.isDebugUser && editor.options.debug_mode) {
			
			content.after($('<b>Error details:</b>'))
			var errorDebugInfos = $('<table />');
			
			for(var line=0;line<error.debuginfos.length;line++) {
				errorDebugInfos.append($('<tr><th>'+error.debuginfos[line].th+'</th><td>'+error.debuginfos[line].td+'</td></tr>'));
			}
			content.after(errorDebugInfos);
		}
		return content;
	},
	
	addText: function(text) {
		var message = $('<p>'+text.replace(/(\r\n)|(\r)|(\n)/g, '<br />')+'</p>');
		return message;
	}
});


var ajax = function(options) {
	var t = this;
	$.ajax({
		type: "POST",
	 	async: true,
	 	url: "../ajax/" + options.url,
	 	data: {data: $.toJSON(options.data || {})},
	 	complete: function(res) {
	 		if (res.status == 401 || res.status == 403) {
	 			showError("Your session has ended, please log in again");
	 			ignoreErrors=true;
	 			window.location.reload();
	 			return;
	 		}
	 		var	errorobject = {originalResponse: res.responseText,responseCode: res.status};
	 		var msg = res.responseText;
	 		try {
	 			msg = $.parseJSON(res.responseText);
 				errorobject.parsedResponse = msg;
 			} catch (e){
 			}
	 		if (res.status != 200) {
	 			return options.errorFn ? options.errorFn(errorobject) : null;
 			}
	 		if (! msg.success) {
	 			return options.errorFn ? options.errorFn(errorobject) : null;
	 		}
	 		return options.successFn ? options.successFn(msg.result) : null;
	 	}
	});
};

var TutorialWindow = Window.extend({
	init: function(options) {
			this._super(options);
			if (options.hideCloseButton)
				$(this.div.parent()[0].getElementsByClassName("ui-dialog-titlebar-close")).hide();
			
			if (!options.tutorialVisible)
				return;
				
			this.editor = options.editor
				
			this.tutorialStatus = options.tutorial_status || 0;
			
			//create UI
			var t = this
			this.text = $("<div>.</div>");
			this.buttons = $("<p style=\"text-align:right; margin-bottom:0px; padding-bottom:0px;\"></p>");
			this.backButton = $("<input type=\"button\" value=\"Back\" />");
			this.buttons.append(this.backButton);
			this.backButton.click(function() {t.tutorialGoBack(); });
			this.skipButton = $("<input type=\"button\" value=\"Skip\" />");
			this.buttons.append(this.skipButton);
			this.skipButton.click(function() {t.tutorialGoForth(); });
			this.closeButton = $("<input type=\"button\" value=\"Close Tutorial\" />");
			this.buttons.append(this.closeButton);
			
			this.closeButton.click(function() {
				t.setTutorialVisible(false);
			});
			
			this.add(this.text);
			this.add(this.buttons);
			
			this.tutorialVisible = true;
			if (options.tutorialVisible != undefined) {
				this.setTutorialVisible(options.tutorialVisible);
			}
			
			//load the basic tutorial at the creating of the editor.
			this.tutorialSteps = [];
			this.loadTutorial();
			
	},
	setTutorialVisible: function(vis) {  //vis==true: show tutorial. vis==false: hide tutorial.
		if (vis) {
			this.show();
		} else {
			this.hide();
			this.closeTutorial();
		}
		this.tutorialVisible = vis;
	},
	tutorialGoBack: function() {
		if (this.tutorialStatus > 0) {
			this.tutorialStatus--;
			this.skipButton.show();
			this.closeButton.hide();
		}
		if (this.tutorialStatus == 0) {
			this.backButton.hide();
		}
		this.updateText();
		this.updateStatusToBackend();
	},
	tutorialGoForth: function() {
		if (this.tutorialStatus + 1 < this.tutorialSteps.length) {
			this.tutorialStatus++;	
			this.backButton.show();
		}
		if (this.tutorialStatus + 1 == this.tutorialSteps.length) {
			this.skipButton.hide();
			this.closeButton.show();
		}
		this.updateText();
		this.updateStatusToBackend();
	},
	triggerProgress: function(triggerObj) { //continues tutorial if correct trigger
		if (this.tutorialVisible) { //don't waste cpu time if not needed... trigger function may be complex.
			if (this.tutorialSteps[this.tutorialStatus].trigger != undefined) {
				if (this.tutorialSteps[this.tutorialStatus].trigger(triggerObj)) {
					this.tutorialGoForth();
				}
			}
		}
	},
	loadTutorial: function() {//loads editor_tutorial.tutName; tutID: position in "tutorials" array
		//load tutorial
		this.tutorialSteps = tutorial_steps
		
		//set visible buttons
		if (this.tutorialStatus == 0) {
			this.backButton.hide();
			this.skipButton.show();
			this.closeButton.hide();
		} else {
			this.backButton.show();
			if (this.tutorialStatus == this.tutorialSteps.length - 1) {
				this.skipButton.hide();
				this.closeButton.show();
			} else {
				this.skipButton.show();
				this.closeButton.hide();
			}
		}
		
		//show text
		this.updateText();
	},
	updateText: function() {
		if (!this.tutorialVisible) return;
		var text = this.tutorialSteps[this.tutorialStatus].text;
		this.text.empty();
		this.text.append(text);

		this.setTitle("Tutorial [" + (this.tutorialStatus+1) + "/" + this.tutorialSteps.length + "]");
		
		//dirty hack: un-set the window's height property
		this.div[0].style.height = "";
		
		var helpUrl=this.tutorialSteps[this.tutorialStatus].help_page;
		if (helpUrl) {
			this.helpLinkTarget=help_baseUrl+"/"+helpUrl;
			this.helpButton.show();
		} else {
			this.helpButton.hide();
		}
		
		var skipButtonText = this.tutorialSteps[this.tutorialStatus].skip_button;
		if (skipButtonText) {
			this.skipButton[0].value = skipButtonText;
		} else {
			this.skipButton[0].value = "Skip";
		}
	},
	updateStatusToBackend: function() {
		ajax({
			url: 'topology/'+this.editor.topology.id+'/modify',
		 	data: {attrs: {
		 					_tutorial_status: this.tutorialStatus
		 					},
		 			}
		});
	},
	closeTutorial: function() {
		var t = this
		if (confirm("You have completed the tutorial. This topology will now be removed. (Press \"Cancel\" to keep the topology)")) {
			this.editor.topology.remove();	
		} else {
			ajax({
				url: 'topology/'+this.editor.topology.id+'/modify',
			 	data: {attrs: {
			 					_tutorial_disabled: true
			 					},
			 			}
			});
		}
	}
	
	
});

var AttributeWindow = Window.extend({
	init: function(options) {
		this._super(options);
		this.table = $('<form class="form-horizontal" role="form"></form>');
		this.div.append(this.table);
		this.elements = [];
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
		if (info.options) {
			el = new ChoiceElement({
				label: info.desc || info.name,
				name: info.name,
				choices: info.options,
				value: value || info["default"],
				disabled: !enabled
			});
		} else if (info.type == "bool") {
			el = new CheckboxElement({
				label: info.desc || info.name,
				name: info.name,
				value: value || info["default"],
				disabled: !enabled
			});
		} else {
			var converter = null;
			switch (info.type) {
				case "int":
					converter = parseInt;
					break;
				case "float":
					converter = parseFloat;
					break;
			}
			el = new TextElement({
				label: info.desc || info.name,
				name: info.name,
				value: value || info["default"],
				disabled: !enabled,
				inputConverter: converter 
			});
		}
		return el;
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
		label.after($('<div class="col-sm-8"/>').append(this.element.getElement()));
		
		div.append(label);
		this.add(form);
		this.setTitle(options.title);
	}
});

var TemplateWindow = Window.extend({
	init: function(options) {
		
		var t = this;
		options.buttons = [ 

		                    {
		                    	text: "Save",
		                    	click: function() {
		                			t.hide();
		                    		t.callback_before_finish(t.getValue());
		                			t.save();
		                		}
		         
		                    },
		                    {
		                    	text: "Cancel",
		                    	click: function() {
		                			t.hide();
		                		}
		                    }];
		
		this._super(options);
		this.element = options.element;
		var windowTitle = "Change Template for "+this.element.data.attrs.name;
		if (editor.options.show_ids) windowTitle = windowTitle + ' (#'+this.element.data.id+')'
		this.setTitle(windowTitle);
		if (options.disabled == undefined || options.disabled == null) {
			this.disabled = false;
		} else {
			this.disabled = options.disabled;
		}
		
		this.callback = function(value) {};
		if (options.callback_after_finish != undefined && options.callback_after_finish != null) {
			this.callback_after_finish = options.callback_after_finish;
		} else {
			this.callback_after_finish = function(value) {};
		}
		
		if (options.callback_before_finish != undefined && options.callback_before_finish != null) {
			this.callback_before_finish = options.callback_before_finish;
		} else {
			this.callback_before_finish = function(value) {};
		}
		
		this.disable_restricted = !(editor.allowRestrictedTemplates);
		
		
		
		this.value = this.element.data.attrs.template;
		this.choices = editor.templates.getAll(this.element.data.type);
		
		var table = this.getList();
		
		
		this.div.append($('<div style="margin-bottom:0.5cm; margin-top:0.5cm;"><table style="vertical-align:top;"><tr><th style="vertical-align:top;">Warning:</th><td style="vertical-align:top; font-size: 10pt; white-space:normal; font-style:italic;">You will lose all data on this device if you change the template.</td></tr></table></div>'));
		this.div.append(table);
	},
	getValue: function() {
		return this.value;
	},
	save: function() {
		var t = this;
		this.element.changeTemplate(
			this.getValue(),
			function(){
				t.callback_after_finish(t.getValue());
			}
		);
	},
	getList: function() {
		var form = $('<form class="form-horizontal"></form>');
		var ths = this;

		//build template list entry
		var div_formgroup = $('<div class="form-group"></div>');
		for(var i=0; i<this.choices.length; i++) {
			var t = this.choices[i];
			
			
			

			
			var div_option = $('<div class="col-md-10" />');
			var div_radio = $('<div class="radio"></div>');
			div_option.append(div_radio);
			var radio = $('<input type="radio" name="template" value="'+t.name+'" />');
			
			if (this.disabled) {
				radio.prop("disabled",true);
			} else {
				radio.change(function() {
					ths.value = this.value;
				});
			}
			
			if (this.disable_restricted && t.restricted) {
				radio.prop("disabled",true);
			}
			
			if (t.name == this.element.data.attrs.template) {
				radio.prop("checked","checked");
			}
			
			var radiolabel = $('<label for="'+t.name+'">'+t.label+'</label>')
			div_radio.append(radiolabel);
			radiolabel.prepend(radio);
			var div_info = $('<div class="col-md-2" />');
			div_info.append(t.infobox());
			
			div_formgroup.append(div_option);
			div_formgroup.append(div_info);
			
			form.append(div_formgroup);
		}
		
		return form;
	}
});

var PermissionsWindow = Window.extend({
	init: function(options) {
		options.modal = true;
		
		var t = this;
		this.options = options;
		this.topology = options.topology;
		this.permissions = options.permissions;
		
		this.options.allowChange = this.options.isGlobalOwner;
		
		
		var closebutton = {
		                    	text: "Close",
		                    	id: "permwindow-close-button",
		                    	click: function() {
		                			t.hide();
		                		}
		         
		                    };
		var addbutton = {
		                    	text: "Add User",
		                    	id: "permwindow-add-button",
		                    	click: function() {
		                    		t.addNewUser();
		                    	}
		                    };

		this.options.buttons=[closebutton,addbutton];
		
		
		this._super(this.options);

		
		this.editingList = {};
		
		this.userList = $('<div />');
		this.userListFinder = {};
		this.div.append(this.userList);
		this.listCreated = false;
		
		this.buttons = $('<div />');
		this.div.append(this.buttons);
		
		this.closeButton = $("#permwindow-close-button");
		this.addButton = $("#permwindow-add-button");
		
	},
	
	disableClose: function() {
		this.closeButton.attr("disabled",true);
		$(this.div.parent()[0].getElementsByClassName("ui-dialog-titlebar-close")).hide();
	},
	enableClose: function() {
		this.closeButton.attr("disabled",false);
		$(this.div.parent()[0].getElementsByClassName("ui-dialog-titlebar-close")).show();
	},
	checkEnableDisableClose: function() {
		var disable = false;
		for (i in this.editingList) {
			disable = disable || this.editingList[i];
		}
		if (disable) {
			this.disableClose();
		} else {
			this.enableClose();
		}
	},
	
	createUserPermList: function() {
		var t = this;
		
		if (this.listCreated) return;
		this.listCreated = true;
		
		if (!this.options.allowChange) {
			this.options.allowChange = (this.topology.data.permissions[this.options.ownUserId] == "owner");
		}
		if (!this.options.allowChange) {
			this.addButton.attr("disabled",true);
		}
		
		
		this.userTable = $('<div class="row"><div class="col-sm-4 col-sm-offset-1"><h4>User</h4></div><div class="col-sm-4"><h4>Permission</h4></div></div>');
		if (this.options.allowChange) this.userTable.append($('<div class="col-sm-3" />'));
		this.userList.append(this.userTable);
		var perm = this.topology.data.permissions;
		for (u in perm) {
			if (perm[u] != null)
				this.addUserToList(u);
		}
	},
	
	addUserToList: function(username) {
		var t = this;
		var tr = $('<div class="row" />');
		var td_name = $('<div class="col-sm-4" />');
		var td_perm = $('<div class="col-sm-4" />');
		var td_buttons = $('<div class="col-sm-3" />');
		var td_icon = $('<div class="col-sm-1" />');
	
		
		ajax({
			url:	'account/'+username+'/info',
			successFn: function(data) {
				var s = data.realname+' (<a href="/account/info/'+data.id+'" target="_blank" style="font-size:10pt;">'+data.id+'</a>)'
				td_name.append($(s));
				if (data.id == t.options.ownUserId) td_icon.append($('<img src="/img/user.png" title="This is you!" />'));
			}
		});

		tr.append(td_icon);
		tr.append(td_name);
		tr.append(td_perm);
		if (this.options.allowChange) tr.append(td_buttons);
		this.userListFinder[username] = {
				td_icon: td_icon,
				td_name: td_name,
				td_perm: td_perm,
				td_buttons: td_buttons,
				tr: tr
		};
		this.userTable.after(tr);
		
		this.drawView(username);
	},
	
	addNewUser: function() {
		var t = this;
		this.username = new InputWindow({
			title: "New User",
			width: 550,
			height: 200,
			zIndex: 1000,
			inputname: "newuser",
			inputlabel: "Username:",
			infotext: "Please enter the user's username:",
			inputvalue: "",
			buttons: [
						{ 
							text: "Add User",
							click: function() {
								t.username.hide();
								if (t.username.element.getValue() != '') ajax({
									url:	'account/'+t.username.element.getValue()+'/info',
									successFn: function(data) {
										if (!(data.id in t.userListFinder)) {
											if (window.confirm("Found the user "+ data.realname + ' (' + data.id +")\nIs this correct?")) {
												t.addUserToList(data.id);
												t.makePermissionEditable(data.id);
											}
										} else
											showError("This user is already in the list.");
									},
									errorFn: function(error) {
								 		this.errorWindow = new errorWindow({error:error});
									},
								});
								t.username = null;
							}
						},
						{
							text: "Cancel",
							click: function() {
								t.username.hide();
								t.username = null;
							}
						}
			],
		});
		this.username.show();
	},
	
	removeUserFromList: function(username) {
		this.userListFinder[username].tr.remove();
		this.editingList[username] = false;
		this.checkEnableDisableClose();
		delete this.userListFinder[username];
	},
	
	makePermissionEditable: function(username) {
		if (!this.options.allowChange || this.username == this.options.ownUserId) return;
		
		var t = this;
		td_perm = this.userListFinder[username].td_perm;
		td_buttons = this.userListFinder[username].td_buttons;
		permission = this.topology.data.permissions[username];
		td_perm.empty();
		td_buttons.empty();
		var sel_id='permissions_'+username;
		
		var div = $('<div class="col-sm-10"/>');
		var sel=$('<select name="sel" id="'+sel_id+'"></select>');
		div.append(sel);
		for (perm in this.permissions) {
			if (perm != "null")
				sel.append($('<option value="'+perm+'" title="'+this.permissions[perm].description+'">'+this.permissions[perm].title+'</option>'));
		}
		sel.change(function(){ sel[0].title = t.permissions[sel[0].value].description });
		
		if ((permission == undefined) || (permission == null))
			permission = 'null';
		sel.val(permission);
		sel.change();
		td_perm.append(sel);
		
		var saveButton = $('<img src="/img/tick.png" title="save" style="cursor:pointer;" />');
		saveButton.click(function() {
			var sel = document.getElementById(sel_id);
			var perm = sel.options[sel.selectedIndex].value;
			t.setPermission(username, perm);
		});
		td_buttons.append(saveButton);
		
		var cancelButton = $('<img src="/img/eraser16.png" title="cancel" style="cursor:pointer;" />');
		cancelButton.click(function(){
			t.backToView(username);
		});
		td_buttons.append(cancelButton);
		
		this.editingList[username] = true;
		this.checkEnableDisableClose();
	},
	
	setPermission: function(username, permission) {
		if (!this.options.allowChange || this.username == this.options.ownUserId) return;
		
		var t = this;
		
		var perm_send = null;
		if (permission != 'null')
			perm_send = permission;
		
		ajax({
			url: 'topology/'+this.topology.id+'/permission',
			data: {user: username, permission: perm_send},
			successFn: function(){ 
				if (permission != null) {
					t.topology.data.permissions[username]=permission;
				} else {
					delete t.topology.data.permissions[username];
				}		
				if (perm_send == null) {
					t.removeUserFromList(username)
				} else {
					t.backToView(username);
				}
			},
			errorFn: function(error){
		 		this.errorWindow = new errorWindow({error:error});
				t.backToView(username);
			}
		})
	},
	
	backToView: function(username) {
		if (username in this.topology.data.permissions && this.topology.data.permissions != null) {
			this.drawView(username);
		} else {
			this.removeUserFromList(username);
		}
	},
	drawView: function(username) {
		var t = this;
		
		var permission = '<div class="hoverdescription">'+this.permissions['null'].title+'</div>';
		if (username in this.topology.data.permissions) {
			permission_var = this.topology.data.permissions[username];
			permission = $('<span title="'+this.permissions[permission_var].description+'">'+this.permissions[permission_var].title+'</span>');
			//permission = $('<div class="hoverdescription">'+this.permissions[permission_var].title+'<div class="hiddenbox"><p>'+ this.permissions[permission_var].description +'</p></div></div>')
		}
		
		var td_perm = this.userListFinder[username].td_perm;
		var td_buttons = this.userListFinder[username].td_buttons;
		td_perm.empty();
		td_buttons.empty();
		
		td_perm.append(permission);
		
		if (username != this.options.ownUserId) {
			var editButton = $('<img src="/img/pencil.png" title="edit permissions" style="cursor:pointer;" />');
			editButton.click(function(){
				t.makePermissionEditable(username);
			});
			td_buttons.append(editButton);
			
			var removeButton = $('<img src="/img/cross.png" title="remove from list" style="cursor:pointer;" />');
			removeButton.click(function(){
				t.setPermission(username,null);
			})
			td_buttons.append(removeButton);
			this.editingList[username] = false;
			this.checkEnableDisableClose();
		}
		
	}
	
	
});

var Workspace = Class.extend({
	init: function(container, editor) {
		this.container = container;
		this.editor = editor;
		container.addClass("ui-widget-content").addClass("ui-corner-all")
		container.addClass("tomato").addClass("workspace");
		container[0].obj = editor.topology;
		this.container.click(function(){});
    	this.size = {x: this.container.width(), y: this.container.height()};
    	this.canvas = Raphael(this.container[0], this.size.x, this.size.y);
    	var c = this.canvas;
		var fs = this.editor.options.frame_size;
    	this.canvas.absPos = function(pos) {
    		return {x: fs + pos.x * (c.width-2*fs), y: fs + pos.y * (c.height-2*fs)};
    	}
    	this.canvas.relPos = function(pos) {
    		return {x: (pos.x - fs) / (c.width-2*fs), y: (pos.y - fs) / (c.height-2*fs)};
    	}
    	
    	//tutorial UI
    	this.tutorialWindow = new TutorialWindow({ 
			autoOpen: false, 
			draggable: true,  
			resizable: false, 
			title: ".", 
			modal: false, 
			buttons: {},
			width:500,
			closeOnEscape: false,
			tutorialVisible:this.editor.options.tutorial,
			tutorial_status:this.editor.options.tutorial_status,
			hideCloseButton: true,
			editor: this.editor
		});
    	
    	this.permissionsWindow = new PermissionsWindow({
    		autoOpen: false,
    		draggable: true,
    		resizable: false,
    		title: "Permissions",
    		modal: false,
    		width: 500,
    		topology: this.editor.topology,
    		isGlobalOwner: this.editor.options.isGlobalOwner, //todo: set value depending on user permissions
    		ownUserId: this.editor.options.user.id,
    		permissions: this.editor.options.permission_list
    	});
    	
    	var t = this;
    	this.editor.listeners.push(function(obj){
    		t.tutorialWindow.triggerProgress(obj);
    	});
    	
    	
		this.connectPath = this.canvas.path("M0 0L0 0").attr({"stroke-dasharray": "- "});
		this.container.click(function(evt){
			t.onClicked(evt);
		});
		this.container.mousemove(function(evt){
			t.onMouseMove(evt);
		});
		this.busyIcon = this.canvas.image("img/loading_big.gif", this.size.x/2, this.size.y/2, 32, 32);
		this.busyIcon.attr({opacity: 0.0});
	},
	
	setBusy: function(busy) {
		this.busyIcon.attr({opacity: busy ? 1.0 : 0.0});
	},
	
	
	onMouseMove: function(evt) {
		if (! this.editor.connectElement) {
			this.connectPath.hide();
			return;
		}
		this.connectPath.show();
		var pos = this.editor.connectElement.getAbsPos();
		var mousePos = {x: evt.pageX - this.container.offset().left, y: evt.pageY - this.container.offset().top};
		this.connectPath.attr({path: "M"+pos.x+" "+pos.y+"L"+mousePos.x+" "+mousePos.y});
	},
	onClicked: function(evt) {
		switch (this.editor.mode) {
			case Mode.position:
				var pos;
				if (evt.offsetX) pos = this.canvas.relPos({x: evt.offsetX, y: evt.offsetY});
				else {
					var objPos = this.container.offset();
					pos = this.canvas.relPos({x: evt.pageX - objPos.left, y: evt.pageY - objPos.top});
				}
				this.editor.positionElement(pos);
				break;
			default:
				break;
		}
	},
	onOptionChanged: function(name) {
    		this.tutorialWindow.updateText();
	},
	onModeChanged: function(mode) {
		for (var name in Mode) this.container.removeClass("mode_" + Mode[name]);
		this.container.addClass("mode_" + mode);
	},
	
	updateTopologyTitle: function() {
		var t = editor.topology;
		var new_name="Topology '"+t.data.attrs.name+"'"+(editor.options.show_ids ? " [#"+t.id+"]" : "");
		$('#topology_name').text(new_name);
		document.title = new_name+" - G-Lab ToMaTo";
	}
});

var Topology = Class.extend({
	init: function(editor) {
		this.editor = editor;
		this.elements = {};
		this.connections = {};
		this.pendingNames = [];
	},
	_getCanvas: function() {
		return this.editor.workspace.canvas;
	},
	loadElement: function(el) {
		var elObj;
		switch (el.type) {
			case "kvm":
			case "kvmqm":
			case "openvz":
			case "repy":
				elObj = new VMElement(this, el, this._getCanvas());
				break;
			case "kvm_interface":
			case "kvmqm_interface":
			case "repy_interface":
				elObj = new VMInterfaceElement(this, el, this._getCanvas());
				break;
			case "openvz_interface":
				elObj = new VMConfigurableInterfaceElement(this, el, this._getCanvas());
				break;
			case "external_network":
				elObj = new ExternalNetworkElement(this, el, this._getCanvas());
				break;
			case "external_network_endpoint":
				//hide external network endpoints with external_network parent but show endpoints without parent 
				elObj = el.parent ? new SwitchPortElement(this, el, this._getCanvas()) : new ExternalNetworkElement(this, el, this._getCanvas()) ;
				break;
			case "tinc_vpn":
				elObj = new VPNElement(this, el, this._getCanvas());
				break;
			case "tinc_endpoint":
				//hide tinc endpoints with tinc_vpn parent but show endpoints without parent 
				elObj = el.parent ? new SwitchPortElement(this, el, this._getCanvas()) : new VPNElement(this, el, this._getCanvas()) ;
				break;
			default:
				elObj = new UnknownElement(this, el, this._getCanvas());
				break;
		}
		if (el.id) this.elements[el.id] = elObj;
		if (el.parent) {
			//parent id is less and thus objects exists
			elObj.parent = this.elements[el.parent];
			this.elements[el.parent].children.push(elObj);
		}
		elObj.paint();
		return elObj;
	},
	loadConnection: function(con, elements) {
		var conObj = new Connection(this, con, this._getCanvas());
		if (con.id) this.connections[con.id] = conObj;
		if (con.elements) { //elements are given by id
			for (var j=0; j<con.elements.length; j++) {
				this.elements[con.elements[j]].connection = conObj;
				conObj.elements.push(this.elements[con.elements[j]]);
			}
		} else { //elements are given by object reference 
			for (var j=0; j<elements.length; j++) {
				elements[j].connection = conObj;
				conObj.elements.push(elements[j]);
			}
		}
		conObj.paint();
		return conObj;
	},
	load: function(data) {
		this.data = data;
		this.id = data.id;
		this.elements = {};
		//sort elements by id so parents get loaded before children
		data.elements.sort(function(a, b){return a.id - b.id;});
		for (var i=0; i<data.elements.length; i++) this.loadElement(data.elements[i]);
		this.connections = {};
		for (var i=0; i<data.connections.length; i++) this.loadConnection(data.connections[i]);
		
		this.settingOptions = true;
		var opts = ["safe_mode", "snap_to_grid", "fixed_pos", "colorify_segments", "debug_mode", "show_ids", "show_sites_on_elements"];
		for (var i = 0; i < opts.length; i++) {
			if (this.data.attrs["_"+opts[i]] != null) this.editor.setOption(opts[i], this.data.attrs["_"+opts[i]]);
		}
		this.settingOptions = false;		

		this.onUpdate();
	},
	setBusy: function(busy) {
		this.busy = busy;
	},
	configWindowSettings: function() {
		return {
			order: ["name"],
			ignore: [],
			unknown: true,
			special: {}
		}
	},
	showConfigWindow: function(callback) {
		var t = this;
		var settings = this.configWindowSettings();

		this.configWindow = new AttributeWindow({
			title: "Attributes",
			width: "600",
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) {
						if (values[name] === t.data.attrs[name]) delete values[name];
						// Tread "" like null
						if (values[name] === "" && t.data.attrs[name] === null) delete values[name];
					}
					t.modify(values);
					t.configWindow.remove();
					t.configWindow = null;

					if(callback != null) {
						callback(t);
					}
				},
				Cancel: function() {
					t.configWindow.remove();
					t.configWindow = null;
				}
			}
		});
        this.configWindow.add(new TextElement({
				label: "Name",
				name: "name",
				value: this.data.attrs.name,
				disabled: false
		}));
		this.configWindow.add(new ChoiceElement({
			label: "Site",
			name: "site",
			choices: createMap(this.editor.sites, "name", function(site) {
				return (site.description || site.name) + (site.location ? (", " + site.location) : "");
			}, {"": "Any site"}),
			value: this.data.attrs.site,
			disabled: false
		}));
		this.configWindow.show();
	},
	modify: function(attrs) {
		this.setBusy(true);
		this.editor.triggerEvent({component: "topology", object: this, operation: "modify", phase: "begin", attrs: attrs});
		var t = this;
		ajax({
			url: 'topology/'+this.id+'/modify',
		 	data: {attrs: attrs},
		 	successFn: function(result) {
				t.editor.triggerEvent({component: "topology", object: this, operation: "modify", phase: "end", attrs: attrs});
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
				t.editor.triggerEvent({component: "topology", object: this, operation: "modify", phase: "error", attrs: attrs});
		 	}
		});
		for (var name in attrs) {
		    this.data.attrs[name] = attrs[name];
    		if (name == "name") editor.workspace.updateTopologyTitle();
		}
	},
	action: function(action, options) {
		var options = options || {};
		var params = options.params || {};
		this.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "begin", action: action, params: params});
		var t = this;
		ajax({
			url: 'topology/'+this.id+'/action',
		 	data: {action: action, params: params},
		 	successFn: function(result) {
		 		var data = result[1];
		 		t.data.timeout = data.timeout;
		 		t.data.attrs = data.attrs;
				t.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "end", action: action, params: params});
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
				t.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "error", action: action, params: params});
		 	}
		});
	},
	modify_value: function(name, value) {
		var attrs = {};
		attrs[name] = value;
		this.modify(attrs);
		if (name == "name") editor.workspace.updateTopologyTitle();
	},
	isEmpty: function() {
		for (var id in this.elements) if (this.elements[id] != this.elements[id].constructor.prototype[id]) return false;
		return true;
		//no connections without elements
	},
	elementCount: function() {
		var count = 0;
		for (var id in this.elements) count++;
		return count;
	},
	connectionCount: function() {
		var count = 0;
		for (var id in this.connections) count++;
		return count;
	},
	nextElementName: function(data) {
		var names = [];
		for (var id in this.elements) names.push(this.elements[id].data.attrs.name);
		var base;
		switch (data.type) {
			case "external_network":
				base = data.attrs.kind || "internet";
				break;
			case "external_network_endpoint":
				base = (data.attrs.kind || "internet") + "_endpoint";
				break;		
			case "tinc_vpn":
				base = data.attrs.mode || "switch";
				break;
			case "tinc_endpoint":
				base = "tinc";
				break;		
			default:
				if (data.attrs && data.attrs.template) {
					base = editor.templates.get(data.type, data.attrs.template).label;
				} else {
					base = data.type;
				}
		}
		base = base+" #";
		var num = 1;
		while (names.indexOf(base+num) != -1 || this.pendingNames.indexOf(base+num) != -1) num++;
		return base+num;
	},
	createElement: function(data, callback) {
		data.attrs = data.attrs || {};
		if (!data.parent) data.attrs.name = data.attrs.name || this.nextElementName(data);
		var obj = this.loadElement(data);
		this.editor.triggerEvent({component: "element", object: obj, operation: "create", phase: "begin", attrs: data});
		obj.setBusy(true);
		this.pendingNames.push(data.name);
		var t = this;
		ajax({
			url: "topology/" + this.id + "/create_element",
			data: data,
			successFn: function(data) {
				t.pendingNames.remove(data.name);
				t.elements[data.id] = obj;
				obj.setBusy(false);
				obj.updateData(data);
				if (callback) callback(obj);
				t.editor.triggerEvent({component: "element", object: obj, operation: "create", phase: "end", attrs: data});
				t.onUpdate();
			},
			errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
				obj.paintRemove();
				t.pendingNames.remove(data.name);
				t.editor.triggerEvent({component: "element", object: obj, operation: "create", phase: "error", attrs: data});
			}
		});
		return obj;
	},
	createConnection: function(el1, el2, data) {
		if (el1 == el2) return;
		if (! el1.isConnectable()) return;
		if (! el2.isConnectable()) return;
		var ids = 0;
		var t = this;
		var obj;
		var callback = function(ready) {
			ids++;
			if (ids < 2) return;
			t.editor.triggerEvent({component: "connection", object: obj, operation: "create", phase: "begin", attrs: data});
			data.elements = [el1.id, el2.id];
			ajax({
				url: "connection/create",
				data: data,
				successFn: function(data) {
					t.connections[data.id] = obj;
					obj.updateData(data);
					t.editor.triggerEvent({component: "connection", object: obj, operation: "create", phase: "end", attrs: data});
					t.onUpdate();
					el1.onConnected();
					el2.onConnected();
				},
				errorFn: function(error) {
			 		this.errorWindow = new errorWindow({error:error});
					obj.paintRemove();
					t.editor.triggerEvent({component: "connection", object: obj, operation: "create", phase: "error", attrs: data});
				}
			});
		};
		el1 = el1.getConnectTarget(callback);
		el2 = el2.getConnectTarget(callback);
		data = data || {};
		data.attrs = data.attrs || {};
		obj = this.loadConnection(copy(data, true), [el1, el2]);
		return obj;
	},
	onOptionChanged: function(name) {
		if (this.settingOptions) return;
		this.modify_value("_" + name, this.editor.options[name]);
		this.onUpdate();
	},
	action_delegate: function(action, options) {
		var options = options || {};
		if ((action=="destroy"||action=="stop") && !options.noask && this.editor.options.safe_mode && ! confirm("Do you want to " + action + " this topology?")) return;
		this.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "begin", action: action});
		var ids = 0;
		var t = this;
		var cb = function() {
			ids--;
			if (ids <= 0 && options.callback) options.callback();
			t.editor.triggerEvent({component: "topology", object: this, operation: "action", phase: "end", action: action});
		}
		for (var id in options.elements||this.elements) {
			var el = this.elements[id];
			if (el.busy) continue;
			if (el.parent) continue;
			if (el.actionEnabled(action)) {
				el.action(action, {
					noask: true,
					callback: cb
				});
				ids++;
			}
		}
		if (ids <= 0 && options.callback) options.callback();
		this.onUpdate();
	},
	_twoStepPrepare: function(callback) {
		var vmids = {};
		var rest = {};
		for (var id in this.elements) {
			var element = this.elements[id];
			switch (element.data.type) {
				case 'openvz':
				case 'kvmqm':
				case 'repy':
					vmids[id] = element;
					break;
				default:
					rest[id] = element;
			}
		}
		var t = this;
		this.action_delegate("prepare", {
			elements: vmids,
			callback: function() {
				t.action_delegate("prepare", {
					elements: rest,
					callback: callback
				})
			}
		})
	},
	action_start: function() {
		var t = this;
		this._twoStepPrepare(function(){
			t.action_delegate("start", {});
		});
	},
	action_stop: function() {
		this.action_delegate("stop");
	},
	action_prepare: function() {
		this._twoStepPrepare();
	},
	action_destroy: function() {
		var t = this;
		if (this.editor.options.safe_mode && !confirm("Are you sure you want to completely destroy this topology?")) return;
		this.action_delegate("stop", {
			callback: function(){
				t.action_delegate("destroy", {noask: true});
			}, noask: true
		});
	},
	remove: function() {
		if (this.editor.options.safe_mode && !confirm("Are you sure you want to completely remove this topology?")) return;
		var t = this;
		var removeTopology = function() {
			t.editor.triggerEvent({component: "topology", object: t, operation: "remove", phase: "begin"});
			ajax({
				url: "topology/"+t.id+"/remove",
				successFn: function() {
					t.editor.triggerEvent({component: "topology", object: t, operation: "remove", phase: "end"});
					window.location = "/topology";
				}
			});			
		}
		this.action_delegate("stop", {noask: true, callback: function() {
			t.action_delegate("destroy", {noask: true, callback: function() {
				if (t.elementCount()) {
					for (var elId in t.elements) {
						if (t.elements[elId].parent) continue;
						t.elements[elId].remove(function(){
							if (! t.elementCount()) removeTopology();		
						}, false);
					}
				} else removeTopology();				
			}});			
		}});
	},
	showDebugInfo: function() {
		var t = this;
		ajax({
			url: 'topology/'+this.id+'/info',
		 	data: {},
		 	successFn: function(result) {
		 		var win = new Window({
		 			title: "Debug info",
		 			position: "center top",
		 			width: 800,
		 			buttons: {
		 				Close: function() {
		 					win.hide();
		 				}
					} 
		 		});
		 		win.add($("<pre></pre>").text(JSON.stringify(result, undefined, 2)));
		 		win.show();
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
		 	}
		});
	},
	showUsage: function() {
  		window.open('/topology/'+this.id+'/usage', '_blank', 'innerHeight=450,innerWidth=650,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
		this.editor.triggerEvent({component: "topology", object: this, operation: "usage-dialog"});
	},
	notesDialog: function() {
		var dialog = $("<div/>");
		var ta = $('<textarea cols=60 rows=20 class="notes"></textarea>');
		ta.text(this.data.attrs._notes || "");
		dialog.append(ta);
		var openWithEditor_html = $('<input type="checkbox" name="openWithEditor">Open Window with Editor</input>');
		var openWithEditor = openWithEditor_html[0];
		if (this.data.attrs._notes_autodisplay) {
			openWithEditor.checked = true;
			console.log("check");
		}
		dialog.append($('<br/>'))
		dialog.append(openWithEditor_html);
		var t = this;
		dialog.dialog({
			autoOpen: true,
			draggable: true,
			resizable: true,
			height: "auto",
			width: 550,
			title: "Notes for Topology",
			show: "slide",
			hide: "slide",
			modal: true,
			buttons: {
				Save: function() {
		        	dialog.dialog("close");
			      	t.modify_value("_notes", ta.val());
			      	t.modify_value("_notes_autodisplay", openWithEditor.checked)
			    },
		        Close: function() {
		        	dialog.dialog("close");
		        }				
			}
		});
	},
	renameDialog: function() {
		var t = this;
		windowOptions = {
			title: "Rename Topology",
			width: 550,
			inputname: "newname",
			inputlabel: "New Name:",
			inputvalue: t.data.attrs.name,
			onChangeFct: function () {
				if(this.value == '') { 
					$('#rename_topology_window_save').button('disable');
				} else { 
					$('#rename_topology_window_save').button('enable');
				}
			},
			buttons: [
				{ 
					text: "Save",
					id: "rename_topology_window_save",
					click: function() {
						t.rename.hide();
						if(t.rename.element.getValue() != '') {
							t.modify_value("name", t.rename.element.getValue());
						}
						t.rename = null;
					}
				},
				{
					text: "Cancel",
					click: function() {
						t.rename.hide();
						t.rename = null;
					}
				}
			],
		};
		this.rename = new InputWindow(windowOptions);
		this.rename.show();
	},
	renewDialog: function() {
		var t = this;
		var dialog, timeout;
		dialog = new AttributeWindow({
			title: "Topology Timeout",
			width: 500,
			buttons: [
						{ 
							text: "Save",
							click: function() {
								t.action("renew", {params:{
									"timeout": timeout.getValue()
								}});
								dialog.remove();
							}
						},
						{
							text: "Close",
							click: function() {
								dialog.remove();
							}
						}
					],
		});
		var choices = {};
		var timeout_settings = t.editor.options.timeout_settings;
		for (var i = 0; i < timeout_settings.options.length; i++) choices[timeout_settings.options[i]] = formatDuration(timeout_settings.options[i]);
		var timeout_val = t.data.timeout - new Date().getTime()/1000.0;
		var text = timeout_val > 0 ? ("Your topology will time out in " + formatDuration(timeout_val)) : "Your topology has timed out. You must renew it to use it.";
		if (timeout_val < timeout_settings.warning) text = '<b style="color:red">' + text + '</b>';
		dialog.addText("<center>"  + text + "</center>");
		timeout = dialog.add(new ChoiceElement({
			name: "timeout",
			label: "New timeout",
			choices: choices,
			value: timeout_settings["default"],
			help_text: "After this time, your topology will automatically be stopped. Timeouts can be extended arbitrarily."
		}));
		dialog.show();		
	},
	initialDialog: function() {
		var t = this;
		var dialog, name, description, timeout;
		dialog = new AttributeWindow({
			title: "New Topology",
			width: 500,
			closable: false,
			buttons: [
						{ 
							text: "Save",
							disabled: true,
							id: "new_topology_window_save",
							click: function() {
								if (name.getValue() && timeout.getValue()) {
									t.modify({
										"name": name.getValue(),
										"_notes": description.getValue(),
										"_initialized": true
									});
									editor.workspace.updateTopologyTitle();
									t.action("renew", {params:{
										"timeout": timeout.getValue()
									}});
									dialog.remove();
									dialog = null;
								}
							}
						}
					],
		});
		name = dialog.add(new TextElement({
			name: "name",
			label: "Name",
			help_text: "The name for your topology",
			onChangeFct:  function () {
				if(this.value == '') { 
					$('#new_topology_window_save').button('disable');
				} else { 
					$('#new_topology_window_save').button('enable');
				}
			}
		}));
		var choices = {};
		var timeout_settings = t.editor.options.timeout_settings;
		for (var i = 0; i < timeout_settings.options.length; i++) choices[timeout_settings.options[i]] = formatDuration(timeout_settings.options[i]); 
		timeout = dialog.add(new ChoiceElement({
			name: "timeout",
			label: "Timeout",
			choices: choices,
			value: timeout_settings["default"],
			help_text: "After this time, your topology will automatically be stopped. Timeouts can be extended arbitrarily."
		}));
		description = dialog.add(new TextAreaElement({
			name: "description",
			label: "Description",
			help_text: "Description of the experiment. (Optional)",
			value: t.data.attrs._notes
		}));
		dialog.show();
	},
	name: function() {
		return this.data.attrs.name;
	},
	onUpdate: function() {
		this.checkNetworkLoops();
		var segments = this.getNetworkSegments();
		this.colorNetworkSegments(segments);
		this.editor.triggerEvent({component: "topology", object: this, operation: "update"});
	},
	getNetworkSegments: function() {
		var segments = [];
		for (var con in this.connections) {
			var found = false;
			for (var i=0; i<segments.length; i++)
			 if (segments[i].connections.indexOf(this.connections[con].id) >= 0)
			  found = true;
			if (found) continue;
			segments.push(this.connections[con].calculateSegment());
		}
		return segments;
	},
	checkNetworkLoops: function() {
		var maxCount = 1;
		this.loop_last_warn = this.loop_last_warn || 1;
		for (var i in  this.elements) {
			var el = this.elements[i];
			if (el.data.type != "external_network_endpoint") continue;
			if (! el.connection) continue; //can that happen?
			var segment = el.connection.calculateSegment([el.id], []);
			var count = 0;
			for (var j=0; j<segment.elements.length; j++) {
				var e = this.elements[segment.elements[j]];
				if (! e) continue; //brand new element
				if (e.data.type == "external_network_endpoint") count++;
			}
			maxCount = Math.max(maxCount, count);
		}
		if (maxCount > this.loop_last_warn) showError("Network segments must not contain multiple external network exits! This could lead to loops in the network and result in a total network crash.");
		this.loop_last_warn = maxCount;
	},
	colorNetworkSegments: function(segments) {
		var skips = 0;
		for (var i=0; i<segments.length; i++) {
			var cons = segments[i].connections;
			var num = (this.editor.options.colorify_segments && cons.length > 1) ? (i-skips) : NaN;
			if (cons.length == 1) skips++;
			for (var j=0; j<cons.length; j++) {
				var con = this.connections[cons[j]];
				if (! con) continue; //brand new connection
				con.setSegment(num);
			}
		}
	}
});

var createTopologyMenu = function(obj) {
	var menu = {
		callback: function(key, options) {},
		items: {
			"header": {
				html:"<span>"+obj.name()+"<small><br />Topology "+(editor.options.show_ids ? ' #'+obj.id : "")+'</small></span>',
				type:"html"
			},
			"actions": {
				name:'Global actions',
				icon:'control',
				items: {
					"start": {
						name:'Start',
						icon:'start',
						callback: function(){
							obj.action_start();
						}
					},
					"stop": {
						name:"Stop",
						icon:"stop",
						callback: function(){
							obj.action_stop();
						}
					},
					"prepare": {
						name:"Prepare",
						icon:"prepare",
						callback: function(){
							obj.action_prepare();
						}
					},
					"destroy": {
						name:"Destroy",
						icon:"destroy",
						callback:function(){
							obj.action_destroy();
						}
					}
				}
			},
			"sep1": "---",
			"notes": {
				name:"Notes",
				icon:"notes",
				callback: function(){
					obj.notesDialog();
				}
			},
			"usage": {
				name:"Resource usage",
				icon:"usage",
				callback: function(){
					obj.showUsage();
				}
			},
			"sep2": "---",
			"configure": {
				name:'Configure',
				icon:'configure',
				callback: function(){
					obj.showConfigWindow();
				}
			},
			"debug": obj.editor.options.debug_mode ? {
				name:'Debug',
				icon:'debug',
				callback: function(){
					obj.showDebugInfo();
				}
			} : null,
			"sep3": "---",
			"remove": {
				name:'Delete',
				icon:'remove',
				callback: function(){
					obj.remove();
				}
			}
		}
	};	
	for (var name in menu.items) {
		if (! menu.items[name]) delete menu.items[name]; 
	}
	return menu;
};

['right', 'longclick'].forEach(function(trigger) {
	$.contextMenu({
		selector: '.tomato.workspace',
		trigger: trigger,
		build: function(trigger, e) {
			return createTopologyMenu(trigger[0].obj);
		}
	});	
});

var Component = Class.extend({
	init: function(topology, data, canvas) {
		this.topology = topology;
		this.editor = topology.editor;
		this.setData(data);
		this.canvas = canvas;
	},	
	paint: function() {
	},
	paintUpdate: function() {
	},
	paintRemove: function() {
	},
	setBusy: function(busy) {
		this.busy = busy;
	},
	actionEnabled: function(action) {
		return (action in this.caps.actions) && (this.caps.actions[action].indexOf(this.data.state) >= 0); 
	},
	attrEnabled: function(attr) {
		return (attr[0] == "_") || (attr in this.caps.attrs) && (! this.caps.attrs[attr].states || this.caps.attrs[attr].states.indexOf(this.data.state) >= 0);
	},
	setData: function(data) {
		this.data = data;
		this.id = data.id;
		this.caps = this.editor.capabilities[this.component_type][this.data.type];
	},
	updateData: function(data) {
		if (data) this.setData(data);
		this.topology.onUpdate();
		this.paintUpdate();
	},
	triggerEvent: function(event) {
		event.component = this.component_type;
		event.object = this;
		this.editor.triggerEvent(event);
	},
	showDebugInfo: function() {
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/info',
		 	data: {},
		 	successFn: function(result) {
		 		var win = new Window({
		 			title: "Debug info",
		 			position: "center top",
		 			width: 800,
		 			buttons: {
		 				Close: function() {
		 					win.hide();
		 					win.remove();
		 				}
					} 
		 		});
		 		win.add($("<pre></pre>").text(JSON.stringify(result, undefined, 2)));
		 		win.show();
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
		 	}
		});
	},
	showUsage: function() {
  		window.open('../'+this.component_type+'/'+this.id+'/usage', '_blank', 'innerHeight=450,innerWidth=650,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no');
		this.triggerEvent({operation: "usage-dialog"});
	},
	configWindowSettings: function() {
		return {
			order: ["name"],
			ignore: [],
			unknown: true,
			special: {}
		} 
	},
	showConfigWindow: function(showTemplate,callback) {
		
		if(showTemplate == null) showTemplate=true;
		
		var absPos = this.getAbsPos();
		var wsPos = this.editor.workspace.container.position();
		var t = this;
		var settings = this.configWindowSettings();
		
		var helpTarget = undefined;
		if ($.inArray(this.data.type,settings.supported_configwindow_help_pages)) {
			helpTarget = help_baseUrl+"/editor:configwindow_"+this.data.type;
		}
		
		console.log('opening config window for type '+this.data.type);
		
		this.configWindow = new AttributeWindow({
			title: "Attributes",
			width: "600",
			helpTarget:helpTarget,
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) {
						if (values[name] === t.data.attrs[name]) delete values[name];
						// Tread "" like null
						if (values[name] === "" && t.data.attrs[name] === null) delete values[name];
					}
					t.modify(values);	
					t.configWindow.remove();
					t.configWindow = null;
					
					
					if(callback != null) {
						callback(t);
					}
				},
				Cancel: function() {
					t.configWindow.remove();
					t.configWindow = null;
				} 
			}
		});
		for (var i=0; i<settings.order.length; i++) {
			var name = settings.order[i];
			if(showTemplate || !(name == 'template')) {
				if (settings.special[name]) this.configWindow.add(settings.special[name]);
				else if (this.caps.attrs[name]) this.configWindow.autoAdd(this.caps.attrs[name], this.data.attrs[name], this.attrEnabled(name));
			}
		}
		if (settings.unknown) {
			for (var name in this.caps.attrs) {
				if (settings.order.indexOf(name) >= 0) continue; //do not repeat ordered fields
				if (settings.ignore.indexOf(name) >= 0) continue;
				if (settings.special[name]) this.configWindow.add(settings.special[name]);
				else if (this.caps.attrs[name]) this.configWindow.autoAdd(this.caps.attrs[name], this.data.attrs[name], this.attrEnabled(name));
			}
		}
		this.configWindow.show();
		this.triggerEvent({operation: "attribute-dialog"});
	},
	update: function(fetch, callback) {
		var t = this;
		this.triggerEvent({operation: "update", phase: "begin"});
		ajax({
			url: this.component_type+'/'+this.id+'/info',
			data: {fetch: fetch},
		 	successFn: function(result) {
		 		t.updateData(result);
		 		t.setBusy(false);
				t.triggerEvent({operation: "update", phase: "end"});
				if (callback) callback();
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
		 		t.setBusy(false);
				t.triggerEvent({operation: "update", phase: "error"});
		 	}
		});
	},
	updateDependent: function() {
	},
	modify: function(attrs) {
		this.setBusy(true);
		for (var name in attrs) {
			if (this.attrEnabled(name)) this.data.attrs[name] = attrs[name];
			else delete attrs[name];
		}
		this.triggerEvent({operation: "modify", phase: "begin", attrs: attrs});
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/modify',
		 	data: {attrs: attrs},
		 	successFn: function(result) {
		 		t.updateData(result);
		 		t.setBusy(false);
				t.triggerEvent({operation: "modify", phase: "end", attrs: attrs});
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
		 		t.update();
				t.triggerEvent({operation: "modify", phase: "error", attrs: attrs});
		 	}
		});
	},
	modify_value: function(name, value) {
		var attrs = {};
		attrs[name] = value;
		this.modify(attrs);
	},
	action: function(action, options) {
		var options = options || {};
		if ((action=="destroy"||action=="stop") && !options.noask && this.editor.options.safe_mode && ! confirm("Do you want to " + action + " this "+this.component_type+"?")) return;
		this.setBusy(true);
		var params = options.params || {};
		this.triggerEvent({operation: "action", phase: "begin", action: action, params: params});
		var t = this;
		ajax({
			url: this.component_type+'/'+this.id+'/action',
		 	data: {action: action, params: params},
		 	successFn: function(result) {
		 		t.updateData(result[1]);
		 		t.setBusy(false);
		 		if (options.callback) options.callback(t, result[0], result[1]);
				t.triggerEvent({operation: "action", phase: "end", action: action, params: params});
				t.updateDependent();
				editor.rextfv_status_updater.add(t, 30);
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
		 		t.update();
				t.triggerEvent({operation: "action", phase: "error", action: action, params: params});
				editor.rextfv_status_updater.add(t, 5);
		 	}
		});
	},
	onConnected: function() {
	}
});

var ConnectionAttributeWindow = AttributeWindow.extend({
	init: function(options, con) {
		options.helpTarget = help_baseUrl+"/editor:configwindow_connection";
		this._super(options);
		
		this.table.append($('<div class="form-group" />').append($('<ul class="nav nav-tabs" style="margin-bottom: 1pt;">\
				<li class="active"><a href="#Link_Emulation" data-toggle="tab">Link Emulation</a></li>\
				  <li><a href="#Packet_capturing" data-toggle="tab">Packet capturing</a></li>\
				</ul>')));
		
		var tab_content = $('<div class="tab-content" />');
		if (con.attrEnabled("emulation")) {
			
			
			
			this.emulation_elements = [];
			var t = this;
			var el = new CheckboxElement({
				name: "emulation",
				value: con.data.attrs.emulation,
				callback: function(el, value) {
					t.updateEmulationStatus(value);
				}
			});
			this.elements.push(el);
			var link_emulation = $('<div class="tab-pane active" id="Link_Emulation" />');
			var link_emulation_elements = $('<div class="form-group" />')
						.append($('<label class="col-sm-4 control-label">Enabled</label>'))
						.append($('<div class="col-sm-8" style="padding: 0px" />')
						.append(el.getElement()));
			
			//direction arrows
			var size = 30;
			var _div = '<div style="width: '+size+'px; height: '+size+'px;"/>';
			var dir1 = $(_div); var dir2 = $(_div);
			var canvas1 = Raphael(dir1[0], size, size);
			var canvas2 = Raphael(dir2[0], size, size);
			var _path1 = "M 0.1 0.5 L 0.9 0.5";
			var _path2 = "M 0.7 0.5 L 0.4 0.3 M 0.7 0.5 L 0.4 0.7";
			var _transform1 = "R"+con.getAngle()+",0.5,0.5S"+size+","+size+",0,0";
			var _transform2 = "R"+(con.getAngle()+180)+",0.5,0.5S"+size+","+size+",0,0";
			var _attrs = {"stroke-width": 2, stroke: "red", "stroke-linecap": "round", "stroke-linejoin": "round"};
			canvas1.path(_path1).transform(_transform1);
			canvas1.path(_path2).transform(_transform1).attr(_attrs);
			canvas2.path(_path1).transform(_transform2);
			canvas2.path(_path2).transform(_transform2).attr(_attrs);
			var name1 = con.elements[0].name();
			var name2 = con.elements[1].name();
			if (con.elements[0].id > con.elements[1].id) {
				var t = name1;
				name1 = name2;
				name2 = t;
			}
			var fromDir = $("<div>From " + name1 + "<br/>to " + name2 + "</div>");
			var toDir = $("<div>From " + name2 + " <br/>to " + name1 + "</div>");
			link_emulation_elements.after($('<div class="form-group" />')
				.append($('<label class="col-sm-4 control-label">Direction</label>'))
				.append($('<div class="col-sm-4" />').append(fromDir).append(dir1))
				.append($('<div class="col-sm-4" />').append(toDir).append(dir2))
			);
			//simple fields
			var order = ["bandwidth", "delay", "jitter", "distribution", "lossratio", "duplicate", "corrupt"];
			for (var i = 0; i < order.length; i++) {
				var name = order[i];
				var el_from = this.autoElement(con.caps.attrs[name+"_from"], con.data.attrs[name+"_from"], true)
				this.elements.push(el_from);
				this.emulation_elements.push(el_from);
				var el_to = this.autoElement(con.caps.attrs[name+"_to"], con.data.attrs[name+"_to"], true)
				this.elements.push(el_to);
				this.emulation_elements.push(el_to);
				link_emulation_elements.after($('<div class="form-group" />')
					.append($('<label class="col-sm-4 control-label" style="padding: 0;" />').append(con.caps.attrs[name+"_to"].desc))
					.append($('<div class="col-sm-3" style="padding: 0;"/>').append(el_from.getElement()))
					.append($('<div class="col-sm-3" style="padding: 0;" />').append(el_to.getElement()))
					.append($('<div class="col-sm-2" style="padding: 0;" />').append(con.caps.attrs[name+"_to"].unit))
				);
			}
			this.updateEmulationStatus(con.data.attrs.emulation);
			
			

			link_emulation.append(link_emulation_elements);
			tab_content.append(link_emulation);
			this.table.append(tab_content);
		}
		if (con.attrEnabled("capturing")) {
			var t = this;
			var packet_capturing = $('<div class="tab-pane" id="Packet_capturing" />');
			
			packet_capturing.append(packet_capturing_elements);
			this.capturing_elements = [];
			var el = new CheckboxElement({
				name: "capturing",
				value: con.data.attrs.capturing,
				callback: function(el, value) {
					t.updateCapturingStatus(value);
				}
			});
			this.elements.push(el);
			var packet_capturing_elements = $('<div class="form-group" />')
			.append($('<label class="col-sm-6 control-label">Enabled</label>'))
			.append($('<div class="col-sm-6" />')
			.append(el.getElement()));
		
			
			var order = ["capture_mode", "capture_filter"];
			for (var i = 0; i < order.length; i++) {
				var name = order[i];
				var el = this.autoElement(con.caps.attrs[name], con.data.attrs[name], con.attrEnabled(name));
				this.capturing_elements.push(el);
				this.elements.push(el);
				packet_capturing_elements.after($('<div class="form-group" />')
					.append($('<label class="col-sm-6 control-label">').append(con.caps.attrs[name].desc))
					.append($('<div class="col-sm-6" />').append(el.getElement()))
				);
			}
			this.updateCapturingStatus(con.data.attrs.capturing);
			

			packet_capturing.append(packet_capturing_elements);
			tab_content.append(packet_capturing);
			this.table.append(tab_content);
		}
	},
	updateEmulationStatus: function(enabled) {
		for (var i=0; i<this.emulation_elements.length; i++)
			 this.emulation_elements[i].setEnabled(enabled);
	},
	updateCapturingStatus: function(enabled) {
		for (var i=0; i<this.capturing_elements.length; i++)
			 this.capturing_elements[i].setEnabled(enabled);
	}
});


var Connection = Component.extend({
	init: function(topology, data, canvas) {
		this.component_type = "connection";
		data.type = data.type || "bridge";
		this._super(topology, data, canvas);
		this.elements = [];
		this.segment = -1;
	},
	fromElement: function() {
		return this.elements[0].id < this.elements[1].id ? this.elements[0] : this.elements[1];
	},
	toElement: function() {
		return this.elements[0].id >= this.elements[1].id ? this.elements[0] : this.elements[1];
	},
	otherElement: function(me) {
		for (var i=0; i<this.elements.length; i++) if (this.elements[i].id != me.id) return this.elements[i];
	},
	onClicked: function() {
		this.editor.onConnectionSelected(this);
	},
	isRemovable: function() {
		return this.actionEnabled("(remove)");
	},
	getCenter: function() {
		if (this.path) return this.path.getPointAtLength(this.path.getTotalLength()/2);
		else {
			var pos1 = this.elements[0].getAbsPos();
			var pos2 = this.elements[1].getAbsPos();
			return {x: (pos1.x + pos2.x)/2, y: (pos1.y + pos2.y)/2}; 
		}
	},
	getPath: function() {
		var pos1 = this.elements[0].getAbsPos();
		var pos2 = this.elements[1].getAbsPos();
		var diff = {x: pos1.x - pos2.x, y: pos1.y - pos2.y};
		var length = Math.sqrt(diff.x * diff.x + diff.y * diff.y);
		var norm = {x: diff.x/length, y: diff.y/length};
		pos1 = {x: pos1.x - norm.x * settings.childElementDistance, y: pos1.y - norm.y * settings.childElementDistance};
		pos2 = {x: pos2.x + norm.x * settings.childElementDistance, y: pos2.y + norm.y * settings.childElementDistance};
		var path = "M"+pos1.x+" "+pos1.y+"L"+pos2.x+" "+pos2.y;
		//TODO: use bezier loop for very short connections
		return path;
	},
	getAbsPos: function() {
		return this.getCenter();
	},
	getAngle: function() {
		var pos1 = this.toElement().getAbsPos();
		var pos2 = this.fromElement().getAbsPos();
		return Raphael.angle(pos1.x, pos1.y, pos2.x, pos2.y);
	},
	paint: function() {
		this.path = this.canvas.path(this.getPath());
		this.path.toBack();
		var pos = this.getAbsPos();
		this.handle = this.canvas.rect(pos.x-5, pos.y-5, 10, 10).attr({fill: "#4040FF", transform: "R"+this.getAngle()});
		$(this.handle.node).attr("class", "tomato connection");
		this.handle.node.obj = this;
		var t = this;
		$(this.handle.node).click(function() {
			t.onClicked();
		})
		this.paintUpdate();
		for (var i=0; i<this.elements.length; i++) this.elements[i].paintUpdate();
	},
	paintRemove: function(){
		this.path.remove();
		this.handle.remove();
	},
	setSegment: function(segment){
		this.segment = segment;
		this.paintUpdate();
	},
	paintUpdate: function(){
		var colors = ["#2A4BD7", "#AD2323", "#1D6914", "#814A19", "#8126C0", "#FFEE33", "#FF9233", "#29D0D0", "#9DAFFF", "#81C57A", "#FFCDF3"];
		var color = colors[this.segment % colors.length] || "#505050";
		var attrs = this.data.attrs;
		var le = attrs && attrs.emulation && (attrs.delay_to || attrs.jitter_to || attrs.lossratio_to || attrs.duplicate_to || attrs.corrupt_to
				         || attrs.delay_from || attrs.jitter_from || attrs.lossratio_from || attrs.duplicate_from || attrs.corrupt_from);
		var bw = 10000000;
		if (attrs && attrs.emulation) bw = Math.min(attrs.bandwidth_to, attrs.bandwidth_from); 
		this.path.attr({stroke: color, "stroke-dasharray": [le ? "-" : ""]});
		this.path.attr({"stroke-width": bw < 10000 ? 1 : ( bw > 10000 ? 4 : 2.5 )});
		this.path.attr({path: this.getPath()});
		var pos = this.getAbsPos();
		this.handle.attr({x: pos.x-5, y: pos.y-5, transform: "R"+this.getAngle()});
		this.handle.conditionalClass("removable", this.isRemovable());
	},
	calculateSegment: function(els, cons) {
		if (! els) els = [];
		if (! cons) cons = [];
		if (cons.indexOf(this.id) >= 0) return {elements: els, connections: cons};
		cons.push(this.id);
		for (var i=0; i < this.elements.length; i++) {
			var res = this.elements[i].calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		return {elements: els, connections: cons};
	},
	action_start: function() {
		this.action("start");
	},
	action_stop: function() {
		this.action("stop");
	},
	action_prepare: function() {
		this.action("prepare");
	},
	action_destroy: function() {
		this.action("destroy");
	},
	captureDownloadable: function() {
		return this.actionEnabled("download_grant") && this.data.attrs.capturing && this.data.attrs.capture_mode == "file";
	},
	downloadCapture: function() {
		this.action("download_grant", {callback: function(con, res) {
			var name = con.topology.data.attrs.name + "_capture_" + con.id + ".pcap";
			var url = "http://" + con.data.attrs.host_info.address + ":" + con.data.attrs.host_info.fileserver_port + "/" + res + "/download?name=" + encodeURIComponent(name); 
			window.location.href = url;
		}})
	},
	viewCapture: function() {
		this.action("download_grant", {params: {limitSize: 1024*1024}, callback: function(con, res) {
			var url = "http://" + con.data.attrs.host_info.address + ":" + con.data.attrs.host_info.fileserver_port + "/" + res + "/download"; 
			window.open("http://www.cloudshark.org/view?url="+url, "_newtab");
		}})
	},
	liveCaptureEnabled: function() {
		return this.actionEnabled("download_grant") && this.data.attrs.capturing && this.data.attrs.capture_mode == "net";
	},
	liveCaptureInfo: function() {
		var host = this.data.attrs.host_info.address;
		var port = this.data.attrs.capture_port;
		var cmd = "wireshark -k -i <( nc "+host+" "+port+" )";
		new Window({
			title: "Live capture Information", 
			content: '<p>Host: '+host+'<br />Port: '+port+"</p><p>Start live capture via: <pre>"+cmd+"</pre></p>", 
			autoShow: true,
			width: 600
		});
	},
	showConfigWindow: function() {
		var absPos = this.getAbsPos();
		var wsPos = this.editor.workspace.container.position();
		var t = this;
		this.configWindow = new ConnectionAttributeWindow({
			title: "Attributes",
			width: 500,
			buttons: {
				Save: function() {
					t.configWindow.hide();
					var values = t.configWindow.getValues();
					for (var name in values) if (values[name] === t.data.attrs[name]) delete values[name];
					t.modify(values);		
					t.configWindow.remove();
					t.configWindow = null;
				},
				Cancel: function() {
					t.configWindow.remove();
					t.configWindow = null;
				} 
			}
		}, this);
		this.configWindow.show();
		this.triggerEvent({operation: "attribute-dialog"});
	},
	remove: function(callback, ask) {
		if (this.busy) return;
		if (ask && this.editor.options.safe_mode && ! confirm("Do you want to delete this connection?")) return;
		this.setBusy(true);
		this.triggerEvent({operation: "remove", phase: "begin"});
		var t = this;
		ajax({
			url: 'connection/'+this.id+'/remove',
		 	successFn: function(result) {
		 		t.paintRemove();
		 		delete t.topology.connections[t.id];
		 		for (var i=0; i<t.elements.length; i++) delete t.elements[i].connection;
		 		t.setBusy(false);
		 		if (callback) callback(t);
		 		t.topology.onUpdate();
				t.triggerEvent({operation: "remove", phase: "end"});
				for (var i=0; i<t.elements.length; i++) 
					if (t.elements[i].isRemovable() && t.topology.elements[t.elements[i].id])
						t.elements[i].remove();
		 	},
		 	errorFn: function(error) {
		 		this.errorWindow = new errorWindow({error:error});
		 		t.setBusy(false);
				t.triggerEvent({operation: "remove", phase: "error"});
		 	}
		});
	},
	name: function() {
		return this.fromElement().name() + " &#x21C4; " + this.toElement().name();
	},
	name_vertical: function() {
		return this.fromElement().name() + "<br/>&#x21C5;<br/>" + this.toElement().name();
	}
});

var createConnectionMenu = function(obj) {
	var menu = {
		callback: function(key, options) {},
		items: {
			"header": {
				html:'<span>'+obj.name_vertical()+"<small><br>Connection"+(editor.options.show_ids ? " #"+obj.id : "")+'</small></span>', type:"html"
			},
			"usage": {
				name:"Resource usage",
				icon:"usage",
				callback: function(){
					obj.showUsage();
				}
			},
			"sep1": "---",
			"cloudshark_capture": obj.captureDownloadable() ? {
				name:"View capture in Cloudshark",
				icon:"cloudshark",
				callback: function(){
					obj.viewCapture();
				}
			} : null,
			"download_capture": obj.captureDownloadable() ? {
				name:"Download capture",
				icon:"download-capture",
				callback: function(){
					obj.downloadCapture();
				}
			} : null,
			"live_capture": obj.liveCaptureEnabled() ? {
				name:"Live capture info",
				icon:"live-capture",
				callback: function(){
					obj.liveCaptureInfo();
				}
			} : null,
			"no_capture": (! obj.liveCaptureEnabled() && ! obj.captureDownloadable()) ? {
				name:"No captures",
				icon:"no-capture"
			} : null,
			"sep2": "---",
			"configure": {
				name:'Configure',
				icon:'configure',
				callback: function(){
					obj.showConfigWindow();
				}
			},
			"debug": obj.editor.options.debug_mode ? {
				name:'Debug',
				icon:'debug',
				callback: function(){
					obj.showDebugInfo();
				}
			} : null,
			"sep3": "---",
			"remove": obj.isRemovable() ? {
				name:'Delete',
				icon:'remove',
				callback: function(){
					obj.remove(null, true);
				}
			} : null
		}
	};
	for (var name in menu.items) {
		if (! menu.items[name]) delete menu.items[name]; 
	}
	return menu;
};


var Element = Component.extend({
	init: function(topology, data, canvas) {
		this.component_type = "element";
		this._super(topology, data, canvas);
		this.children = [];
		this.connection = null;
	},
	rextfvStatusSupport: function() {
		return this.data.attrs.rextfv_supported;
	},
	openRexTFVStatusWindow: function() {
		window.open('../element/'+this.id+'/rextfv_status', '_blank', "innerWidth=350,innerheight=420,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
		this.triggerEvent({operation: "rextfv-status"});
	},
	onDragged: function() {
		if (!this.isMovable()) return;
		this.modify_value("_pos", this.getPos());
	},
	onClicked: function() {
		this.editor.onElementSelected(this);
	},
	isMovable: function() {
		return (!this.editor.options.fixed_pos) && this.editor.mode == Mode.select;
	},
	isConnectable: function() {
		if (this.connection) return false;
		if (! this.caps.children) return false;
		for (var ch in this.caps.children)
			if (this.caps.children[ch].indexOf(this.data.state) >= 0)
				return true;
		return false;
	},
	isRemovable: function() {
		return this.actionEnabled("(remove)");
	},
	isEndpoint: function() {
		return true;
	},
	getUsedAddress: function() {
		if (this.data.attrs.use_dhcp) return "dhcp";
		if (! this.data.attrs.ip4address) return null;
		res = /10.0.([0-9]+).([0-9]+)\/[0-9]+/.exec(this.data.attrs.ip4address);
		if (! res) return res;
		return [parseInt(res[1]), parseInt(res[2])];
	},
	getAddressHint: function() {
		var segs = this.topology.getNetworkSegments();
		for (var i=0; i < segs.length; i++) {
			var seg = segs[i];
			if (seg.elements.indexOf(this.id)>=0) break;
		}
		//Determine major usage counts in segment
		var usedMajors = {};
		for (var i=0; i < seg.elements.length; i++) {
			var el = this.topology.elements[seg.elements[i]];
			if (!el || !el.data) continue; //Element is being created
			if (el.data.type == "external_network_endpoint") return "dhcp";
			var addr = el.getUsedAddress();
			if (! addr) continue;
			if (addr == "dhcp")	usedMajors.dhcp = (usedMajors.dhcp || 0) + 1;
			else usedMajors[addr[0]] = (usedMajors[addr[0]] || 0) + 1;
		}
		//Find the most common major
		var major = null;
		var majorCount = 0;
		for (var m in usedMajors) {
			if (usedMajors[m] > majorCount) {
				major = m;
				majorCount = usedMajors[m]; 
			}
		}
		if (major == "dhcp") return "dhcp";
		if (! major) {
			//If no major in segment so far, find free global major
			var usedMajors = {};
			for (var i=0; i < segs.length; i++) {
				var seg = segs[i];
				for (var j=0; j < seg.elements.length; j++) {
					var el = this.topology.elements[seg.elements[j]];
					if (!el || !el.data) continue; //Element is being created
					var addr = el.getUsedAddress();
					if (! addr || addr == "dhcp") continue;
					usedMajors[addr[0]] = (usedMajors[addr[0]] || 0) + 1; 
				}
			}
			var major = 0;
			while (usedMajors[major]) major++;
			return [major, 1];
		} else {
			//Find free minor for the major
			major = parseInt(major);
			var usedMinors = {};
			for (var j=0; j < seg.elements.length; j++) {
				var el = this.topology.elements[seg.elements[j]];
				if (!el || !el.data) continue; //Element is being created
				var addr = el.getUsedAddress();
				if (! addr || addr == "dhcp") continue;
				if (addr[0] == major) usedMinors[addr[1]] = (usedMinors[addr[1]] || 0) + 1; 
			}
			var minor = 1;
			while (usedMinors[minor]) minor++;
			return [major, minor];			
		}
	},
	calculateSegment: function(els, cons) {
		if (! els) els = [];
		if (! cons) cons = [];
		if (els.indexOf(this.id) >= 0) return {elements: els, connections: cons};
		els.push(this.id);
		if (this.connection) {
			var res = this.connection.calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		if (this.isEndpoint()) return {elements: els, connections: cons};
		for (var i=0; i < this.children.length; i++) {
			var res = this.children[i].calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		if (this.parent) {
			var res = this.parent.calculateSegment(els, cons);
			els = res.elements;
			cons = res.connections;
		}
		return {elements: els, connections: cons};
	},
	enableClick: function(obj) {
		obj.click(function() {
			this.onClicked();
		}, this);
	},
	enableDragging: function(obj) {
		obj.drag(function(dx, dy, x, y) { //move
			if (!this.isMovable()) return;
			this.setAbsPos({x: this.opos.x + dx, y: this.opos.y + dy});
		}, function() { //start
			if (!this.isMovable()) return false;
			this.opos = this.getAbsPos();
		}, function() { //stop
			var pos = this.getAbsPos();
			if (! this.opos) return;
			if (pos.x == this.opos.x && pos.y == this.opos.y) return;
			this.onDragged();
		}, this, this, this);
	},
	getConnectTarget: function() {
		return this;
	},
	getPos: function() {
		if (! this.data.attrs._pos) {
			this.data.attrs._pos = {x: Math.random(), y: Math.random()};
			this.modify_value("_pos", this.data.attrs._pos);
		}
		return this.data.attrs._pos;
	},
	setPos: function(pos) {
		if (this.editor.options.fixed_pos) return;
		this.data.attrs._pos = {x: Math.min(1, Math.max(0, pos.x)), y: Math.min(1, Math.max(0, pos.y))};
		this.onPosChanged(true);
	},
	onPosChanged: function(con) {
		this.paintUpdate();
		for (var i=0; i<this.children.length; i++) this.children[i].onPosChanged(con);
		if (con && this.connection) {
			this.connection.otherElement(this).onPosChanged(false);
			this.connection.paintUpdate();
		}
	},
	getAbsPos: function() {
		return this.canvas.absPos(this.getPos());
	},
	setAbsPos: function(pos) {
		var grid = this.editor.options.grid_size;
		if (this.editor.options.snap_to_grid) pos = {x: Math.round(pos.x/grid)*grid, y: Math.round(pos.y/grid)*grid};
		this.setPos(this.canvas.relPos(pos));
	},
	openConsole: function() {
	    window.open('../element/'+this.id+'/console', '_blank', "innerWidth=745,innerheight=400,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
		this.triggerEvent({operation: "console-dialog"});
	},
	openConsoleNoVNC: function() {
	    window.open('../element/'+this.id+'/console_novnc', '_blank', "innerWidth=760,innerheight=440,status=no,toolbar=no,menubar=no,location=no,hotkeys=no,scrollbars=no");
		this.triggerEvent({operation: "console-dialog"});
	},
	openVNCurl: function() {
		var host = this.data.attrs.host_info.address;
		var port = this.data.attrs.vncport;
		var passwd = this.data.attrs.vncpassword;
		var link = "vnc://:" + passwd + "@" + host + ":" + port;
	    window.open(link, '_self');
		this.triggerEvent({operation: "console-dialog"});
	},
	showVNCinfo: function() {
		var host = this.data.attrs.host_info.address;
		var port = this.data.attrs.vncport;
		var wport = this.data.attrs.websocket_port;
		var passwd = this.data.attrs.vncpassword;
		var link = "vnc://:" + passwd + "@" + host + ":" + port;
 		var win = new Window({
 			title: "VNC info",
 			content: '<p>Link: <a href="'+link+'">'+link+'</a><p>Host: '+host+"</p><p>Port: "+port+"</p><p>Websocket-Port: "+wport+"</p><p>Password: <pre>"+passwd+"</pre></p>",
 			autoShow: true,
 			width: 500,
 		});
		this.triggerEvent({operation: "console-dialog"});
	},
	consoleAvailable: function() {
		return this.data.attrs.vncpassword && this.data.attrs.vncport && this.data.attrs.host && this.data.state == "started";
	},
	downloadImage: function() {
		this.action("download_grant", {callback: function(el, res) {
			var name = el.topology.data.attrs.name + "_" + el.data.attrs.name;
			switch (el.data.type) {
				case "kvmqm":
				case "kvm":
					name += ".qcow2";
					break;
				case "openvz":
					name += ".tar.gz";
					break;
				case "repy":
					name += ".repy";
					break;
			}
			var url = "http://" + el.data.attrs.host_info.address + ":" + el.data.attrs.host_info.fileserver_port + "/" + res + "/download?name=" + encodeURIComponent(name); 
			window.location.href = url;
		}})
	},
	downloadRexTFV: function() {
		this.action("rextfv_download_grant", {callback: function(el, res) {
			var name = el.topology.data.attrs.name + "_" + el.data.attrs.name + '_rextfv.tar.gz';
			var url = "http://" + el.data.attrs.host_info.address + ":" + el.data.attrs.host_info.fileserver_port + "/" + res + "/download?name=" + encodeURIComponent(name); 
			window.location.href = url;
		}})
	},
	changeTemplate: function(tmplName,action_callback) {
		this.action("change_template", {
			params:{
				tmplName: tmplName
				},
			callback: action_callback
			}
		);
	},
	uploadFile: function(window_title, grant_action, use_action) {
		if (window.location.protocol == 'https:') { //TODO: fix this.
			showError("Upload is currently not available over HTTPS. Load this page via HTTP to do uploads.");
			return;
		}
		this.action(grant_action, {callback: function(el, res) {
			var url = "http://" + el.data.attrs.host_info.address + ":" + el.data.attrs.host_info.fileserver_port + "/" + res + "/upload";
			var iframe = $('<iframe id="upload_target" name="upload_target">Test</iframe>');
			// iframe.load will be triggered a moment after iframe is added to body
			// this happens in a seperate thread so we cant simply wait for it (esp. on slow Firefox)
			iframe.load(function(){ 
				iframe.off("load");
				iframe.load(function(){
					iframe.remove();
					this.info.remove();
					this.info = null;	
					el.action(use_action);
					$('#upload_from').remove();
					iframe.remove();
				});
				var t = this;							
				var div = $('<div/>');
				this.upload_form = $('<form method="post" id="upload_form" enctype="multipart/form-data" action="'+url+'" target="upload_target"><input type="file" name="upload" onChange="javascript: $(\'#upload_window_upload\').button(\'enable\');"/></form>');
				div.append(this.upload_form);
				this.info = new Window({
					title: window_title, 
					content: div, 
					autoShow: true, 
					width:300,
					buttons: [{
						text: "Upload",
						id: "upload_window_upload",
						disabled: true,
						click: function() {		
							t.upload_form.css("display","none");
							$('#upload_window_upload').button("disable");
							$('#upload_window_cancel').button("disable");
							t.upload_form.submit();
							div.append($('<div style="text-align:center;"><img src="../img/loading_big.gif" /></div>'));
						},
					},
					{
						text: "Cancel",
						id: "upload_window_cancel",
						click: function() {
							t.info.hide();
							t.info.remove();
							t.info = null;
						},
					}]										
				});
			});
			iframe.css("display", "none");
			$('body').append(iframe);			
		}});
	},
	uploadImage: function() {
		this.uploadFile("Upload Image","upload_grant","upload_use");	
	},
	uploadRexTFV: function() {
		this.uploadFile("Upload Executable Archive","rextfv_upload_grant","rextfv_upload_use");
	},
	action_start: function() {
		this.action("start");
	},
	action_stop: function() {
		this.action("stop");
	},
	action_prepare: function() {
		this.action("prepare");
	},
	action_destroy: function() {
		this.action("destroy");
	},
	updateDependent: function() {
		for (var i = 0; i < this.children.length; i++) {
			this.children[i].update();
			this.children[i].updateDependent();
		}
		if (this.connection) {
			this.connection.update();
			this.connection.updateDependent();			
		}
	},
	removeChild: function(ch) {
		for (var i = 0; i < this.children.length; i++)
	     if (this.children[i].id == ch.id)
	      this.children.splice(i, 1);
	},
	remove: function(callback, ask) {
		if (this.busy) return;
		if (ask && this.editor.options.safe_mode && ! confirm("Do you want to delete this element?")) return;
		this.setBusy(true);
		this.triggerEvent({operation: "remove", phase: "begin"});
		var t = this;
		var removed = false;
		var waiter = function(obj) {
			t.removeChild(obj);
			if (t.children.length) return;
			if (removed) return;
			removed = true;
			ajax({
				url: 'element/'+t.id+'/remove',
			 	successFn: function(result) {
			 		t.paintRemove();
			 		delete t.topology.elements[t.id];
			 		if (t.parent) t.parent.removeChild(t);
			 		t.setBusy(false);
			 		if (callback) callback(t);
			 		t.topology.onUpdate();
					t.triggerEvent({operation: "remove", phase: "end"});
			 	},
			 	errorFn: function(error) {
			 		this.errorWindow = new errorWindow({error:error});
			 		t.setBusy(false);
					t.triggerEvent({operation: "remove", phase: "error"});
			 	}
			});			
		}
		for (var i=0; i<this.children.length; i++) this.children[i].remove(waiter);
		if (this.connection) this.connection.remove();
		waiter(this);
	},
	name: function() {
		var name = this.data.attrs.name;
		if (this.parent) name = this.parent.name() + "." + name;
		return name;
	}
});

var createElementMenu = function(obj) {
	var header= {
		html:'<span>'+obj.name()+'<small><br />Element'+
		(editor.options.show_ids ? 
				" #"+obj.id : 
				"")+
		(editor.options.show_sites_on_elements && obj.component_type=="element" && obj.data.attrs && "site" in obj.data.attrs ? "<br />"+
				(obj.data.attrs.host_info && obj.data.attrs.host_info.site ? 
						"at "+editor.sites_dict[obj.data.attrs.host_info.site].description : 
						(obj.data.attrs.site ? 
								"will be at " + editor.sites_dict[obj.data.attrs.site].description : 
								"no site selected")  ) : 
				"")+
		'</small></span>', 
		type:"html"
	}
	var menu;
	
	if (obj.busy) {
		menu={
			callback: function(key, options) {},
			items: {
				"header": header,
				"busy_indicator": {
					name:'Please wait for the current action to finish and re-open this menu.',
					icon:'loading'
				}
			}
		}
	} else {
		menu= {
			callback: function(key, options) {},
			items: {
				"header": header,
				"connect": obj.isConnectable() ? {
					name:'Connect',
					icon:'connect',
					callback: function(){
						obj.editor.onElementConnectTo(obj);
					}
				} : null,
				"start": obj.actionEnabled("start") ? {
					name:'Start',
					icon:'start',
					callback: function(){
						obj.action_start();
					}
				} : null,
				"stop": obj.actionEnabled("stop") ? {
					name:"Stop",
					icon:"stop",
					callback: function(){
						obj.action_stop();
					}
				} : null,
				"prepare": obj.actionEnabled("prepare") ? {
					name:"Prepare",
					icon:"prepare",
					callback: function(){
						obj.action_prepare();
					}
				} : null,
				"destroy": obj.actionEnabled("destroy") ? {
					name:"Destroy",
					icon:"destroy",
					callback: function(){
						obj.action_destroy();
					}
				} : null,
				"sep2": "---",
				"console": obj.consoleAvailable() ? {
					name:"Console",
					icon:"console",
					items: {
						"console_novnc": obj.data.attrs.websocket_pid ? {
							name:"NoVNC (HTML5+JS)",
							icon:"novnc",
							callback: function(){
								obj.openConsoleNoVNC();
							}
						} : null,
						"console_java": {
							name: "Java applet",
							icon: "java-applet",
							callback: function(){
								obj.openConsole();
							}
						}, 
						"console_link": {
							name:"vnc:// link",
							icon:"console",
							callback: function(){
								obj.openVNCurl();
							}
						},
						"console_info": {
							name:"VNC Information",
							icon:"info",
							callback: function(){
								obj.showVNCinfo();
							}
						},
					}
				} : null,
				"used_addresses": obj.data.attrs.used_addresses ? {
					name:"Used addresses",
					icon:"info",
					callback: function(){
						obj.showUsedAddresses();
					}
				} : null,
				"usage": {
					name:"Resource usage",
					icon:"usage",
					callback: function(){
						obj.showUsage();
					}
				},
				"disk_image": (obj.actionEnabled("download_grant") || obj.actionEnabled("upload_grant")) || obj.actionEnabled("change_template") ? { 
					name: "Disk image",
					icon: "drive",
					items: {
						"change_template": obj.actionEnabled("change_template") ? {
							name:"Change Template",
							icon:"edit",
							callback: function() {
								obj.showTemplateWindow();
							}
						} : null,
						"download_image": obj.actionEnabled("download_grant") ? {
							name:"Download image",
							icon:"download",
							callback: function(){
								obj.downloadImage();
							}
						} : null,
						"upload_image": obj.actionEnabled("upload_grant") ? {
							name:"Upload custom image",
							icon:"upload",
							callback: function(){
								obj.uploadImage();
							}
						} : null,
					}
				} : null,
				"rextfv": obj.actionEnabled("rextfv_download_grant") || obj.actionEnabled("rextfv_upload_grant") || obj.rextfvStatusSupport() ? {
					name:"Executable archive",
					icon:"rextfv",
					items: {
						"download_rextfv": obj.actionEnabled("rextfv_download_grant") ? {
							name:"Download Archive",
							icon:"download",
							callback: function(){
								obj.downloadRexTFV();
							}
						} : null,
						"upload_rextfv": obj.actionEnabled("rextfv_upload_grant") ? {
							name:"Upload Archive",
							icon:"upload",
							callback: function(){
								obj.uploadRexTFV();
							}
						} : null,
						"rextfv_status": obj.rextfvStatusSupport() ? {
							name:"Status",
							icon:"info",
							callback: function(){
								obj.openRexTFVStatusWindow();
							}
						} : null,
					},
				} : null,
				"sep3": "---",
				"configure": {
					name:'Configure',
					icon:'configure',
					callback:function(){
					obj.showConfigWindow(true);
					}
				},
				"debug": obj.editor.options.debug_mode ? {
					name:'Debug',
					icon:'debug',
					callback: function(){
						obj.showDebugInfo();
					}
				} : null,
				"sep4": "---",
				"remove": obj.isRemovable() ? {
					name:'Delete',
					icon:'remove',
					callback: function(){
						obj.remove(null, true);
					}
				} : null
			}
		};
	}
	for (var name in menu.items) {
		if (! menu.items[name]) {
			delete menu.items[name];
			continue;
		}
		var menu2 = menu.items[name];
		if (menu2.items) for (var name2 in menu2.items) if (! menu2.items[name2]) delete menu2.items[name2]; 
	}
	return menu;
};

var createComponentMenu = function(obj) {
	switch (obj.component_type) {
		case "element":
			return createElementMenu(obj);
		case "connection":
			return createConnectionMenu(obj);
	}
};

['right', 'longclick'].forEach(function(trigger) {
	$.contextMenu({
		selector: 'rect,circle', //filtering on classes of SVG objects does not work
		trigger: trigger,
		build: function(trigger, e) {
			return createComponentMenu(trigger[0].obj);
		}
	});	
});

var UnknownElement = Element.extend({
	paint: function() {
		var pos = this.getAbsPos();
		this.circle = this.canvas.circle(pos.x, pos.y, 15).attr({fill: "#CCCCCC"});
		this.innerText = this.canvas.text(pos.x, pos.y, "?").attr({"font-size": 25});
		this.text = this.canvas.text(pos.x, pos.y+22, this.data.type + ": " + this.data.attrs.name);
		this.enableDragging(this.circle);
		this.enableDragging(this.innerText);
		this.enableClick(this.circle);
		$(this.circle.node).attr("class", "tomato element selectable");
		this.enableClick(this.innerText);
	},
	paintRemove: function(){
		this.circle.remove();
		this.innerText.remove();
		this.text.remove();
	},
	paintUpdate: function() {
		var pos = this.getAbsPos();
		this.circle.attr({cx: pos.x, cy:pos.y});
		this.innerText.attr({x: pos.x, y:pos.y});
		this.text.attr({x: pos.x, y: pos.y+22});
		this.enableDragging(this.circle);
		this.circle.node.obj = this;
	}
});

var IconElement = Element.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconSize = {x: 32, y:32};
		this.busy = false;
		editor.rextfv_status_updater.add(this, 1);
	},
	iconUrl: function() {
		return "img/" + this.data.type + "32.png";
	},
	isMovable: function() {
		return this._super() && !this.busy;
	},
	setBusy: function(busy) {
		this._super(busy);
		this.paintUpdate();
	},
	updateStateIcon: function() {
		
		//set 'host has problems' icon if host has problems
		if (this.data.attrs.host_info && this.data.attrs.host_info.problems && this.data.attrs.host_info.problems.length != 0) {
			this.errIcon.attr({'title':'The Host for this device has problems. Contact an Administrator.'});
			this.errIcon.attr({'src':'/img/error.png'});
		} else {
			this.errIcon.attr({'title':''});
			this.errIcon.attr({'src':'/img/pixel.png'})
		}
		
		if (this.busy) {
			this.stateIcon.attr({src: "img/loading.gif", opacity: 1.0});
			this.stateIcon.attr({title: "Action Running..."});
			this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
			this.rextfvIcon.attr({title: ""});
			return;			
		}

		//set state icon
		switch (this.data.state) {
			case "started":
				this.stateIcon.attr({src: "img/started.png", opacity: 1.0});
				this.stateIcon.attr({title: "State: Started"});
				break;
			case "prepared":
				this.stateIcon.attr({src: "img/prepared.png", opacity: 1.0});
				this.stateIcon.attr({title: "State: Prepared"});
				break;
			case "created":
			default:
				this.stateIcon.attr({src: "img/pixel.png", opacity: 0.0});
				this.stateIcon.attr({title: "State: Created"});
				break;
		}
		
		//set RexTFV icon
		if (this.rextfvStatusSupport() && this.data.state=="started") {
			rextfv_stat = this.data.attrs.rextfv_run_status;
			if (rextfv_stat.readable) {
				if (rextfv_stat.isAlive) {
					this.rextfvIcon.attr({src: "img/loading.gif", opacity: 1.0});
					this.rextfvIcon.attr({title: "Executable Archive: Running"});
				} else {
					if (rextfv_stat.done) {
						this.rextfvIcon.attr({src: "img/tick.png", opacity: 1.0});
						this.rextfvIcon.attr({title: "Executable Archive: Done"});
					} else {
						this.rextfvIcon.attr({src: "img/cross.png", opacity: 1.0});
						this.rextfvIcon.attr({title: "Executable Archive: Unknown. Probably crashed."});
					}
				}
			} else {
				this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
				this.rextfvIcon.attr({title: ""});
			}
		} else {
			this.rextfvIcon.attr({src: "img/pixel.png", opacity: 0.0});
			this.rextfvIcon.attr({title: ""});
		}
		
	},
	getRectObj: function() {
		return this.rect[0];
	},
	paint: function() {
		var pos = this.canvas.absPos(this.getPos());
		this.icon = this.canvas.image(this.iconUrl(), pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2-5, this.iconSize.x, this.iconSize.y);
		this.text = this.canvas.text(pos.x, pos.y+this.iconSize.y/2, this.data.attrs.name);
		this.stateIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2-10, pos.y+this.iconSize.y/2-15, 16, 16);
		this.errIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2, pos.y-this.iconSize.y/2-10, 16, 16);
		this.rextfvIcon = this.canvas.image("img/pixel.png", pos.x+this.iconSize.x/2, pos.y-this.iconSize.y/2+8, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		this.updateStateIcon();
		//hide icon below rect to disable special image actions on some browsers
		this.rect = this.canvas.rect(pos.x-this.iconSize.x/2, pos.y-this.iconSize.y/2-5, this.iconSize.x, this.iconSize.y + 10).attr({opacity: 0.0, fill:"#FFFFFF"});
		this.enableDragging(this.rect);
		this.enableClick(this.rect);
		this.rect.node.obj = this;
		this.rect.conditionalClass("tomato", true);
		this.rect.conditionalClass("element", true);
		this.rect.conditionalClass("selectable", true);
		this.rect.conditionalClass("connectable", this.isConnectable());
		this.rect.conditionalClass("removable", this.isRemovable());
	},
	paintRemove: function(){
		this.icon.remove();
		this.text.remove();
		this.stateIcon.remove();
		this.rect.remove();
	},
	paintUpdate: function() {
		if (! this.icon) return;
		var pos = this.getAbsPos();
		this.icon.attr({src: this.iconUrl(), x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2-5});
		this.stateIcon.attr({x: pos.x+this.iconSize.x/2-10, y: pos.y+this.iconSize.y/2-15});
		this.errIcon.attr({x: pos.x+this.iconSize.x/2, y: pos.y-this.iconSize.y/2-10});
		this.rextfvIcon.attr({x: pos.x+this.iconSize.x/2, y: pos.y-this.iconSize.y/2+8});
		this.rect.attr({x: pos.x-this.iconSize.x/2, y: pos.y-this.iconSize.y/2-5});
		this.text.attr({x: pos.x, y: pos.y+this.iconSize.y/2, text: this.data.attrs.name});
		this.updateStateIcon();
		$(this.rect.node).attr("class", "tomato element selectable");
		this.rect.conditionalClass("connectable", this.isConnectable());
		this.rect.conditionalClass("removable", this.isRemovable());
	}
});

var VPNElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconSize = {x: 32, y:16};
	},
	iconUrl: function() {
		return dynimg(32,"vpn",this.data.attrs.mode,null);
	},
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	isEndpoint: function() {
		return false;
	},
	getConnectTarget: function(callback) {
		return this.topology.createElement({type: "tinc_endpoint", parent: this.data.id}, callback);
	}
});

var ExternalNetworkElement = IconElement.extend({
	init: function(topology, data, canvas) {
		this._super(topology, data, canvas);
		this.iconSize = {x: 32, y:32};

	},
	iconUrl: function() {
		return editor.networks.getNetworkIcon(this.data.attrs.kind);
	},
	configWindowSettings: function() {
		var config = this._super();
		config.order = ["name", "kind"];
		
		var networkInfo = {};
		var networks = this.editor.networks.getAllowed();
		
		for (var i=0; i<networks.length; i++) {
			var info = $('<div class="hoverdescription" style="display: inline;"></div>');
			var d = $('<div class="hiddenbox"></div>');
			var p = $('<p style="margin:4px; border:0px; padding:0px; color:black;"></p>');
			var desc = $('<table></table>');
			p.append(desc);
			d.append(p);
			
			net = networks[i];
			
			info.append('<img src="/img/info.png" />');

			if (net.description) {
				desc.append($('<tr><td style="background:white;"><img src="/img/info.png" /></td><td style="background:white;">'+net.description+'</td></tr>'));
			
			}
			
			info.append(d);
			networkInfo[net.kind] = info;
		}
		
		config.special.kind = new ChoiceElement({
			label: "Network kind",
			name: "kind",
			info: networkInfo,
			choices: createMap(this.editor.networks.getAll(), "kind", "label"),
			value: this.data.attrs.kind || this.caps.attrs.kind["default"],
			disabled: !this.attrEnabled("kind")
		});
		return config;
	},
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	isEndpoint: function() {
		return false;
	},
	getConnectTarget: function(callback) {
		return this.topology.createElement({type: "external_network_endpoint", parent: this.data.id}, callback);
	}
});

var createMap = function(listOfObj, keyAttr, valueAttr, startMap) {
	var map = startMap ? copy(startMap) : {};
	for (var i = 0; i < listOfObj.length; i++) 
		map[listOfObj[i][keyAttr]] = typeof valueAttr === "function" ? valueAttr(listOfObj[i]) : listOfObj[i][valueAttr];
	return map;
};

var VMElement = IconElement.extend({
	isConnectable: function() {
		return this._super() && !this.busy;
	},
	iconUrl: function() {
		return this.getTemplate() ? this.getTemplate().iconUrl() : this._super(); 
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	isEndpoint: function() {
		var default_ = true;
		if (this.data && this.data.type == "repy") {
			default_ = false;
			var tmpl = this.getTemplate();
			if (tmpl && tmpl.subtype == "device") default_ = true;
		}
		return (this.data.attrs && this.data.attrs._endpoint != null) ? this.data.attrs._endpoint : default_;
	},
	getTemplate: function() {
		return this.editor.templates.get(this.data.type, this.data.attrs.template);
	},
	showTemplateWindow: function(callback_before_finish,callback_after_finish) {
		var window = new TemplateWindow({
			element: this,
			width: 400,
			callback_after_finish: callback_after_finish,
			callback_before_finish: callback_before_finish
		});
		window.show();
	},
	configWindowSettings: function() {
		var config = this._super();
		config.order = ["name", "site", "profile", "template", "_endpoint"];
		
		var profileInfo = {};
		var profiles = this.editor.profiles.getAllowed(this.data.type);
		var profile_helptext = null;
		if (!editor.allowRestrictedProfiles)
			profile_helptext = 'If you need more performance, contact your administrator.';
		
		for (var i=0; i<profiles.length; i++) {
			var info = $('<div class="hoverdescription" style="display: inline;"></div>');
			var d = $('<div class="hiddenbox"></div>');
			var p = $('<p style="margin:4px; border:0px; padding:0px; color:black;"></p>');
			var desc = $('<table></table>');
			p.append(desc);
			d.append(p);
			
			prof = profiles[i];
			
			info.append('<img src="/img/info.png" />');

			if (prof.description) {
				desc.append($('<tr><td style="background:white;"></td><td style="background:white;">'+prof.description+'</td></tr>'));
			}
			
			if (prof.cpus) {
				desc.append($('<tr><td style="background:white;">CPUs</td><td style="background:white;">'+prof.cpus+'</td></tr>'));
			}
			
			if (prof.ram) {
				desc.append($('<tr><td style="background:white;">RAM</td><td style="background:white;">'+prof.ram+' MB</td></tr>'));
			}
			
			if (prof.diskspace) {
				desc.append($('<tr><td style="background:white;">Disk</td><td style="background:white;">'+prof.diskspace+' MB</td></tr>'));
			}
			
			if (prof.restricted) {
				info.append('<img src="/img/lock_open.png" />');
				desc.append($('<tr><td style="background:white;"><img src="/img/lock_open.png" /></td><td>This profile is restricted; you have access to restricted profiles.</td></tr>'));
			}
			
			info.append(d);
			profileInfo[prof.name] = info;
		}
		
		
		var siteInfo = {};
		var sites = this.editor.sites;
		
		for (var i=0; i<sites.length; i++) {
			var info = $('<div class="hoverdescription" style="display: inline;"></div>');
			var d = $('<div class="hiddenbox"></div>');
			var p = $('<p style="margin:4px; border:0px; padding:0px; color:black;"></p>');
			var desc = $('<table></table>');
			p.append(desc);
			d.append(p);
			
			site = sites[i];
			
			info.append('<img src="/img/info.png" />');
			
			if (this.data.attrs.host_info.site && (this.data.attrs.site == null)) {
				info.append('<img src="/img/automatic.png" />'); //TODO: insert a useful symbol for "automatic" here and on the left column one line below
				desc.append($('<tr><td><img src="/img/automatic.png" /></td><td>This site has been automatically selected by the backend.</td></tr>'))
			}

			if (site.description_text) {
				desc.append($('<tr><td style="background:white;"><img src="/img/info.png" /></td><td style="background:white;">'+site.description_text+'</td></tr>'));
			}
			
			var hostinfo_l = '<tr><td style="background:white;"><img src="/img/server.png" /></td><td style="background:white;"><h3>Hosted By:</h3>';
			var hostinfo_r = '</td></tr>';
			if (site.organization.homepage_url) {
				hostinfo_l = hostinfo_l + '<a href="' + site.organization.homepage_url + '">';
				hostinfo_r = '</a>' + hostinfo_r;
			}
			if (site.organization.image_url) {
				hostinfo_l = hostinfo_l + '<img style="max-width:8cm;max-height:8cm;" src="' + site.organization.image_url + '" title="' + site.organization.description + '" />';
			} else {
				hostinfo_l = hostinfo_l + site.organization.description;
			}
			desc.append($(hostinfo_l + hostinfo_r));
			
			info.append(d);
			siteInfo[site.name] = info;
		}
		
		config.special.template = new TemplateElement({
			label: "Template",
			name: "template",
			value: this.data.attrs.template || this.caps.attrs.template["default"],
			custom_template: this.data.attrs.custom_template,
			disabled: (this.data.state == "started"),
			type: this.data.type,
			call_element: this
		});
		config.special.site = new ChoiceElement({
			label: "Site",
			name: "site",
			info: siteInfo,
			choices: createMap(this.editor.sites, "name", function(site) {
				return (site.description || site.name) + (site.location ? (", " + site.location) : "");
			}, {"": "Any site"}),
			value: this.data.attrs.host_info.site || this.data.attrs.site || this.caps.attrs.site["default"],
			disabled: !this.attrEnabled("site")
		});
		config.special.profile = new ChoiceElement({
			label: "Performance Profile",
			name: "profile",
			info: profileInfo,
			choices: createMap(this.editor.profiles.getAll(this.data.type), "name", "label"),
			value: this.data.attrs.profile || this.caps.attrs.profile["default"],
			disabled: !this.attrEnabled("profile"),
			help_text: profile_helptext
		});
		config.special._endpoint = new ChoiceElement({
			label: "Segment seperation",
			name: "_endpoint",
			choices: {true: "Seperates segments", false: "Connects segments"},
			value: this.isEndpoint(),
			inputConverter: Boolean.parse
		}); 
		return config;
	},
	getConnectTarget: function(callback) {
		return this.topology.createElement({type: this.data.type + "_interface", parent: this.data.id}, callback);
	}
});

var ChildElement = Element.extend({
	getHandlePos: function() {
		var ppos = this.parent.getAbsPos();
		var cpos = this.connection ? this.connection.getCenter() : {x:0, y:0};
		var xd = cpos.x - ppos.x;
		var yd = cpos.y - ppos.y;
		var magSquared = (xd * xd + yd * yd);
		var mag = settings.childElementDistance / Math.sqrt(magSquared);
		return {x: ppos.x + (xd * mag), y: ppos.y + (yd * mag)};
	},
	isEndpoint: function() {
		return this.parent.isEndpoint();
	},
	getAbsPos: function() {
		return this.parent.getAbsPos();
	},
	isRemovable: function() {
		return this._super() && !this.busy;
	},
	paint: function() {
		var pos = this.getHandlePos();
		this.circle = this.canvas.circle(pos.x, pos.y, 7).attr({fill: "#CDCDB3"});
		$(this.circle.node).attr("class", "tomato element");
		this.circle.node.obj = this;
		this.enableClick(this.circle);
	},
	paintRemove: function(){
		this.circle.remove();
	},
	paintUpdate: function() {
		var pos = this.getHandlePos();
		this.circle.attr({cx: pos.x, cy: pos.y});
	},
	updateData: function(data) {
		this._super(data);
		if (this.parent && ! this.connection && this.isRemovable()) this.remove();
	}
});

var VMInterfaceElement = ChildElement.extend({
	showUsedAddresses: function() {
		var t = this;
		this.update(true, function() {
	 		var win = new Window({
	 			title: "Used addresses on " + t.name(),
	 			content: '<p>'+t.data.attrs.used_addresses.join('<br/>')+'</p>',
	 			autoShow: true
	 		});			
		});
	}
});

var VMConfigurableInterfaceElement = VMInterfaceElement.extend({
	onConnected: function() {
		var hint = this.getAddressHint();
		if (hint == "dhcp") this.modify({"use_dhcp": true});
		else this.modify({"ip4address": "10.0." + hint[0] + "." + hint[1] + "/24"});
	}
});

var SwitchPortElement = ChildElement.extend({
	configWindowSettings: function() {
		var config = this._super();
		config.ignore = ["peers"];
		return config;
	}	
});

var HiddenChildElement = Element.extend({
	getPos: function() {
		return this.parent.getPos();
	},
	getAbsPos: function() {
		return this.parent.getAbsPos();
	}
});

var Template = Class.extend({
	init: function(options) {
		this.classoptions = options;
		this.type = options.tech;
		this.subtype = options.subtype;
		this.name = options.name;
		this.label = options.label || options.name;
		this.description = options.description || "no description available";
		this.nlXTP_installed = options.nlXTP_installed || false;
		this.creation_date = options.creation_date;
		this.restricted = options.restricted;
		this.preference = options.preference;
		this.showAsCommon = options.show_as_common;
		this.icon = options.icon;
	},
	iconUrl: function() {
		return this.icon || dynimg(32,this.type,(this.subtype?this.subtype:null),(this.name?this.name:null));
	},
	menuButton: function(options) {
		var hb = '<p style="margin:4px; border:0px; padding:0px; color:black;"><table><tbody>'+
					'<tr><td><img src="/img/info.png"></td><td>'+this.description+'</td></tr>';
		if (!this.nlXTP_installed) {
			hb = hb + '<tr><td><img src="/img/error.png" /></td>'+
				'<td>No nlXTP guest modules are installed. Executable archives will not auto-execute and status '+
				'will be unavailable. <a href="'+help_baseUrl+'/rextfv/guestmodules" target="_help">More Info</a></td></tr>';
		}
		hb = hb + "</tbody></table></p>";
		return Menu.button({
			name: options.name || (this.type + "-" + this.name),
			label: options.label || this.label || (this.type + "-" + this.name),
			icon: this.iconUrl(),
			toggle: true,
			toggleGroup: options.toggleGroup,
			small: options.small,
			func: options.func,
			hiddenboxHTML: hb
		});
	},
	labelForCommon: function() {
		var label = this.label.replace(/[ ]*\(.*\)/, "");
		switch (this.type) {
			case "kvmqm":
				label += " (KVM)";
				break;
			case "openvz":
				label += " (OpenVZ)";
				break;
			case "repy":
				label += " (Repy)";
				break;
		}
		return label;
	},
	infobox: function() {
		var restricted_icon = "/img/lock_open.png";
		var restricted_text = "You have the permission to use this restricted template.";
		if (!editor.allowRestrictedTemplates) {
			restricted_icon = "/img/lock.png";
			restricted_text = "This template is restricted. Contact an administrator if you want to get access to restricted templates.";
		}
		
		var info = $('<div class="hoverdescription" style="display: inline;"></div>');
		var d = $('<div class="hiddenbox"></div>');
		var p = $('<p style="margin:4px; border:0px; padding:0px; color:black;"></p>');
		var desc = $('<table></table>');
		p.append(desc);
		d.append(p);
		
		if (this.description || this.creation_date) {

			info.append('<img src="/img/info.png" />');
		
			if (this.description) {
				desc.append($('<tr><td style="background:white;"><img src="/img/info.png" /></td><td style="background:white;">'+this.description+'</td></tr>'));	
			}
			
			if (this.creation_date) {
				desc.append($('<tr><td style="background:white;"><img src="/img/calendar.png" /></td><td style="background:white;">'+this.creation_date+'</td></tr>'));
			}
			
		} else {
			info.append('<img src="/img/invisible16.png" />');
		}
		
		if (!this.nlXTP_installed) {
			desc.append($('<tr><td style="background:white;"><img src="/img/warning16.png" /></td><td style="background:white;">No nlXTP guest modules are installed. Executable archives will not auto-execute and status will be unavailable. <a href="'+help_baseUrl+'/rextfv/guestmodules" target="_help">More Info</a></td></tr>'));
			info.append('<img src="/img/warning16.png" />');
		} else {
			info.append('<img src="/img/invisible16.png" />');
		}
		
		if (this.restricted) {
			desc.append($('<tr><td style="background:white;"><img src="'+restricted_icon+'" /></td><td style="background:white;">'+restricted_text+'</td></tr>'));
			info.append('<img src="'+restricted_icon+'" />');
		} else {
			info.append('<img src="/img/invisible16.png" />');
		}
		
		info.append(d);
		
		return info;
	}
});

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

var TemplateStore = Class.extend({
	init: function(data,editor) {
		this.editor = editor;
		data.sort(function(t1, t2){
			var t = t2.attrs.preference - t1.attrs.preference;
			if (t) return t;
			if (t1.attrs.name < t2.attrs.name) return -1;
			if (t2.attrs.name < t1.attrs.name) return 1;
			return 0;
		});
		this.types = {};
		for (var i=0; i<data.length; i++)
		 if (data[i].type == "template")
		  this.add(new Template(data[i].attrs));
	},
	add: function(tmpl) {
		if (! this.types[tmpl.type]) this.types[tmpl.type] = {};
		this.types[tmpl.type][tmpl.name] = tmpl;
	},
	getAll: function(type) {
		if (! this.types[type]) return [];
		var tmpls = [];
		for (var name in this.types[type])
			tmpls.push(this.types[type][name]);
		return tmpls;
	},
	getAllowed: function(type) {
		var templates = this.getAll(type);
		if (!this.editor.allowRestrictedTemplates) {
			var templates_filtered = [];
			for (var i = 0; i<templates.length;i++) {
				if (!(templates[i].restricted))
					templates_filtered.push(templates[i]);
			}
			templates = templates_filtered;
		}
		return templates;
	},
	get: function(type, name) {
		if (! this.types[type]) return null;
		return this.types[type][name];
	},
	getCommon: function() {
		var common = [];
		for (var type in this.types)
		 for (var name in this.types[type])
		  if (this.types[type][name].showAsCommon && (!this.types[type][name].restricted || this.editor.allowRestrictedTemplates))
		   common.push(this.types[type][name]);
		return common;
	}
});

var Profile = Class.extend({
	init: function(options) {
		this.type = options.tech;
		this.name = options.name;
		this.label = options.label || options.name;
		this.restricted = options.restricted;
		this.description = options.description;
		this.diskspace = options.diskspace;
		this.cpus = options.cpus;
		this.ram = options.ram;
	}
});

var ProfileStore = Class.extend({
	init: function(data,editor) {
		this.editor = editor;
		data.sort(function(t1, t2){
			var t = t2.attrs.preference - t1.attrs.preference;
			if (t) return t;
			if (t1.attrs.name < t2.attrs.name) return -1;
			if (t2.attrs.name < t1.attrs.name) return 1;
			return 0;
		});
		this.types = {};
		for (var i=0; i<data.length; i++)
		 if (data[i].type == "profile")
		  this.add(new Profile(data[i].attrs));
	},
	add: function(tmpl) {
		if (! this.types[tmpl.type]) this.types[tmpl.type] = {};
		this.types[tmpl.type][tmpl.name] = tmpl;
	},
	getAll: function(type) {
		if (! this.types[type]) return [];
		var tmpls = [];
		for (var name in this.types[type]) tmpls.push(this.types[type][name]);
		return tmpls;
	},
	getAllowed: function(type) {
		var profs = this.getAll(type);
		if (!this.editor.allowRestrictedProfiles) {
			var profs_filtered = [];
			for (var i = 0; i<profs.length;i++) {
				if (!(profs[i].restricted))
					profs_filtered.push(profs[i]);
			}
			profs = profs_filtered;
		}
		return profs;
	},
	get: function(type, name) {
		if (! this.types[type]) return null;
		return this.types[type][name];
	}
});

var NetworkStore = Class.extend({
	init: function(data,editor) {

		this.editor = editor;
		data.sort(function(t1, t2){
			var t = t2.attrs.preference - t1.attrs.preference;
			if (t) return t;
			if (t1.attrs.kind < t2.attrs.kind) return -1;
			if (t2.attrs.kind < t1.attrs.kind) return 1;
			return 0;
		});
		this.nets = [];
		for (var i=0; i<data.length; i++) {
		 if (data[i].type == "network") {
			 net = data[i].attrs;
			 if (!net.icon) {
				 net.icon = this.getNetworkIcon(net.kind);
			 }
			 this.nets.push(net);
		 }
		}
	},
	getAll: function() {
		return this.nets;
	},
	getAllowed: function() {
		var allowedNets = this.getAll()
		if (!this.editor.allowRestrictedNetworks) {
			var nets_filtered = [];
			
			for (var i = 0; i<allowedNets.length;i++) {
				if (!(allowedNets[i].restricted)) {
					nets_filtered.push(allowedNets[i]);
				}
			}
			allowedNets = nets_filtered;
		}
		return allowedNets;
	},
	getCommon: function() {
		var common = [];
		for (var i = 0; i < this.nets.length; i++)
		 if (this.nets[i].show_as_common && (!this.nets[i].restricted || this.editor.allowRestrictedNetworks))
		   common.push(this.nets[i]);
		return common;
	},
	getNetworkIcon: function(kind) {
		return dynimg(32,"network",kind.split("/")[0],(kind.split("/")[1]?kind.split("/")[1]:null));
	}
});

var RexTFV_status_updater = Class.extend({
	init: function(options) {
		this.options = options;
		this.elements = [];
	},
	updateAll: function(t) { //this should be called by a timer. Takes RexTFV_status_updater as argument.
		toRemove = [];
		//iterate through all entries, update them, and then update their retry-count according to the refreshed data.
		//do not remove elements while iterating. instead, put to-be-removed entries in the toRemove array.
		for (var i=0; i<t.elements.length; i++) {
			entry = t.elements[i];
			entry.element.update();
			if (entry.element.rextfvStatusSupport() && entry.element.data.attrs.rextfv_run_status.running) {
				entry.tries = 1;
			} else {
				entry.tries--;
				if (entry.tries < 0) {
					toRemove.push(entry)
				}
			}
		}
		//remove entries marked as to-remove.
		for (var i=0; i<toRemove.length; i++) {
			t.remove(toRemove[i]);
		}
	},
	add: function(el,tries) { //every entry has a number of retries and an element attached to it.
								// retries are decreased when the status is something else than "running".
								// retries are set to 1 if the status is "running".
								// the idea is that the system might need some time to detect RexTFV activity after uploading the archive or starting a device.
								// retries == 1 is the default. if retries < 0, the entry is removed. This means, after the status is set to "not running",
								// the editor will update the element twice before removing it.
		
		
		//first, search whether this element is already monitored. If yes, update number of tries if necessary (keep the bigger one). exit funciton if found.
		for (var i=0; i<this.elements.length; i++) {
			if (this.elements[i].element == el) {
				found = true;
				if (this.elements[i].tries < tries)
					this.elements[i].tries = tries;
				return
			}
		}
		
		//if the search hasn't found anything, simply append this.
		this.elements.push({
			element: el,
			tries: tries
		})
	},
	// usually only called by this. removes an entry.
	remove: function(entry) {
		for (var i=0; i<this.elements.length; i++) {
			entry_found = this.elements[i];
			if (entry_found == entry) {
				this.elements.splice(i,1);
				return;
			}
		}
	}
});

var Mode = {
	select: "select",
	connect: "connect",
	connectOnce: "connect_once",
	remove: "remove",
	position: "position"
}

var Editor = Class.extend({
	init: function(options) {
		this.options = options;
		
		this.rextfv_status_updater = new RexTFV_status_updater(); //has to be created before any element.
		var t = this;
		
		this.allowRestrictedTemplates= false;
		this.allowRestrictedProfiles = false;
		this.allowRestrictedNetworks = false;
		this.isDebugUser = options.isDebugUser;
		for (var i=0; i<this.options.user.flags.length; i++) {
			if (this.options.user.flags[i] == "restricted_profiles") this.allowRestrictedProfiles = true;
			if (this.options.user.flags[i] == "restricted_templates") this.allowRestrictedTemplates= true;
			if (this.options.user.flags[i] == "restricted_networks") this.allowRestrictedNetworks= true;
		}
		
		this.options.grid_size = this.options.grid_size || 25;
		this.options.frame_size = this.options.frame_size || this.options.grid_size;
		this.listeners = [];
		this.capabilities = this.options.capabilities;
		this.menu = new Menu(this.options.menu_container);
		this.topology = new Topology(this);
		this.workspace = new Workspace(this.options.workspace_container, this);
		this.sites = this.options.sites;
		this.profiles = new ProfileStore(this.options.resources,this);
		this.templates = new TemplateStore(this.options.resources,this);
		this.networks = new NetworkStore(this.options.resources,this);
		this.buildMenu(this);
		this.setMode(Mode.select);
		
		
		this.sites_dict = {};
		for (s in this.sites) {
			this.sites_dict[this.sites[s].name] = this.sites[s];
		}
				
		this.workspace.setBusy(true);
		ajax ({
			url: "topology/"+options.topology+"/info",
			successFn: function(data){
				t.topology.load(data);
				t.workspace.setBusy(false);
				if (t.topology.data.attrs._initialized) {
					if (t.topology.data.timeout - new Date().getTime()/1000.0 < t.topology.editor.options.timeout_settings.warning) t.topology.renewDialog();
					if (t.topology.data.attrs._notes_autodisplay) t.topology.notesDialog();
				} else 
					if (t.topology.data.attrs._tutorial_url) {
						t.topology.modify({
							"_initialized": true
						});
						t.topology.action("renew", {params:{
							"timeout": t.options.timeout_settings["default"]
						}});
					} else
						if (t.topology.data.attrs._initialized!=undefined)
							t.topology.initialDialog();
				t.workspace.updateTopologyTitle();
			}
		});

		setInterval(function(){t.rextfv_status_updater.updateAll(t.rextfv_status_updater)}, 1200);
	},
	triggerEvent: function(event) {
		log(event);
		for (var i = 0; i < this.listeners.length; i++) this.listeners[i](event);
	},
	setOption: function(name, value) {
		this.options[name] = value;
		this.optionCheckboxes[name].setChecked(value);
		this.onOptionChanged(name);
		this.triggerEvent({component: "editor", object: this, operation: "option", name: name, value: value});
	},
	onOptionChanged: function(name) {
		this.topology.onOptionChanged(name);
		this.workspace.onOptionChanged(name);
		this.workspace.updateTopologyTitle();
	},
	optionMenuItem: function(options) {
		var t = this;
		return Menu.checkbox({
			name: options.name, label: options.label, tooltip: options.tooltip,
			func: function(value){
				t.options[options.name]=value != null;
			  t.onOptionChanged(options.name);
			},
			checked: this.options[options.name]
		});
	},
	onElementConnectTo: function(el) {
		this.setMode(Mode.connectOnce);
		this.connectElement = el;
	},
	onElementSelected: function(el) {
		switch (this.mode) {
			case Mode.connectOnce:
				if (! el.isConnectable()) return;
				this.topology.createConnection(el, this.connectElement);
				this.setMode(Mode.select);
				break;
			case Mode.connect:
				if (! el.isConnectable()) return;
				if (this.connectElement) {
					this.topology.createConnection(el, this.connectElement);
					this.connectElement = null;
				} else this.connectElement = el;
				break;
			case Mode.remove:
				if (! el.isRemovable()) return;
				el.remove();
				break;
			default:
				break;
		}
	},
	onConnectionSelected: function(con) {
		switch (this.mode) {
			case Mode.remove:
				con.remove();
				break;
			default:
				break;
		}
	},
	setMode: function(mode) {
		this.mode = mode;
		this.workspace.onModeChanged(mode);
		if (mode != Mode.position) this.positionElement = null;
		if (mode != Mode.connect && mode != Mode.connectOnce) this.connectElement = null;
		this.triggerEvent({component: "editor", object: this, operation: "mode", mode: this.mode});
	},
	setPositionElement: function(el) {
		this.positionElement = el;
		this.setMode(Mode.position);		
	},
	createPositionElementFunc: function(el) {
		var t = this;
		return function() {
			t.setPositionElement(el);
		}
	},
	createModeFunc: function(mode) {
		var t = this;
		return function() {
			t.setMode(mode);
		}
	},
	createElementFunc: function(el) {
		var t = this;
		return function(pos) {
			var data = copy(el, true);
			data.attrs._pos = pos;
			t.topology.createElement(data);
			t.selectBtn.click();
		}
	},
	createUploadFunc: function(type) {
		var t = this;
		return function(pos) {
			var data = {type: type, attrs: {_pos: pos}};
			t.topology.createElement(data, function(el1) {
					el1.showConfigWindow(false, function (el2) { 
							el2.action("prepare", { callback: function(el3) {el3.uploadImage();} });	
						}
				);
				}
			);
			t.selectBtn.click();
		};
	},
	createTemplateFunc: function(tmpl) {
		return this.createElementFunc({type: tmpl.type, attrs: {template: tmpl.name}});
	},
	buildMenu: function(editor) {
		var t = this;

		var toggleGroup = new ToggleGroup();
	
		var tab = this.menu.addTab("Home");

		var group = tab.addGroup("Modes");
		this.selectBtn = Menu.button({
			label: "Select & Move",
			icon: "img/select32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			checked: true,
			func: this.createModeFunc(Mode.select)
		});
		group.addElement(this.selectBtn);
		group.addStackedElements([
			Menu.button({
				label: "Connect",
				icon: "img/connect16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createModeFunc(Mode.connect)
			}),
			Menu.button({
				label: "Delete",
				name: "mode-remove",
				icon: "img/eraser16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createModeFunc(Mode.remove)
			})
		]);

		var group = tab.addGroup("Topology control");
		group.addElement(Menu.button({
			label: "Start",
			icon: "img/start32.png",
			toggle: false,
			small: false,
			func: function() {
				t.topology.action_start();
			}
		}));
		group.addElement(Menu.button({
			label: "Stop",
			icon: "img/stop32.png",
			toggle: false,
			small: false,
			func: function() {
				t.topology.action_stop();
			}
		}));
		group.addStackedElements([
			Menu.button({
				label: "Prepare",
				icon: "img/prepare16.png",
				toggle: false,
				small: true,
				func: function() {
					t.topology.action_prepare();
				}
			}),
			Menu.button({
				label: "Destroy",
				icon: "img/destroy16.png",
				toggle: false,
				small: true,
				func: function() {
					t.topology.action_destroy();
				}
			})
		]);
		
		var group = tab.addGroup("Common elements");
		var common = t.templates.getCommon();
		for (var i=0; i < common.length; i++) {
			var tmpl = common[i];
			group.addElement(tmpl.menuButton({
				label: tmpl.labelForCommon(),
				toggleGroup: toggleGroup,
				small: false,
				func: this.createPositionElementFunc(this.createTemplateFunc(tmpl))
			}));
		}
		for (var i=0; i < settings.otherCommonElements.length; i++) {
			var cel = settings.otherCommonElements[i];
			group.addElement(Menu.button({
				label: cel.label,
				name: cel.name,
				icon: cel.icon,
				toggle: true,
				toggleGroup: toggleGroup,
				small: false,
				func: this.createPositionElementFunc(this.createElementFunc({
					type: cel.type,
					attrs: cel.attrs
				}))
			}));			
		}
		var common = t.networks.getCommon();
		for (var i=0; i < common.length; i++) {
			var net = common[i];
			group.addElement(Menu.button({
				label: net.label,
				name: net.name,
				icon: "img/internet32.png",
				toggleGroup: toggleGroup,
				small: false,
				func: this.createPositionElementFunc(this.createElementFunc({
					type: "external_network",
					attrs: {kind: net.kind}					
				}))
			}));
		}

		var tab = this.menu.addTab("Devices");

		var group = tab.addGroup("Linux (OpenVZ)");
		var tmpls = t.templates.getAllowed("openvz");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
			 btns.push(tmpls[i].menuButton({
				toggleGroup: toggleGroup,
				small: true,
				func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Linux (KVM)");
		var tmpls = t.templates.getAllowed("kvmqm", "linux");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype == "linux")
			  btns.push(tmpls[i].menuButton({
				toggleGroup: toggleGroup,
				small: true,
				func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Other (KVM)");
		var tmpls = t.templates.getAllowed("kvmqm");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype != "linux")
			  btns.push(tmpls[i].menuButton({
			  	toggleGroup: toggleGroup,
				small: true,
			  	func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Scripts (Repy)");
		var tmpls = t.templates.getAllowed("repy");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype == "device")
		  btns.push(tmpls[i].menuButton({
		  	toggleGroup: toggleGroup,
		  	small: true,
		  	func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Upload own images");
		group.addStackedElements([
			Menu.button({
				label: "KVM image",
				name: "kvm-custom",
				icon: "img/kvm32.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createPositionElementFunc(this.createUploadFunc("kvmqm"))
			}),
			Menu.button({
				label: "OpenVZ image",
				name: "openvz-custom",
				icon: "img/openvz32.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createPositionElementFunc(this.createUploadFunc("openvz"))
			}),
			Menu.button({
				label: "Repy script",
				name: "repy-custom",
				icon: "img/repy32.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createPositionElementFunc(this.createUploadFunc("repy"))
			})
		]);


		var tab = this.menu.addTab("Network");

		var group = tab.addGroup("VPN Elements");
		group.addElement(Menu.button({
			label: "Switch",
			name: "vpn-switch",
			icon: "img/switch32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "tinc_vpn",
				attrs: {mode: "switch"}
			}))
		}));
		group.addElement(Menu.button({
			label: "Hub",
			name: "vpn-hub",
			icon: "img/hub32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "tinc_vpn",
				attrs: {mode: "hub"}
			}))
		}));

		var group = tab.addGroup("Scripts (Repy)");
		group.addElement(Menu.button({
			label: "Custom script",
			name: "repy-custom",
			icon: "img/repy32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createUploadFunc("repy"))
		}));
		var tmpls = t.templates.getAllowed("repy");
		var btns = [];
		for (var i=0; i<tmpls.length; i++)
		 if(tmpls[i].subtype != "device")
		  btns.push(tmpls[i].menuButton({
		  	toggleGroup: toggleGroup,
		  	small: true,
		  	func: this.createPositionElementFunc(this.createTemplateFunc(tmpls[i]))
		})); 
		group.addStackedElements(btns);

		var group = tab.addGroup("Networks");
		var common = t.networks.getAllowed();
		var buttonstack = [];
		for (var i=0; i < common.length; i++) {
			var net = common[i];
			var inet_button = Menu.button({
				label: net.label,
				name: net.name,
				icon: net.icon,
				toggle: true,
				toggleGroup: toggleGroup,
				small: !net.big_icon,
				func: this.createPositionElementFunc(this.createElementFunc({
					type: "external_network",
					attrs: {kind: net.kind}					
				}))
			});
			if (net.big_icon) {
				if(buttonstack.length>0) {
					group.addStackedElements(buttonstack);
					buttonstack=[];
				}
				group.addElement(inet_button);
			} else {
				buttonstack.push(inet_button);
			}
		}
		group.addStackedElements(buttonstack);
		
		
		
		
		var tab = this.menu.addTab("Topology");

		var group = tab.addGroup("");
		group.addElement(Menu.button({
			label: "Renew",
			icon: "img/renew.png",
			toggle: false,
			small: false,
			func: function(){
				t.topology.renewDialog();
			}
		}));
		group.addElement(Menu.button({
			label: "Notes",
			icon: "img/notes32.png",
			toggle: false,
			small: false,
			func: function(){
				t.topology.notesDialog();
			}
		}));
		group.addElement(Menu.button({
			label: "Resource usage",
			icon: "img/office-chart-bar.png",
			toggle: false,
			small: false,
			func: function(){
				t.topology.showUsage();
			}
		}));
		group.addStackedElements([
			Menu.button({
				label: "Rename",
				icon: "img/rename.png",
				toggle: false,
				small: true,
				func: function(){
					t.topology.renameDialog();
				}
			}),
			Menu.button({
				label: "Export",
				icon: "img/export16.png",
				toggle: false,
				small: true,
				func: function() {
					window.open(document.URL+ "/export");
				}
			}),
			Menu.button({
				label: "Delete",
				name: "topology-remove",
				icon: "img/cross.png",
				toggle: false,
				small: true,
				func: function() {
					t.topology.remove();
				}
			})
		]);
		group.addElement(Menu.button({
			label: "Users & Permissions",
			icon: "img/user32.png",
			toggle: false,
			small: false,
			func: function() {
				t.workspace.permissionsWindow.createUserPermList();
				t.workspace.permissionsWindow.show();
			}
		}));


		var tab = this.menu.addTab("Options");

		var group = tab.addGroup("Editor");
		this.optionCheckboxes = {
			safe_mode: this.optionMenuItem({
				name:"safe_mode",
   				label:"Safe mode",
   				tooltip:"Asks before all destructive actions"
   			}),
   			snap_to_grid: this.optionMenuItem({
   				name:"snap_to_grid",
   				label:"Snap to grid",
   				tooltip:"All elements snap to an invisible "+this.options.grid_size+" pixel grid"
   			}),
   			fixed_pos: this.optionMenuItem({
		        name:"fixed_pos",
		        label:"Fixed positions",
		        tooltip:"Elements can not be moved"
		    }),

		    colorify_segments: this.optionMenuItem({
		        name:"colorify_segments",
		        label:"Colorify segments",
		        tooltip:"Paint different network segments with different colors"
		    }),
		    
		    show_ids: this.optionMenuItem({
		        name:"show_ids",
		        label:"Show IDs",
		        tooltip:"Show IDs in right-click menus"
		    }),
		    
		    show_sites_on_elements: this.optionMenuItem({
		        name:"show_sites_on_elements",
		        label:"Show Element Sites",
		        tooltip:"Show the site an element is located at in its right-click menu"
		    }),
		    
		    debug_mode: this.optionMenuItem({
		        name:"debug_mode",
		        label:"Debug mode",
		        tooltip:"Displays debug messages"
		    })
		};

		group.addStackedElements([this.optionCheckboxes.safe_mode, 
									this.optionCheckboxes.snap_to_grid,
									this.optionCheckboxes.colorify_segments,
									this.optionCheckboxes.fixed_pos,
									this.optionCheckboxes.show_ids,
									this.optionCheckboxes.show_sites_on_elements,
									this.optionCheckboxes.debug_mode
								]);

		


		this.menu.paint();
	}
});

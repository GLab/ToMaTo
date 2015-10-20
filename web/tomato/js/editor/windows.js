
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
var showError = function(error) {
	if (ignoreErrors) return;
	new errorWindow({error: { originalResponse: error,},show_error_appendix: true});
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
				show_error_appendix: false,
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
		this.errorContent = $('<div />');

		console.log(error); //keep this logging

		this.errorResponse = $('<div />');

		if(error.parsedResponse) {
			this.errorResponse.append(this.addError(error.parsedResponse.error));
		} else {
			this.errorResponse.append(this.addText(error.originalResponse));
		}
		
		if(!(editor.options.isDebugUser || editor.options.debug_mode) && !options.show_error_appendix) {
			this.errorResponse.append('<p style="color: #a0a0a0">'+this.options.error_message_appendix+'</p>');
		}
		this.errorContent.append(this.errorResponse);
		this.div.append(this.errorContent);

	},

	addError: function(error) {
		//Show additional information for debug users like the errorcode, the errormessage and errordata for debugusers
		this.setTitle("Error: "+error.typemsg);
		
		this.content = $('<div />');
		this.errorMessage = $('<p>'+error.errormsg+'</p>');

		this.content.append(this.errorMessage);
		
		if(editor.options.isDebugUser && editor.options.debug_mode) {
			
			this.content.append($('<b>Error details:</b>'))
			var errorDebugInfos = $('<table />');
			log(error); //keep this logging
			for(var line=0;line<error.debuginfos.length;line++) {
				errorDebugInfos.append($('<tr><th>'+error.debuginfos[line].th+'</th><td>'+error.debuginfos[line].td+'</td></tr>'));
			}
			this.content.append(errorDebugInfos);
		}
		return this.content;
	},
	
	addText: function(text) {
		var message = $('<p>'+text.replace(/(\r\n)|(\r)|(\n)/g, '<br />')+'</p>');
		return message;
	}
});


var TutorialWindow = Window.extend({
	init: function(options) {
			this.pos = {my: "right bottom", at: "right bottom", of: "#editor"};
			options.position = this.pos;
			this._super(options);
			if (options.hideCloseButton)
				$(this.div.parent()[0].getElementsByClassName("ui-dialog-titlebar-close")).hide();
			
			if (!options.tutorialVisible)
				return;
				
			this.editor = options.editor
				
			this.tutorialState = options.tutorial_state;
			
			//create UI
			var t = this
			this.text = $("<div>.</div>");
			this.buttons = $("<div style=\"text-align:right; margin-bottom:0px; padding-bottom:0px;\"></div>");
			this.backButton = $('<button class="btn btn-default"><span class="glyphicon glyphicon-arrow-left"></span> Back</button>');
			this.buttons.append(this.backButton);
			this.backButton.click(function() {t.tutorialGoBack(); });
			this.skipButton = $('<button class="btn btn-default">Skip <span class="glyphicon glyphicon-arrow-right"></span></button>');
			this.buttons.append("&nbsp;");
			this.buttons.append(this.skipButton);
			this.skipButton.click(function() {t.tutorialGoForth(); });
			this.closeButton = $('<button class="btn btn-success">Close Tutorial <span class="glyphicon glyphicon-remove"></span></button>');
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
		if (this.tutorialState.step > 0) {
			this.tutorialState.step--;
			this.skipButton.show();
			this.closeButton.hide();
		}
		if (this.tutorialState.step == 0) {
			this.backButton.hide();
		}
		this.updateText();
		this.updateStatusToBackend();
		//this.setPosition(this.pos);
	},
	tutorialGoForth: function() {
		if (this.tutorialState.step + 1 < this.tutorialSteps.length) {
			this.tutorialState.step++;	
			this.backButton.show();
		}
		if (this.tutorialState.step + 1 == this.tutorialSteps.length) {
			this.skipButton.hide();
			this.closeButton.show();
		}
		this.updateText();
		this.updateStatusToBackend();
		//this.setPosition(this.pos);
	},
	triggerProgress: function(triggerObj) { //continues tutorial if correct trigger
		if (this.tutorialVisible) { //don't waste cpu time if not needed... trigger function may be complex.
			if (this.tutorialSteps[this.tutorialState.step].trigger != undefined) {
				try {
					if (this.tutorialSteps[this.tutorialState.step].trigger(triggerObj)) {
						this.tutorialGoForth();
					}
				}
				catch(e) {}
			}
		}
	},
	loadTutorial: function() {//loads editor_tutorial.tutName; tutID: position in "tutorials" array
		//load tutorial
		this.tutorialSteps = tutorial_steps
		
		//set visible buttons
		if (this.tutorialState.step == 0) {
			this.backButton.hide();
			this.skipButton.show();
			this.closeButton.hide();
		} else {
			this.backButton.show();
			if (this.tutorialState.step == this.tutorialSteps.length - 1) {
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
		var text = this.tutorialSteps[this.tutorialState.step].text;
		this.text.empty();
		this.text.append(text);

		this.setTitle("Tutorial [" + (this.tutorialState.step+1) + "/" + this.tutorialSteps.length + "]");
		
		//dirty hack: un-set the window's height property
		this.div[0].style.height = "";
		
		var helpUrl=this.tutorialSteps[this.tutorialState.step].help_page;
		if (helpUrl) {
			this.helpLinkTarget=help_baseUrl+"/"+helpUrl;
			this.helpButton.show();
		} else {
			this.helpButton.hide();
		}
		
		var skipButtonText = this.tutorialSteps[this.tutorialState.step].skip_button;
		var highlight_skipbutton = true;
		if (!(skipButtonText)) {
			skipButtonText = "Skip";
			highlight_skipbutton = false;
		}
		this.skipButton[0].innerHTML = skipButtonText + ' <span class="glyphicon glyphicon-arrow-right"></span>';
		if (highlight_skipbutton) { //this has not the 'skip' text on it, i.e., highlight the button
			if (this.tutorialState.step == 0) { //this is the first step, which has the 'start tutorial' button
				$(this.skipButton[0].getElementsByClassName('glyphicon')[0]).removeClass('glyphicon-arrow-right');
				$(this.skipButton[0].getElementsByClassName('glyphicon')[0]).addClass('glyphicon-play');
				$(this.skipButton[0]).removeClass('btn-default btn-info');
				$(this.skipButton[0]).addClass('btn-success');
			} else {
				$(this.skipButton[0].getElementsByClassName('glyphicon')[0]).removeClass('glyphicon-play');
				$(this.skipButton[0].getElementsByClassName('glyphicon')[0]).addClass('glyphicon-arrow-right');
				$(this.skipButton[0]).removeClass('btn-success btn-default');
				$(this.skipButton[0]).addClass('btn-info');
			}
		} else {
			$(this.skipButton[0].getElementsByClassName('glyphicon')[0]).removeClass('glyphicon-play');
			$(this.skipButton[0].getElementsByClassName('glyphicon')[0]).addClass('glyphicon-arrow-right');
			$(this.skipButton[0]).removeClass('btn-info btn-success');
			$(this.skipButton[0]).addClass('btn-default');
		}
		
		this.div.dialog("option","height","auto");

	},
	getData: function() {
		return this.tutorialState.data;
	},
	setData: function(data) {
		this.tutorialState.data = data;
		this.updateStatusToBackend();
	},
	updateStatusToBackend: function() {
		ajax({
			url: 'topology/'+this.editor.topology.id+'/modify',
		 	data: {_tutorial_state: this.tutorialState}
		});
	},
	closeTutorial: function() {
		var t = this
		if (confirm("You have completed the tutorial. This topology will now be removed. (Press \"Cancel\" to keep the topology)")) {
			this.editor.topology.remove();	
		} else {
			ajax({
				url: 'topology/'+this.editor.topology.id+'/modify',
			 	data: {_tutorial_disabled: true}
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
		if (type == "bool") {
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
		var windowTitle = "Change Template for "+this.element.data.name;
		if (editor.options.show_ids) windowTitle = windowTitle + ' ['+this.element.data.id+']'
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
		
		
		
		this.value = this.element.data.template;
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
		var winID = Math.random();

		//build template list entry
		var div_formgroup = $('<div class="form-group"></div>');
		for(var i=0; i<this.choices.length; i++) {
			var t = this.choices[i];

			
			var div_option = $('<div class="col-md-10" />');
			var div_radio = $('<div class="radio"></div>');
			div_option.append(div_radio);
			var radio = $('<input type="radio" name="template" value="'+t.name+'" id="'+winID+t.name+'" />');
			
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
			
			if (t.name == this.element.data.template) {
				radio.prop("checked",true);
			}
			
			var radiolabel = $('<label for="'+winID+t.name+'">'+t.label+'</label>');
			radiolabel.click( function(){
				$(this).children('input').attr('checked', 'checked');
			});
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
		options.close_keep = true;
		
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
		
		
		if (!this.options.allowChange) {
			this.options.allowChange = (this.topology.data.permissions[this.options.ownUserId] == "owner");
		}
		if (!this.options.allowChange) {
			this.addButton.attr("disabled",true);
		}
		
		
		this.userTable = $('<div />');
		var tableHeader = $('<div class="row"><div class="col-sm-1" /><div class="col-sm-5"><h4>User</h4></div><div class="col-sm-3"><h4>Permission</h4></div><div class="col-sm-3" /></div>');
		this.userTable.append(tableHeader); 
		this.userList.empty();
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
		var td_name = $('<div class="col-sm-5" />');
		var td_perm = $('<div class="col-sm-3" />');
		var td_buttons = $('<div class="col-sm-3" />');
		var td_icon = $('<div class="col-sm-1" />');
	
		
		ajax({
			url:	'account/'+username+'/info',
			successFn: function(data) {
				td_name.append(''+data.realname+' (<a href="/account/info/'+data.id+'" target="_blank" style="font-size:10pt;">'+data.id+'</a>)');
				
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
		this.userTable.append(tr);
		
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
								 		new errorWindow({error:error});
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
		 		new errorWindow({error:error});
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


var ConnectionAttributeWindow = AttributeWindow.extend({
	init: function(options, con) {
		options.helpTarget = help_baseUrl+"/editor:configwindow_connection";
		this._super(options);

		var panels = $('<ul class="nav nav-tabs" style="margin-bottom: 1pt;"></ul>');
		this.table.append($('<div class="form-group" />').append(panels));

		var tab_content = $('<div class="tab-content" />');
		if (con.attrEnabled("emulation")) {
			this.emulation_elements = [];
			var t = this;
			var el = new CheckboxElement({
				name: "emulation",
				value: con.data.emulation == undefined ? con.caps.attributes.emulation['default'] : con.data.emulation,
				callback: function(el, value) {
					t.updateEmulationStatus(value);
				}
			});
			this.elements.push(el);
			var link_emulation = $('<div class="tab-pane active" id="Link_Emulation" />');
			link_emulation.append($('<div class="form-group" />')
						.append($('<label class="col-sm-4 control-label">Enabled</label>'))
						.append($('<div class="col-sm-8" style="padding: 0px" />')
						.append(el.getElement())));
			
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
			link_emulation.append($('<div class="form-group" />')
				.append($('<label class="col-sm-4 control-label">Direction</label>'))
				.append($('<div class="col-sm-4" />').append(fromDir).append(dir1))
				.append($('<div class="col-sm-4" />').append(toDir).append(dir2))
			);
			//simple fields
			var order = ["bandwidth", "delay", "jitter", "distribution", "lossratio", "duplicate", "corrupt"];
			for (var i = 0; i < order.length; i++) {
				var name = order[i];
				var info_from = con.caps.attributes[name+"_from"];
				info_from.name = name + "_from";
				var el_from = this.autoElement(info_from, con.data[name+"_from"], true)
				this.elements.push(el_from);
				this.emulation_elements.push(el_from);
				var info_to = con.caps.attributes[name+"_to"];
				info_to.name = name + "_to";
				var el_to = this.autoElement(info_to, con.data[name+"_to"], true)
				this.elements.push(el_to);
				this.emulation_elements.push(el_to);
				link_emulation.append($('<div class="form-group" />')
					.append($('<label class="col-sm-4 control-label" style="padding: 0;" />').append(con.caps.attributes[name+"_to"].label))
					.append($('<div class="col-sm-3" style="padding: 0;"/>').append(el_from.getElement()))
					.append($('<div class="col-sm-3" style="padding: 0;" />').append(el_to.getElement()))
					.append($('<div class="col-sm-2" style="padding: 0;" />').append(con.caps.attributes[name+"_to"].value_schema.unit))
				);
			}
			this.updateEmulationStatus(con.data.emulation);
			
			tab_content.append(link_emulation);
			this.table.append(tab_content);
			panels.append($('<li class="active"><a href="#Link_Emulation" data-toggle="tab">Link Emulation</a></li>'));
		}
		if (con.attrEnabled("capturing")) {
			var t = this;
			var packet_capturing = $('<div class="tab-pane" id="Packet_capturing" />');
			
			this.capturing_elements = [];
			var el = new CheckboxElement({
				name: "capturing",
				value: con.data.capturing,
				callback: function(el, value) {
					t.updateCapturingStatus(value);
				}
			});
			this.elements.push(el);
			packet_capturing.append($('<div class="form-group" />')
					.append($('<label class="col-sm-6 control-label">Enabled</label>'))
					.append($('<div class="col-sm-6" />')
					.append(el.getElement())));

			var order = ["capture_mode", "capture_filter"];
			for (var i = 0; i < order.length; i++) {
				var name = order[i];
				var info = con.caps.attributes[name];
				info.name = name;
				var el = this.autoElement(info, con.data[name], con.attrEnabled(name));
				this.capturing_elements.push(el);
				this.elements.push(el);
				packet_capturing.append($('<div class="form-group" />')
					.append($('<label class="col-sm-6 control-label">').append(con.caps.attributes[name].label))
					.append($('<div class="col-sm-6" />').append(el.getElement()))
				);
			}
			this.updateCapturingStatus(con.data.capturing);

			tab_content.append(packet_capturing);
			this.table.append(tab_content);
			panels.append($('<li><a href="#Packet_capturing" data-toggle="tab">Packet capturing</a></li>'));
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
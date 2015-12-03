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
		
		if(editor.options.isDebugUser && editor.options.debug_mode && error.debuginfos) {
			
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


var showError = function(error) {
	if (ignoreErrors) return;
	new errorWindow({error: { originalResponse: error,},show_error_appendix: true});
}



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
	var html = $('<input style="margin-left:0.25cm;" type="checkbox" id="'+options.name+'" /> <label style="margin-right:0.25cm;" for="'+options.name+'">'+options.label+'</label>');
	if (options.tooltip) html.attr("title", options.tooltip);
	if (options.func) html.click(function(){
		options.func(html.prop("checked"));
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


var createTopologyMenu = function(obj) {
	var menu = {
		callback: function(key, options) {},
		items: {
			"header": {
				html:"<span>"+obj.name()+"<small><br />Topology "+(editor.options.show_ids ? ' ['+obj.id+']' : "")+'</small></span>',
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


var createConnectionMenu = function(obj) {
	var menu = {
		callback: function(key, options) {},
		items: {
			"header": {
				html:'<span>'+obj.name_vertical()+"<small><br>Connection"+(editor.options.show_ids ? " ["+obj.id+"]" : "")+'</small></span>', type:"html"
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



var createElementMenu = function(obj) {
	var header= {
		html:'<span>'+obj.name()+'<small><br />Element'+
		(editor.options.show_ids ? 
				" ["+obj.id+"]" :
				"")+
		(editor.options.show_sites_on_elements && obj.component_type=="element" && obj.data && "site" in obj.data ? "<br />"+
				(obj.data.host_info && obj.data.host_info.site ?
						"at "+editor.sites_dict[obj.data.host_info.site].label :
						(obj.data.site ?
								"will be at " + editor.sites_dict[obj.data.site].label :
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
				"console": obj.consoleAvailable() || obj.actionEnabled("download_log_grant") ? {
					name:"Console",
					icon:"console",
					items: {
						"console_novnc": obj.consoleAvailable() && obj.data.websocket_pid ? {
							name:"NoVNC (HTML5+JS)",
							icon:"novnc",
							callback: function(){
								obj.openConsoleNoVNC();
							}
						} : null,
						"console_java": obj.consoleAvailable() ? {
							name: "Java applet",
							icon: "java-applet",
							callback: function(){
								obj.openConsole();
							}
						} : null,
						"console_link": obj.consoleAvailable() ? {
							name:"vnc:// link",
							icon:"console",
							callback: function(){
								obj.openVNCurl();
							}
						} : null,
						"console_info": obj.consoleAvailable() ? {
							name:"VNC Information",
							icon:"info",
							callback: function(){
								obj.showVNCinfo();
							}
						} : null,
						"sepconsole": obj.actionEnabled("download_log_grant") && obj.consoleAvailable() ? "---" : null,
						"log": obj.actionEnabled("download_log_grant") ? {
							name:"Download Log",
							icon:"console_download",
							callback: function(){
								obj.downloadLog();
							},
						} : null,
					}
				} : null,
				"used_addresses": obj.data.used_addresses ? {
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

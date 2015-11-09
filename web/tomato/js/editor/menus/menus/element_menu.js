



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
						"upload_image_file": obj.actionEnabled("upload_grant") ? {
							name:"Upload custom image from disk",
							icon:"upload",
							callback: function(){
								obj.uploadImage_fromFile();
							}
						} : null,
						"upload_image_url": (obj.actionEnabled("upload_grant") && editor.web_resources.executable_archives.length > 0) ? {
							name:"Upload custom image from URL",
							icon:"upload",
							callback: function(){
								obj.uploadImage_byURL();
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
						"upload_rextfv_file": obj.actionEnabled("rextfv_upload_grant") ? {
							name:"Upload Archive from Disk",
							icon:"upload",
							callback: function(){
								obj.uploadRexTFV_fromFile();
							}
						} : null,
						"upload_rextfv_url": obj.actionEnabled("rextfv_upload_grant") ? {
							name:"Upload Archive from URL",
							icon:"upload",
							callback: function(){
								obj.uploadRexTFV_byURL();
							}
						} : null,
						"upload_rextfv_default": obj.actionEnabled("rextfv_upload_grant") ? {
							name:"Use a Default Archive",
							icon:"upload",
							callback: function(){
								obj.uploadRexTFV_fromDefault();
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



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
		this.web_resources = this.options.web_resources;
		this.profiles = new ProfileStore(this.options.resources.profiles,this);
		this.templates = new TemplateStore(this.options.resources.templates,this);
		this.networks = new NetworkStore(this.options.resources.networks,this);
		this.buildMenu(this);
		this.setMode(Mode.select);

		// create web_resources.executable_archives_dict
		this.web_resources.executable_archives_dict = {};
		for(var i=0; i<this.web_resources.executable_archives.length; i++) {
			var archive = this.web_resources.executable_archives[i];
			if (archive.icon==undefined || archive.icon==null) archive.icon="/img/rextfv.png";
			this.web_resources.executable_archives_dict[archive.name] = archive;
		}
		
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
				if (t.topology.data._initialized) {
					if (t.topology.data.timeout - new Date().getTime()/1000.0 < t.topology.editor.options.timeout_settings.warning) t.topology.renewDialog();
					if (t.topology.data._notes_autodisplay) t.topology.notesDialog();
				} else 
					if (t.topology.data._tutorial_url) {
						t.topology.modify({
							"_initialized": true
						});
						t.topology.action("renew", {params:{
							"timeout": t.options.timeout_settings["default"]
						}});
					} else
						if (t.topology.data._initialized!=undefined)
							t.topology.initialDialog();
				t.workspace.updateTopologyTitle();
				t.options.onready();
			}
		});
		
		this.setWorkspaceContentMenu();
		
		setInterval(function(){t.rextfv_status_updater.updateSome(t.rextfv_status_updater)}, 1000);
	},
	triggerEvent: function(event) {
		log(event); //keep this logging
		for (var i = 0; i < this.listeners.length; i++) this.listeners[i](event);
	},
	setWorkspaceContentMenu: function() {
		var t = this;
		$('.tomato.workspace').on('contextmenu',function(e) {
			if(t.mode == Mode.connect || t.mode == Mode.connectOnce) {
				e.preventDefault();
				e.stopImmediatePropagation();
				
				t.setMode(Mode.select);
				t.workspace.connectPath.hide();
				
				$("#Modes_SelectandMove").addClass("ui-state-highlight");
				$("#Modes_Connect").removeClass("ui-state-highlight");
				
			}
		});
		
		['right', 'longclick'].forEach(
				function(trigger) {
					$.contextMenu({
						selector: '.tomato.workspace',
						trigger: trigger,
						build: function(trigger, e) {
							return createTopologyMenu(trigger[0].obj);
						}
				});	
			});
		
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
		for(element in this.topology.elements) {
			this.topology.elements[element].paintUpdate();
		}
		for(connection in this.topology.connections) {
			this.topology.connections[connection].paintUpdate();
		}
	},
	optionMenuItem: function(options) {
		var t = this;

		return Menu.checkbox({
			name: options.name, 
			label: options.label, 
			tooltip: options.tooltip,
			func: function(value){
				t.setOption(options.name,value);
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
			data._pos = pos;
			t.topology.createElement(data);
			t.selectBtn.click();
		}
	},
	createUploadFunc: function(type) {
		var t = this;
		return function(pos) {
			var data = {type: type, _pos: pos};
			t.topology.createElement(data, function(el1) {
					el1.showConfigWindow(false, function (el2) { 
							el2.action("prepare", { callback: function(el3) {el3.uploadImage_fromFile();} });
						}
				);
				}
			);
			t.selectBtn.click();
		};
	},
	createTemplateFunc: function(tmpl) {
		return this.createElementFunc({type: tmpl.type, template: tmpl.name});
	},
	buildMenu: function(editor) {
		var t = this;

		var toggleGroup = new ToggleGroup();
	
		var tab = this.menu.addTab("Home");

		var group = tab.addGroup("Modes");
		this.selectBtn = Menu.button({
			label: "Select & Move",
			name: "Modes_SelectandMove",
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
				name: "Modes_Connect",
				icon: "img/connect16.png",
				toggle: true,
				toggleGroup: toggleGroup,
				small: true,
				func: this.createModeFunc(Mode.connect)
			}),
			Menu.button({
				label: "Delete",
				name: "Modes_Delete",
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
				func: this.createPositionElementFunc(this.createElementFunc(cel.data))
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
					kind: net.kind
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
			label: "Switch (Tinc)",
			name: "tinc-switch",
			icon: "img/switch32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "tinc_vpn",
				mode: "switch"
			}))
		}));
		group.addElement(Menu.button({
			label: "Hub (Tinc)",
			name: "tinc-hub",
			icon: "img/hub32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "tinc_vpn",
				mode: "hub"
			}))
		}));
		group.addElement(Menu.button({
			label: "Switch (VpnCloud)",
			name: "vpncloud-switch",
			icon: "img/switch32.png",
			toggle: true,
			toggleGroup: toggleGroup,
			small: false,
			func: this.createPositionElementFunc(this.createElementFunc({
				type: "vpncloud"
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
					kind: net.kind
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

		var top_group = tab.addGroup("Topology");
		var view_group = tab.addGroup("View");

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

		    big_editor: this.optionMenuItem({
		    	name:"big_editor",
		    	label:"Big workspace",
		    	tooltip:"Have a bigger editor workspace. Requires page reload."
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
		    }),
		    
		    element_name_on_top: this.optionMenuItem({
		        name:"element_name_on_top",
		        label:"Names on Top",
		        tooltip:"Show element name on top of element the element."
		    }),

		    show_connection_controls: this.optionMenuItem({
		    	name:"show_connection_controls",
		    	label:"Show Connection Controls",
		    	tooltip:"Show network interfaces on elements, and a connection control handle on connections. These might be useful to hide when taking screenshots."
		    })
		};

		top_group.addStackedElements([
									this.optionCheckboxes.safe_mode,
									this.optionCheckboxes.snap_to_grid,
									this.optionCheckboxes.fixed_pos,
									this.optionCheckboxes.big_editor,
									this.optionCheckboxes.debug_mode
								]);
		view_group.addStackedElements([
									this.optionCheckboxes.show_connection_controls,
									this.optionCheckboxes.colorify_segments,
									this.optionCheckboxes.show_ids,
									this.optionCheckboxes.show_sites_on_elements,
									this.optionCheckboxes.element_name_on_top
								]);

		


		this.menu.paint();
	}
});

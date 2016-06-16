var OptionsManager = Class.extend({
	init: function(editor) {

		this.editor = editor;
		this.hasLoaded = false;


		// define topology (topl) and user option entries
		this.topl_opts = [
			{
				name:"safe_mode",
   				label:"Safe mode",
   				tooltip:"Asks before all destructive actions",
   				default_value: true
   			},
   			{
   				name:"snap_to_grid",
   				label:"Snap to grid",
   				tooltip:"All elements snap to an invisible "+this.editor.options.grid_size+" pixel grid",
   				default_value: false
   			},
   			{
		        name:"fixed_pos",
		        label:"Fixed positions",
		        tooltip:"Elements can not be moved",
   				default_value: false
		    },
		    {
		    	name:"big_editor",
		    	label:"Big workspace",
		    	tooltip:"Have a bigger editor workspace. Requires page reload.",
   				default_value: false
		    }
		];
		this.user_opts = [
			{
		        name:"colorify_segments",
		        label:"Colorify segments",
		        tooltip:"Paint different network segments with different colors",
   				default_value: false
		    },
		    {
		        name:"show_ids",
		        label:"Show IDs",
		        tooltip:"Show IDs in right-click menus",
   				default_value: false
		    },
		    {
		        name:"show_sites_on_elements",
		        label:"Show Element Sites",
		        tooltip:"Show the site an element is located at in its right-click menu",
   				default_value: false
		    },
		    {
		        name:"debug_mode",
		        label:"Debug mode",
		        tooltip:"Displays debug messages",
   				default_value: false
		    },
		    {
		        name:"element_name_on_top",
		        label:"Names on Top",
		        tooltip:"Show element name on top of element the element.",
   				default_value: false
		    },
		    {
		    	name:"show_connection_controls",
		    	label:"Show Connection Controls",
		    	tooltip:"Show network interfaces on elements, and a connection control handle on connections. These might be useful to hide when taking screenshots.",
   				default_value: true
		    }
		];

		//disable topology options for non-owners
		//todo: set {enabled: false} in topl_opts entries if user is not owner

		//optimization: save lists of names
		this.topl_opts_keys = [];
		for (var i = 0; i < this.topl_opts.length; i++) {
			this.topl_opts_keys.push(this.topl_opts[i].name)
		}

		this.user_opts_keys = [];
		for (var i = 0; i < this.user_opts.length; i++) {
			this.user_opts_keys.push(this.user_opts[i].name)
		}


		//define how to store keys (user or topology)
		this.store_map = {};
		var t = this;
		for (var i = 0; i < this.topl_opts_keys.length; i++) {
			this.store_map[this.topl_opts_keys[i]] = function(opt, value) {
				//todo: save to account_info instead
				t.editor.topology.modify_value("_"+opt, value);
			}
		}
		for (var i = 0; i < this.user_opts_keys.length; i++) {
			this.store_map[this.user_opts_keys[i]] = function(opt, value) {
				t.editor.topology.modify_value("_"+opt, value);
			}
		}

	},

	loadOpts: function() {
		for (var i = 0; i < this.topl_opts.length; i++) {
			var opt = this.topl_opts[i].name;
			if (this.editor.topology.data["_"+opt] != null) {
				this.editor.setOption(opt, this.editor.topology.data["_"+opt]);
			} else {
				this.editor.setOption(opt, this.topl_opts[i].default_value);
			}
		}
		for (var i = 0; i < this.user_opts.length; i++) {
			//todo: load from account_info instead
			var opt = this.user_opts[i].name;
			if (this.editor.topology.data["_"+opt] != null) {
				this.editor.setOption(opt, this.editor.topology.data["_"+opt]);
			} else {
				this.editor.setOption(opt, this.user_opts[i].default_value);
			}
		}
		this.hasLoaded = true;
	},

	saveOpt: function(opt, value) {
		if (this.hasLoaded)  // do not store anything before options have been loaded
			this.store_map[opt](opt, value);
	},

	buildOptionsTab: function(tab) {
		var topl_options = [];
		for (var i = 0; i < this.topl_opts.length; i++) {
			this.editor.optionCheckboxes[this.topl_opts[i].name] = this.editor.optionMenuItem(this.topl_opts[i])
			topl_options.push(this.editor.optionCheckboxes[this.topl_opts[i].name]);
		}
		var topl_group = tab.addGroup("Topology");
		topl_group.addStackedElements(topl_options);

		var user_options = [];
		for (var i = 0; i < this.user_opts.length; i++) {
		this.editor.optionCheckboxes[this.user_opts[i].name] = this.editor.optionMenuItem(this.user_opts[i])
			user_options.push(this.editor.optionCheckboxes[this.user_opts[i].name]);
		}
		var user_group = tab.addGroup("User");
		user_group.addStackedElements(user_options);
	}
});
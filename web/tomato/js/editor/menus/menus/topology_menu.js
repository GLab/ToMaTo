
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

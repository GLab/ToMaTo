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
			/*
			"cloudshark_capture": obj.captureDownloadable() ? {
				name:"View capture in Cloudshark",
				icon:"cloudshark",
				callback: function(){
					obj.viewCapture();
				}
			} : null,
			*/
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

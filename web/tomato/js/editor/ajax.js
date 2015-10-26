
var ajax = function(options) {
	var t = this;
	$.ajax({
		type: "POST",
	 	async: !options.synchronous,
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

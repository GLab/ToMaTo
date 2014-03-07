function browser_check(filter) {
	return function() {
		return navigator.userAgent.search(filter) != -1;
	}
}

var issues = [
  {
	  type: "warning",
	  check: browser_check(/Chrome\/34/),
	  title: "Browser bug in Chrome 34",
	  description: "Chrome 34 contains a bug which makes the ToMaTo editor unusable as it breaks topology rendering. Please use a different browser or another version of Chrome."
  },
  {
	  type: "note",
	  check: browser_check(/iPhone|iPad|Android|BlackBerry|PlayBook|Kindle|Opera Mobi|Windows Phone/),
	  title: "Touch interfaces not supported",
	  description: "ToMaTo does not have a touch interface at this time. You can use the editor but most likely you will not be able to right-click on elements."
  }            
];

var close_button = '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>'; 

function display_issues(div) {
	for (var i=0; i<issues.length; i++) {
		var issue = issues[i];
		if (! issue.check()) continue;
		switch (issue.type) {
			case "warning": 
				var msg = $('<div class="alert alert-danger fade in">'+close_button+'<h4>'+issue.title+'</h4><p>'+issue.description+'</p></div>');
				div.append(msg);
				msg.alert();
				break;
			case "note":
				var msg = $('<div class="alert alert-warning fade in">'+close_button+'<strong>'+issue.title+'</strong><p>'+issue.description+'</p></div>');
				div.append(msg);
				msg.alert();
				break;
		}
	}
}
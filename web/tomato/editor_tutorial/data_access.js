var editor_tutorial = [
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Data Access tutorial!<br />\
						This tutorial will teach you how you can upload and/or download data to or from your devices.</p>\
					<p class="tutorialExplanation">\
						Let\'s assume you have created this topology, and now you need to put files on your devices to execute your experiment.</p>\
					<p class="tutorialExplanation">\
						<i>This tutorial requires knowledge which has been taught in the beginners\' tutorial</i></p>',
			skip_button: 'Start tutorial'
			},
			{
			trigger:function(obj) { 
					if (obj != undefined) {
						if (obj.component != undefined && 
							obj.operation != undefined &&
							obj.action != undefined &&
							obj.phase != undefined) {
								
							if (obj.action == "prepare" &&
								obj.component == "element" &&
								obj.operation == "action" &&
								obj.phase == "begin") {
								return true;
							}
						}
					}
					return false;
				},
			text:	'<p class="tutorialExplanation">\
						Currently, your topology does only exist as a "plan". This means, that devices do not have any hard drive images or similar.</p>\
					<p> class ="tutorialExplanation">\
						When you prepare the devices, those images will be created from the templates.</p>\
					<p class="tutorialCommand">\
						Prepare your topology\'s devices.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						Wait for both devices to be prepared. Then press "Continue" button.</p>',
			skip_button: "Continue"
			},
			{
			text:"TODO: talk about downloading and uploading images here. Explain how to use this for file distribution (create 1 machine; upload to many) and different cool stuff about images."
			},
			{
			trigger:function(obj) { 
					if (obj != undefined) {
						if (obj.attrs != undefined && 
							obj.component != undefined && 
							obj.operation != undefined &&
							obj.phase != undefined) {
							
							if (obj.attrs.type != undefined && 
								obj.attrs.state != undefined) {
								
								if (obj.attrs.state == "created" && 
									obj.attrs.type == "external_network" && 
									obj.component == "element" &&
									obj.operation == "create" &&
									obj.phase == "end") {
									return true;
								}
							}
						}
					}
					return false;
					},
			text:	'<p class="tutorialExplanation">\
						The easiest way to transmit files to or from your devices is the internet.</p>\
					<p> class ="tutorialExplanation">\
						Devices don\'t have an internet connection by default. To connect them, the first thing you need to do is to create an internet interface</p>\
					<p class="tutorialCommand">\
						Add an "Internet" to your topology. You can find it in the "Home" tab.</p>',
			},
			{
			trigger:function(obj) { 
				console.log("TODO: check if this is a connection between the Internet and a device");
					if (obj != undefined) {
						if (obj.attrs != undefined && 
							obj.component != undefined && 
							obj.operation != undefined &&
							obj.phase != undefined) {
							
							if (obj.attrs.state != undefined) {
								
								if (obj.attrs.state == "created" &&
									obj.component == "connection" &&
									obj.operation == "create" &&
									obj.phase == "end") {
									return true;
								}
							}
						}
					}
					return false;
				},
			text:	'<p class="tutorialCommand">\
						Now, connect your devices with the internet.</p>',
			},
			{
			trigger:function(obj) { 
				console.log("TODO: check if this is a connection between the Internet and a device");
					if (obj != undefined) {
						if (obj.attrs != undefined && 
							obj.component != undefined && 
							obj.operation != undefined &&
							obj.phase != undefined) {
							
							if (obj.attrs.state != undefined) {
								
								if (obj.attrs.state == "created" &&
									obj.component == "connection" &&
									obj.operation == "create" &&
									obj.phase == "end") {
									return true;
								}
							}
						}
					}
					return false;
				},
			text:	'<p class="tutorialCommand">\
						Also, connect the other device to the internet.</p>',
			},
				
			{
			trigger:function(obj) { 
					if (obj != undefined) {
						if (obj.component != undefined && 
							obj.operation != undefined &&
							obj.action != undefined &&
							obj.phase != undefined) {
								
							if (obj.action == "start" &&
								obj.component == "element" &&
								obj.operation == "action" &&
								obj.phase == "begin") {
								return true;
							}
						}
					}
					return false;
				},
			text:	'<p class="tutorialExplanation">\
						<i>In case you wonder about the different look of the connections: You\'ll learn more about this in the "Connections" tutorial. You can ignore it in this tutorial.</i></p>\
					<p class="tutorialExplanation">\
						Of course your devices must be running to be able to access the internet.</p>\
					<p class="tutorialCommand">\
						Start your topology\'s devices.</p>'
			}
];
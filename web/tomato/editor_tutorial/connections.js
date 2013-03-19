var editor_tutorial = [
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Connections tutorial!<br />\
						This tutorial will teach you many things about connections.<br />\
						It might be a bit longer, but you can continue the tutorial from any point in case you close the window.</p>\
					<p class="tutorialExplanation">\
						<i>This tutorial requires knowledge which has been taught in the beginners\' tutorial, and a basic knowledge about the Linux command line.</i></p>',
			skip_button: 'Start tutorial'
			},
			{
			text:	'<p class="tutorialExplanation">\
						To start, let\'s take a closer look at a connection.</p>\
					<p class="tutorialExplanation">\
						Every connection consits of two network interfaces and the connection itself.<br />\
						An interface is represented by a grey circle at a device. Here you can configure the device's network preferences (e.g., ip address).<br />
						The connection is represented by a blue square at its center. Here, you can configure the link (e.g., bandwidth, loss rate, etc).</p>\
					<p class="tutorialExplanation">\
						The options available to a connection depend on the connected devices. The same is for interfaces.</p>',
			skip_button: 'Continue'
			},
			{
			text:	'<p class="tutorialExplanation">\
						Additionally, we have to define some terms:\
						<ul><li><b>Connection</b>: The connection which you can see in this editor. In this tutorial, "Connection" always refers to the blue square on a connection.</li>\
						<li><b>Link</b>: The virtualized representation of a connection</li>\
						<li><b>Link Emulation</b>: The fact that a link acts like a physical link. This means delay, packet loss, etc.<br />
						Link emulation is set on a connection and executed on a link.</li>',
			skip_button: 'Continue'
			},
			{
			trigger:function(obj) { 
					
				mask = {
					attrs: {
						state: "created",
						type: "external_network"
					},
					component: "element",
					operation: "create",
					phase: "end"
				};
				return compareToMask(obj,mask);
			
			  },
			text:	'<p class="tutorialExplanation">\
						By default, a connection can only be created between exactly two devices.\
						If you want to connect multiple devices to the same network, you need a switch.</p>\
					<p class="tutorialExplanation">\
						It is not possible to turn on link emulation on a connection which connects anything with the Internet.
						To be able to do this, we can use a switch</p>\
					<p class="tutorialCommand">\
						Add a switch to your topology, and connect it to both the Internet and your device.</p>'
			},
			{
			trigger:function(obj) { 
				console.log("TODO: check if this is a connection between the switch and a device or the internet");
				mask = {
					attrs: {
						state: "created",
					},
					component: "connection",
					operation: "create",
					phase: "end"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">
						Connect the switch to both elements</p>'
			},
			{
			trigger:function(obj) { 
				console.log("TODO: check if this is a connection between the switch and a device or the internet");
				mask = {
					attrs: {
						state: "created",
					},
					component: "connection",
					operation: "create",
					phase: "end"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">
						Don\'t forget the second connection.</p>'
			},
			
			{
			text:	'<p class="tutorialExplanation">\
						That was it for this tutorial!</p>'
			}
];
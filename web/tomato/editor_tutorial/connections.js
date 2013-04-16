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
						Additionally, we have to define some terms:\
						<ul><li><b>Connection</b>: The connection which you can see in this editor. In this tutorial, "Connection" always refers to the blue square on a connection.</li>\
						<li><b>Link</b>: The virtualized representation of a connection</li>\
						<li><b>Link Emulation</b>: The fact that a link acts like a physical link. This means delay, packet loss, etc.<br />\
						Link emulation is set on a connection and executed on a link.</li>',
			skip_button: 'Continue'
			},
			{
			trigger:function(obj) { 
					
				mask = {
					attrs: {
						state: "created",
						type: "tinc_vpn"
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
						It is not possible to turn on link emulation on a connection which connects anything with the Internet.\
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
			text:	'<p class="tutorialCommand">\
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
			text:	'<p class="tutorialCommand">\
						Don\'t forget the second connection.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						Let\'s take a closer look at a connection.</p>\
					<p class="tutorialExplanation">\
						Every connection consits of two network interfaces and the connection itself.<br />\
						An interface is represented by a grey circle at a device. Here you can configure the device\'s network preferences (e.g., ip address).<br />\
						The connection is represented by a blue square at its center. Here, you can configure the link (e.g., bandwidth, loss rate, etc).</p>\
					<p class="tutorialExplanation">\
						The options available to a connection depend on the connected devices. The same is for interfaces.</p>',
			skip_button: 'Continue'
			},
			{
			trigger:function(obj) { 
				console.log("TODO: check if this is a connection between the switch and a device or the internet");
				mask = {
					component: "connection",
					operation: "attribute-dialog"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">\
						Open the Configure Dialog of the Device-Switch connection.</p>\
					<p class="tutorialExplanation">\
						To open the Configure Dialog, Right-click on the connection (that is, the blue square), and select "Configure".</p>\
					<p class="tutorialExplanation">\
						<i><small>This tutorial will also react if you open the other connection\'s configure dialog (technical issues). In case you wonder what you would see in it: It would be empty.</small></i></p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						You might might need a small overview:</p>\
					<p class="tutorialExplanation">\
						The attributes are devided into two subjects: link emulation and packet capturing.<br />\
						For now, let\'s ignore the packet capturing part, and only look at link emulation.\
					<p class="tutorialExplanation">\
						Values are devided into two columns, one for each direction.<br />\
						Every value only affects packets being sent in that particular direction.<br />\
						The best way to determine the direction of the column is to look at the small graphic. It has the same orientation as the link in the editor, and the red arrow is the direction.</p>\
					<p class="tutorialExplanation">\
						Bandwidth and delay should be self-explaining. By setting a jitter, you can simulate a jitter in the delay (it will be normally distributed by a standard deviation of the set jitter).<br />\
						TODO: explain distribution\
						Loss ratio, duplication ratio and corruption ratio should also be self-explaining.</p>',
			skip_button: "Continue"
			},
			{
			trigger:function(obj) {
				
				mask = {
						component: "element",
						operation: "attribute-dialog",
						object: {
							data: {
								type: "openvz_interface"
							}
						}
					};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">\
						Close this Configure Dialog and open the Configure Dialog for the network interface on your OpenVZ device.</p>'
			},
			{
			trigger:function(obj) {
				
				mask = {
					action: "start",
					component: "element",
					operation: "action",
					phase: "begin"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">\
						Make sure DHCP is enabled. The close this dialog and start your topology.'
			},
			{
			trigger:function(obj) {
				
				mask = {
					component: "element",
					operation: "console-dialog"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialExplanation">\
						While your topology is being started, let me explain what happens:<br />\
						All devices connected to a switch connected to to the internet will have a direct connection to the internet (no NAT router or similar). TODO: Is this correct?<br />\
						For this to work, the device must use DHCP. Instead of setting this in the editor, you could also have run "dhclient eth0" on your device.</p>\
					<p class="tutorialCommand>\
						When the topology is running, open a console connection to the device.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						<i><small>This tutorial can\'t read the console\'s I/O, so just follow the following instructions.</small></i></p>\
					<p class="tutorialExplanation">\
						You should be able to ping any server on the internet. Please start a continuous ping to any server.</p>\
					<p class="tutorialExplanation">\
						The delay you are currently seeing is the delay between your device\'s host system and the server you are pinging.</p>\
					<p class="tutorialExplanation">\
						Open the connection\'s configure dialogue again, and set the delay of one direction to 100ms, and Apply the changes.<br />\
						You will notice that this delay will be added to your previous delay.<br />\
						You will also notice a change in the connection\'s appearance: A dashed line means that link emulation is taking place (except for bandwidth).</p>\
					<p class="tutorialExplanation">\
						Now, set a jitter of 50ms on the same direction. You will notice a jitter in the delay.</p>',
			skip_button:	"Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						You can reset the delay to 0ms now.</p>\
					<p class="tutorialExplanation">\
						When playing around with loss ratio, corruption ratio, and/or duplication ratio, you will notice lost, corrupted and duplicated packets in your ping history, where the ratio is the probability of corruption for each packet when travelling in the corresponding direction.<br />\
					<p class="tutorialExplanation">\
						Please reset delay and ratios to 0, and stop the pinging.</p>',
			skip_button:	"Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						For the next step, you need a URL to a large file (> ~50MB) or a continuous stream. The faster the respective server, the better; it should be available at >3 MByte/s</p>\
					<p class="tutorialExplanation">\
						The default bandwidth is set to 10Mbit/s. You will see this when you download the file (you don\'t need to complete the download; just start it and cancel when you have seen the download speed.</p>\
					<p class="tutorialExplanation">\
						You can now change the bandwidth (from switch to device) to be bigger or smaller, and see that these changes affect the download (even while it is running).<br />\
						You will also notice a change in the connection\'s thickness. This represents the bandwidth.</p>',
			skip_button:	"Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						Now, let\'s take a look at packet capturing.<br />\
						Enable packet capturing (mode: "for download", filter expressionÖ "") in the connection\'s settings, and then let the device load a webpage.</p>\
					<p class="tutorialExplanation">\
						Using the connection\'s right-click menu, you can now download the capture, or directly view it in cloudshark.<br />\
						The downloaded file can be viewed by any application which supports pcap viewing.</p>\
					<p class="tutorialExplanation">\
						If you instead prefer life-viewing using wireshark, set the capture mode to "via network". Then, a different item will appear in the right-click menu ("live capture info"), providing all info you need.</p>\
					<p class="tutorialExplanation">\
						The filter expression is the same you would use with tcpdump. (See the tdpdump manpage for more information)</p>',
			skip_button:	"Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						A last hint: In the "Options" tab, you can find the option "colorify segments".<br />\
						By using this options, you can colorify segments of a more complex topology:<br />\
						<img src="/img/tutorial_connections_colorify.png" /></p>',
			skip_button:	"Continue"
			},
			
			{
			text:	'<p class="tutorialExplanation">\
						That was it for this tutorial!</p>'
			}
];
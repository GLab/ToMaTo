[
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Link Emulation tutorial!<br />\
						You will learn how to use ToMaTo\'s link emulation feature.</p>',
			skip_button: 'Start tutorial'
			},
			{
			text:	'<p class="tutorialExplanation">\
						Let\'s take a closer look at a connection.</p>\
					<p class="tutorialExplanation">\
						Every connection consits of two network interfaces and the connection itself.<br />\
						An interface is represented by a grey circle at a device. Here you can configure the device\'s network preferences (e.g., ip address).<br />\
						The connection is represented by a blue square at its center. Here, you can configure the link (e.g., bandwidth, loss rate, etc).</p>\
					<p class="tutorialExplanation">\
						The options available to a connection depend on the connected devices. The same is true for interfaces.</p>',
			skip_button: 'Continue'
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
			text:	'<p class="tutorialExplanation">\
						You see a topology where an OpenVZ device is connected to a switch, and the switch is connected to the internet.<br />\
						Link emulation does not work when the connection is directly at an external network. Therefore, we need a switch in order to use link emulation.\
					<p class="tutorialExplanation">\
						All devices connected to a switch which is connected to to the internet will have a direct connection to the internet (no NAT router or similar).<br />\
						For this to work, the device must use DHCP. Instead of setting this in the editor, you could also have run "dhclient eth0" on your device.</p>\
					<p class="tutorialCommand">\
						Please start your topology. Changes to link emulation settings can be done while the topology is running.',
			help_page: 'NetworkTypes'
			},
			{
			trigger:function(obj) { 
				mask = {
					component: "connection",
					operation: "attribute-dialog",
					object: {
						elements: { 
							0: {
								parent: {
									data: {
										type: "tinc_endpoint",
									}
								}
							}
						},
						elements: { 
							1: {
								parent: {
									data: {
										type: "openvz",
									}
								}	
							}
						},
					},


							
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">\
						Open the Configure Dialog of the Device-Switch connection.</p>\
					<p class="tutorialExplanation">\
						To open the Configure Dialog, Right-click on the connection (i.e., the blue square), and select "Configure".</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						You might might need a small overview:</p>\
					<p class="tutorialExplanation">\
						The attributes are devided into two subjects: link emulation and packet capturing.<br />\
						In this tutorial, we will ignore the packet capturing part, and only look at link emulation.\
					<p class="tutorialExplanation">\
						Values are devided into two columns, one for each direction.<br />\
						Every value only affects packets being sent in that particular direction.<br />\
						The best way to determine the direction of the column is to look at the small graphic. The line has the same orientation as the link has in the editor, and the red arrow is the direction.</p>\
					<p class="tutorialExplanation">\
						Bandwidth and delay should be self-explaining. By setting a jitter, you can simulate a jitter in the delay. You can select how the random jitter is distributed.<br />\
						Loss ratio, duplication ratio and corruption ratio should also be self-explaining.</p>',
			skip_button: "Continue"
			},
			{
			trigger:function(obj) {
				
				mask = {
					component: "element",
					operation: "console-dialog"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand>\
						When the topology is running, open a VNC connection to the device.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
						<i><small>This tutorial can\'t read the console\'s I/O, so just follow these instructions.</small></i></p>\
					<p class="tutorialExplanation">\
						You should be able to ping any server on the internet. Please start a continuous ping to any server.</p>\
					<p class="tutorialExplanation">\
						The delay you are currently seeing is the delay between your device\'s host system and the server you are pinging.</p>\
					<p class="tutorialExplanation">\
						Open the connection\'s configure dialogue again, and set the delay of one direction to 100ms, and Apply the changes.<br />\
						You will notice that this delay will be added to your previous delay.<br />\
						You will also notice a change in the connection\'s appearance: A dashed line means that link emulation (except for bandwidth) is taking place.</p>\
					<p class="tutorialExplanation">\
						Now, set a jitter of 50ms on the same direction. You will notice a jitter in the delay.</p>',
			skip_button:	"Continue",
			help_page: 'linkemulation'
			},
			{
			text:	'<p class="tutorialExplanation">\
						You can reset the delay to 0ms now.</p>\
					<p class="tutorialExplanation">\
						When playing around with loss ratio, corruption ratio, and/or duplication ratio, you will notice lost, corrupted and duplicated packets in your ping history, where the ratio is the probability of corruption for each packet when travelling in the respective direction.<br />\
					<p class="tutorialExplanation">\
						Please reset delay and ratios to 0, and stop the pinging.</p>',
			skip_button:	"Continue",
			help_page: 'linkemulation'
			},
			{
			text:	'<p class="tutorialExplanation">\
						For the next step, you need a URL to a large file (> ~50MB) or a continuous stream. The faster the respective server, the better; it should be available at >3 MByte/s</p>\
					<p class="tutorialExplanation">\
						The default bandwidth is set to 10Mbit/s. You will see this when you download the file (you don\'t need to complete the download; just start it and cancel when you have seen the download speed.</p>\
					<p class="tutorialExplanation">\
						You can now change the bandwidth (from switch to device) to be bigger or smaller, and see that these changes affect the download (even while it is running).<br />\
						You will also notice a change in the connection\'s thickness. This represents the bandwidth.</p>',
			skip_button:	"Continue",
		help_page: 'linkemulation'
			},
			{
			text:	'<p class="tutorialExplanation">\
						That was it for this tutorial.</p>'
			}
]

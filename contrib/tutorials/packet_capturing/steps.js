[
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Packet Capturing tutorial!<br />\
						In this tutorial, you will learn how to capture traffic between ToMaTo devices.</p>',
			skip_button: 'Start tutorial'
			},
			{
			trigger:function(obj) {
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				var match = compareToMask(obj, {
					action: "start",
					component: "element",
					operation: "action",
					phase: "end"
				});
				if (match) data.tmp++;
				console.log("tutorial_data.tmp: "+data.tmp);				
				if (data.tmp >= 3) {
					data.tmp = 0;
					return true;
				}
				return false;

			  },
			text:	'<p class="tutorialExplanation">\
						All devices connected to a switch which is connected to to the internet will have a direct connection to the internet (no NAT router or similar).<br />\
						For this to work, the device must use DHCP. Instead of setting this in the editor, you could also have run "dhclient eth0" on your device.</p>\
					<p class="tutorialCommand">\
						Please start your topology.'
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
				
				mask = {
					component: "element",
					operation: "console-dialog"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialCommand">\
						When the topology is running, open a VNC connection to the device.</p>'
			},
			{
			trigger:function(obj) { 


				mask = { 
					component: "connection",
					operation: "attribute-dialog",
					object: {
						elements: {
							0: {
								data: {
									type: "tinc_endpoint"
								}
							},					
							1: {
								data: {
									type: "openvz_interface"
								}
							}
						}	
					}				
				};
				console.log(mask);
				if(compareToMask(obj,mask)) {
					return true;
				}
				mask = { 
					component: "connection",
					operation: "attribute-dialog",
					object: {
						elements: {
							1: {
								data: {
									type: "tinc_endpoint"
								}
							},					
							0: {
								data: {
									type: "openvz_interface"
								}
							}
						}	
					}			
				};
				if(compareToMask(obj,mask)) {
					return true;
				}

				return false;
			  },
			text:	'<p class="tutorialCommand">\
						Now open the Configure Dialog of the Device-Switch connection.</p>\
					<p class="tutorialExplanation">\
						To open the Configure Dialog, Right-click on the connection (i.e., the blue square), and select "Configure".</p>'
			},
			{
			trigger: function(obj) {
				mask = { 	operation: "modify",
						phase: "end",
						component: "connection",
						attrs: {
							capturing: true,
							capture_mode: "file",
						}
					};
				return compareToMask(obj,mask);
			},
			text:	'<p class="tutorialExplanation">\
						In this tutorial, we will only use the packet capturing part of the configuration window.</p>\
						<p class="tutorialCommand">Enable packet capturing (mode: "for download", filter expression "") in the connection\'s settings.</p>\
			',
			skip_button:	"Continue",
			help_page: 'packetcapturing'
			},
			{
			text: '<p class="tutorialCommand">Now let the device load a webpage. You can do this by typing <pre>wget http://tomato-lab.org/</pre></p>',
			skip_button:	"Continue"
			},
			{
			trigger: function(obj) {
				mask = {	operation: "action",
						phase: "end",
						action: "download_grant"
				};
				return compareToMask(obj,mask);
			},
			text:	'<p class="tutorialExplanation">\
						Using the connection\'s right-click menu, you can now download the capture, or directly view it in cloudshark.<br />\
						The downloaded file can be viewed by any application which supports pcap viewing, like Wireshark.</p>\
<p class="tutorialCommand">Please download the captur using the connection\'s right-click menu.</p>',
			skip_button:	"Continue",
			help_page: 'packetcapturing'
			},
			{
			trigger: function(obj) {
				mask = { 	operation: "action",
						phase: "end",
						component: "connection",
						action: "download_grant"
					};
				return compareToMask(obj,mask);
			},
			text:	'<p class="tutorialCommand">\
					Now use the right-click menu to View the Capture in CloudShark.\
					</p>',
			skip_button:	"Continue",
			help_page: 'packetcapturing'
			},
			{
			trigger: function(obj) {
				mask = { 	operation: "modify",
						phase: "end",
						component: "connection",
						attrs: {
							capture_mode: "net",
						}
					};
				return compareToMask(obj,mask);
			},
			text:	'<p class="tutorialExplanation">\
						If you instead prefer life-viewing using wireshark, set the capture mode to "via network". Then, a different item will appear in the right-click menu ("live capture info"), providing all info you need.</p>\
				<p class="tutorialExplanation">\
						The filter expression is the same you would use with tcpdump. (See <a href="http://www.tcpdump.org/manpages/pcap-filter.7.html" target="_blank" style="color: blue;">the tcpdump manpage</a> for more information)</p>',
			skip_button:	"Continue",
			help_page: 'packetcapturing'
			},
			{
			text:	'<p class="tutorialExplanation">\
						That was it for this tutorial!</p>'
			}
]

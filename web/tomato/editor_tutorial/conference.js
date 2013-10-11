var editor_tutorial = [

		/*
		 * tutorial data
		 * 
		 * Structure: name: [{trigger, text, help_page, skip_button}]
		 * name: name two find a tutorial, must be the same as in the tutorial list
		 * per step:
		 * 	trigger: takes a trigger object (handed over by every function that may be a tutorial trigger at one certain time)
		 * 		decides if this trigger object matches current step (shall the tut continue now - next step?)
		 * 		if not set, there will be no automatical way to continue.
		 * 	text: the text shown on screen (HTML formatting possible; CSS: style/editor.css)
		 *  help_page: if set, a ?-icon will appear in the tutorial window, directing to the url '/help/help_page'
		 *  skip_button: if set, the skip button will have this caption.
		 *
		 * be careful: tutorials with only 1 step might be buggy.
		 *
		 */
		
		     	
					{
					text:	'<p class="tutorialExplanation">\
								Welcome to the ToMaTo Tutorial at the GEC18 Conference!<br />\
								This guide will show you the main features of ToMaTo.</p>\
							<p class="tutorialCommand">\
								If you see bold commands, the tutorial will continue automatically after you followed these commands.</p>\
							<p class="tutorialExplanation">\
								Otherwise, you will have to click the Continue Button in this window. Due to network latency, the tutorial may need a second to react to your input.',
					skip_button: 'Start tutorial'
					},
					{
					trigger:function(obj) { 
					
						mask = {
							attrs: {
								state: "created",
								type: "openvz"
							},
							component: "element",
							operation: "create",
							phase: "end"
						};
						return compareToMask(obj,mask);
					
					  },
					text:	'<p class = "tutorialCommand">\
								To add a first device to your topology, click on OpenVZ (blue screen) \
								in \'Common elements\' in the menu, and then click somewhere in the workspace.</p>'
					},
					{
					trigger:function(obj) {
						
						mask = {
							attrs: {
								attrs: {
									mode: "switch"
								},
								type: "tinc_vpn"
							},
							component: "element",
							operation: "create",
							phase: "end"
						};
						return compareToMask(obj,mask);
						
					  },
					text:	'<p class="tutorialExplanation">\
								You will need more devices to get a real topology. This time, let\'s create a switch.</p>\
							<p class="tutorialCommand">\
								Click on the Switch button in Common elements in the menu above, and the place it in the editor by\
								clicking somewhere into the white.</p>'
					},
					{
					trigger:function(obj) {
						
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
					text:	'<p class="tutorialExplanation">\
								By now, the two elements don\'t have any network connection.</p>\
							<p class="tutorialCommand">\
								To connect them, right-Click on one of them, select Connect, and then left-click on the other one.</p>'
					},
					{
					text:	'<p class="tutorialExplanation">\
								Please expand your topology like this:\
								<img src="/editor_tutorial/conference.png"/></p>\
							<p class="tutorialExplanation">\
								Click on "Continue" when you are done.</p>',
					skip_button:"Continue"
					},
					{
					trigger:function(obj) {
						mask = {
							component: "element",
							object: {
								parent: {
									component_type: "element"
								}
							},
							operation: "attribute-dialog"
						};
						return compareToMask(obj,mask);
					  },
					text:	'<p class="tutorialExplanation">\
								Network interfaces are represented as grey circles.</p>\
							<p class="tutorialCommand">\
								Open the network interface configuration of the openvz device by right-clicking on its network interface, configure</p>'
					},
					{
					text:	'<p class="tutorialCommand">\
								Here you could set the IP address. We don\'t need this in this tutorial, so just close the configuration window.</p>',
					skip_button: "Continue"
					},
					{
					trigger:function(obj) {
						mask = {
							component: "element",
							operation: "attribute-dialog",
						};
						return compareToMask(obj,mask);
					  },
					text:	'<p class="tutorialExplanation">\
								Now, let\'s take a look at the device\'s configuration.</p>\
							<p class="tutorialCommand">\
								Open the device configuration of the openvz device by right-clicking on it, configure</p>'
					},
					{
					text:	'<p class="tutorialExplanation">\
								You can specify some parameters for your device. E.g., you can select an operating system from the template list.</p>\
							<p class="tutorialExplanation">\
								Click the help button if you want to know more.</p>',
					skip_button: "Continue"
					},
					{
					trigger:function(obj) {
						
						mask = {
							action: "prepare",
							component: "element",
							operation: "action",
							phase: "begin"
						};
						return compareToMask(obj,mask);
						
					  },
					text:	'<p class="tutorialExplanation">\
								Let\'s try out our new topology.</p>\
							<p class="tutorialCommand">\
								Click on \'Prepare\' under \'Topology control\'.</p>'
					},
					{
					text:	'<p class="tutorialExplanation">\
								The system is now configuring the devices.</p>\
							<p class="tutorialExplanation">\
								By preparing a topology, disk images will be generated from the selected templates,\
								and devices and connections will be created on the servers.</p>\
							<p class="tutorialExplanation">\
								Your topology is ready to run when you see the prepared (<img src="/img/prepared.png" />) symbol on every device.\
								Please wait for this, and click "Continue" when it\'s finished.</p>',
					skip_button: 'Continue',
					help_page: 'prepare'
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
								Currently, the devices are turned off.</p>\
							<p class="tutorialCommand">\
								Click on \'Start\' under \'Topology control\'. This will start the simulation of this topology.</p>'
					},
					{
					text: '<p class="tutorialExplanation">\
								You have started the topology. This means that all virtual machines are running now. You can see this by the running (<img src="/img/started.png" />) icon on the devices.</p>\
							<p class="tutorialExplanation">\
								Note also that you did not connect the devices to the internet yet.\
								You will see that there is no internet connection available on the devices.</p>',
					skip_button: 'Continue',
					help_page: 'run'
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
								To access the devices\' command line, right-click the device, Console, and select your preferred way to establish a VNC connection.\
								if you are unsure, choose NoVNC.</p>\
							<p class="tutorialCommand">\
								Please open a console for one of your OpenVZ devices.'
					},
					{
						text: "TODO: playing around with the program"
					}
		];
		


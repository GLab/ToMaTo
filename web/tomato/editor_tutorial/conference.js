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
								state: "created",
								type: "kvmqm"
							},
							component: "element",
							operation: "create",
							phase: "end"
						};
						return compareToMask(obj,mask);
						
					  },
					text:	'<p class="tutorialExplanation">\
								You will need more devices to get a whole topology. This time, let\'s create a KVM device.</p>\
							<p class="tutorialCommand">\
								Click KVM (green screen) in Common elements in the menu above, and the place it in the editor by\
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
								By now, the two devices don\'t have any network connection.</p>\
							<p class="tutorialCommand">\
								To connect them, right-Click on one of them, select Connect, and then left-click on the other one.</p>'
					},
					{
						text: "TODO: show the config menu, configure ip addresses"
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
					text:	'<p class="tutorialCommand">\
								To access the devices via command line, right-click the device, Console, NoVNC</p>\
							<p class="tutorialExplanation">\
								You can also use one of the other options, but then you\'ll need to press the \'Skip\' button to continue this tutorial.</p>'
					},
					{
					text:	'<p class="tutorialExplanation">\
								You can now play around with these two devices.</p>\
							<p class="tutorialExplanation">\
								If you are done, you can disconnect all shells and continue the tutorial.</p>',
					skip_button: 'Continue'
					},
					{
					trigger:function(obj) {
						
						mask = {
							action: "stop",
							component: "element",
							operation: "action",
							phase: "begin"
						};
						return compareToMask(obj,mask);
						
					  },
					text:	'<p class="tutorialCommand">\
								To stop the devices, press the \'Stop\' button in the top menu.</p>'
					},
					{
					text: '<p class="tutorialExplanation">\
								The devices are stopped when you see the prepared (<img src="/img/prepared.png" />) icon again.</p>\
							<p class="tutorialExplanation">\
								Devices will not be stopped by closing the window etc, but only when you stop them (although there might be other cases where a stop may be forced by the system or administrators).</p>',
					skip_button: 'Continue',
					help_page: 'prepare'
					},
					{
					trigger:function(obj) {
						
						mask = {
							action: "destroy",
							component: "element",
							operation: "action",
							phase: "begin"
						};
						return compareToMask(obj,mask);
						
					  },
					text:	'<p class="tutorialCommand">\
								To destroy the devices, click the \'destroy\' button.</p>'
					},
					{
					text: '<p class="tutorialExplanation">\
								You have now destroyed the devices and connections. This means, you have undone the preparation.</p>\
							<p class="tutorialExplanation">\
								You can also start, stop, prepare and destroy individual devices in their right-click menu.</p>',
					skip_button: 'Continue',
					help_page: 'prepare'
					},
					{
					trigger:function(obj) {
						
						mask = {
							component: "connection",
							operation: "remove",
							phase: "end"
						};
						return compareToMask(obj,mask);
						
					  },
					text:	'<p class="tutorialExplanation">\
								To finish the tutorial, let\'s clean up.</p>\
							<p class="tutorialCommand">\
								To delete the connection, right-click the connection (the square on the line) and select \'delete\'.</p>'
					},
					{
					trigger:function(obj) {
						
						mask_openvz = {
							object: { data: {
								type: "openvz"
							}},
							component: "element",
							operation: "remove",
							phase: "end"
						};
						
						mask_kvmqm = {
							object: { data: {
								type: "kvmqm"
							}},
							component: "element",
							operation: "remove",
							phase: "end"
						};
						
						return compareToMask(obj,mask_openvz) || compareToMask(obj,mask_kvmqm);
						
					  },
					text:	'<p class="tutorialExplanation">\
								To delete devices or connections, you can also use the \'delete\' mode from the \'Modes\' group in the menu.</p>\
							<p class="tutorialExplanation">\
								When you delete a device, you also delete all its connections.</p>\
							<p class="tutorialCommand">\
								Now, delete both devices.</p>'
					},
					{
					trigger:function(obj) {
						
						mask_openvz = {
							object: { data: {
								type: "openvz"
							}},
							component: "element",
							operation: "remove",
							phase: "end"
						};
						
						mask_kvmqm = {
							object: { data: {
								type: "kvmqm"
							}},
							component: "element",
							operation: "remove",
							phase: "end"
						};
						
						return compareToMask(obj,mask_openvz) || compareToMask(obj,mask_kvmqm);
						
					  },
					text:	'<p class="tutorialCommand">\
								Delete the other device.</p>'
					},
					{
					text:	'<p class="tutorialExplanation">\
								Congratulations, you have successfully completed the basic tutorial.</p>\
							<p class="tutorialExplanation">\
								To get the most out of this tool, we recommend you to walk through the additional tutorials. You can find them by clicking the "Tutorials" link in the topology list.</p>\
							<p class="tutorialExplanation">\
								You can find a button to delete this topology in the "Topology" tab.'
					}
		];
		


[

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
		 *  help_page: if set, a ?-icon will appear in the tutorial window, directing to the given url under the backend's help url
		 *  skip_button: if set, the skip button will have this caption.
		 *
		 * be careful: tutorials with only 1 step might be buggy.
		 *
		 */
		
		     	
					{
					text:	'<p class="tutorialExplanation">\
								Welcome to ToMaTo!<br />\
								This guide will tell you the basics of how to use this editor.<br />\
								If you already know how to use this tool, you can close this window.</p>\
							<p class="tutorialCommand">\
								If you see bold commands, the tutorial will continue automatically after you followed these commands.</p>\
							<p class="tutorialExplanation">\
								Otherwise, you will have to click the Continue Button in this window. Due to network latency, the tutorial may need a second to react to your input.',
					skip_button: 'Start tutorial'
					},
					{
					text:	'<p class="tutorialExplanation">\
								First of all, let\'s start with an overview over the user interface.</p>\
							<p class="tutorialExplanation">\
								The Topology Editor consists of two major parts: The menu at the top, and the workspace which is currently empty.</p>\
							<p class="tutorialExplanation">\
								In the menu, you will find all the tools you need to model and control your topologies.</p>\
							<p class="tutorialExplanation">\
								In the workspace, you will model the topology.</p>',
					skip_button: 'Continue',
					help_page: 'TopologyDesign'
					},
					{
					text: '<p class="tutorialExplanation">\
								Let\'s take a closer look at the menu:</p>\
							<p class="tutorialExplanation">\
								It is devided into tabs (Home, Devices, ...). Every tab is devided into multiple Groups (Modes, Topology control, ...), each of which consists of multiple buttons.</p>\
							<p class="tutorialExplanation">\
								Of special importance is the "Modes" group in the "Home" tab: It lets you choose between three modes which define what a left-click in the workspace does when you\'re not using any other features. Especially the "Delete" mode may cause unwanted, irreversible changes to your topology.</p>\
							<p class="tutorialExplanation">\
								The "Home" tab provides you the most important features.</p>',
					skip_button: 'Continue'
					},
					{
					text: '<p class="tutorialExplanation">\
								The "Devices" tab provides access to all device templates. See the "Devices" tutorial for more information.</p>\
							<p class="tutorialExplanation">\
								The "Network" tab provides access to virtual network hardware. See the "Network" tutorial for more information.</p>\
							<p class="tutorialExplanation">\
								Use the "Topology" tab to manage this topology.</p>\
							<p class="tutorialExplanation">\
								The "Options" tab provides several options, which are saved per-topology.</p>',
					skip_button: 'Continue'
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
					text:	'<p class="tutorialExplanation">\
								Congratulations! You have placed your first OpenVZ device.<br />\
								You can always identify OpenVZ devices by a blue screen.\
								OpenVZ devices are virtual machines which use their host\'s kernel to operate, but have their own virtual file system.\
								This makes them more efficient to run, but prohibits modifying the VM\'s kernel \
								which also means you can only run Linux systems in OpenVZ devices.</p>\
							<p class="tutorialExplanation">Did you notice the ? button, which just appeared in the top-right corner of this window?\
								This leads you to a help page which tells you more about what you just did (Don\'t worry, it opens in a new browser tab).</p>',
					help_page:'DeviceTypes',
					skip_button: 'Continue'
					},
					{
					trigger:function(obj) {
					  
						mask = {
							component: "element",
							operation: "modify",
							phase: "end"
						};
						mask2= {
						  attrs: {
							_pos: {x: 1,y: 1}
						  }
						}
						return compareToMask(obj,mask) && maskExists(obj,mask2);
						
					  },
					text:	'<p class="tutorialExplanation">\
								You can move your new device via drag-and-drop.</p>\
							<p class="tutorialCommand">\
								Try it now!</p>'
					},
					{
					text:	'<p class="tutorialExplanation">\
								You can disable moving elements or enable <i>snap-to-grid</i> in the options tab.</p>',
					help_page:'EditorSettings',
					skip_button: 'Continue'
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
					text:	'<p class="tutorialExplanation">\
								You just created a KVM device.\
								KVM devices can be identified by a green screen.\
								Contrary to OpenVZ, KVM devices run completely separated from their host systems.\
								This means that you can modify the kernel and/or use any operating system.</p>',
					skip_button:'continue'
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
					text:	'<p class="tutorialExplanation">\
								You have created a network connection between the two devices. The connection is shown as a line between them.</p>\
							<p class="tutorialExplanation">\
								To learn more about connections, take a look at the \'connections\' tutorial later.</p>',
					skip_button: 'Continue'
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
								Since you have a topology now, you can run it.</p>\
							<p class="tutorialExplanation">\
								To get started, the devices and connections must be created on the servers.\
								<i>Note: If you don\'t have the permissions to run topologies (yet), you can skip to the last step of this tutorial.</i></p>\
							<p class="tutorialCommand">\
								Click on \'Prepare\' under \'Topology control\'.</p>'
					},
					{
					text:	'<p class="tutorialExplanation">\
								The system is now configuring the devices.</p>\
							<p class="tutorialExplanation">\
								Your topology is ready to run when you see the prepared (<img src="/img/prepared.png" />) symbol on every device. Please wait for this, and click "Continue" when it\'s finished.</p>',
					skip_button: 'Continue',
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
								Now, you want to run it.</p>\
							<p class="tutorialCommand">\
								Click on \'Start\' under \'Topology control\'. This will start the simulation of this topology.</p>'
					},
					{
					text: '<p class="tutorialExplanation">\
								You have started the topology. This means that all virtual machines are running now. You can see this by finding a running (<img src="/img/started.png" />) icon on the devices.</p>\
							<p class="tutorialExplanation">\
								<i>Note:</i> If no or not all devices have been prepared when you start the topology, ToMaTo will automatically do this step for you. You can skip the prepare step without need to worry.</p>\
							<p class="tutorialExplanation">\
								Note also that you did not connect the devices to the internet yet (We\'ll do that in the \'connections\' tutorial).</p>',
					skip_button: 'Continue',
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
								Please open a console for one of your two devices.',
					help_page: 'TopologyInteraction'
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
						skip_button: 'Continue'
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
						skip_button: 'Continue'
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
		]

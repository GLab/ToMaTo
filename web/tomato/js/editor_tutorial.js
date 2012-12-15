/*
 * TODO tutorial:
 * 
 * implement tutorial window close button
 * 
 * finish basic tutorial
 * 
 * add links to help (either in-text or an optional help button)
 * 		assumes help has been created
 */

var editor_tutorial = {
        /*
         * part one: tutorial list: metadata for the tutorials
         * 
         * Structure for the tutorial list:
         * name: the key where to find the tutorial data. must be different from "tutorials"
         * title: Title of the tutorial for display
         * description: a short description for a tooltip or similar
         * icon: url to the menu icon
         */
		tutorials: [
		    //0: this is the one which will be loaded by default for new users
			{
				name: "basic",
				title: "Basic Usage",
				description: "This tutorial will tell you the very basics of how to use the editor and topologies.",
				icon: "img/user32.png"
			},
			
		    // other tutorials; can be loaded through menu
			{
				name: "devices",
				title: "Devices",
				description: "This tutorial will tell you the very basics of how to use the editor and topologies.",
				icon: "img/openvz32.png"
			},
			{
				name: "connections",
				title: "Connections",
				description: "This tutorial will tell you the very basics of how to use the editor and topologies.",
				icon: "img/connect32.png"
			}
			
		],
		
         

		/*
		 * part two: tutorial data
		 * 
		 * Structure: name: [{trigger, text}]
		 * name: name two find a tutorial, must be the same as in the tutorial list
		 * per step:
		 * 	trigger: takes a trigger object (handed over by every function that may be a tutorial trigger at one certain time)
		 * 		decides if this trigger object matches current step (shall the tut continue now - next step?)
		 * 	text: the text shown on screen (HTML formatting possible; CSS: style/editor.css)
		 *
		 * be careful: tutorials with only 1 step might be buggy.
		 *
		 */
		
		basic: [     	
					//0
					{
					trigger:function(obj) { return true; },
					text:	'<p class="tutorialExplanation">\
								Welcome to ToMaTo! You have just created a new Topology.<br />\
								This guide will tell you the basics of how to use this editor.<br />\
								If you already know how to use this tool, you can close this window.</p>\
							<p class = "tutorialCommand">\
								To add a first device to your topology, first click on OpenVZ (blue screen) \
								in Common elements in the menu above, and then click somewhere in the white field.</p>'
					},
					
					//1
					{
					trigger:function(obj) { return true; },
					text:	'<p class="tutorialExplanation">\
								Congratulations! You have placed your first OpenVZ device.<br />\
								You can always identify OpenVZ devices by a blue screen.\
								OpenVZ devices are virtual machines which use their host\'s kernel to operate, but have their own virtual file system.\
								This makes them more efficient to run, but disallows modifying the kernel, but,\
								however, this also means, you can only run Linux systems in OpenVZ devices.</p>\
							<p class="tutorialExplanation">Did you notice the ? button, which just appeared in the top-right corner of this window?\
								This leads you to a help page which tells you more about what you just did (Don\'t worry, it opens in a new browser tab).</p>\
							<p class="tutorialCommand">\
								You can move your new device via drag-and-drop. Try it now!</p>',
					help_page:'kvm'
					},
					
					//2
					{
					trigger:function(obj) { return true; },
					text:	'<p class="tutorialExplanation">\
								You can disable moving elements in the options.</p>\
							<p class="tutorialExplanation">\
								You will need more devices to get a whole topology. This time, let\s create a KVM device.</p>\
							<p class="tutorialCommand">\
								Click KVM in Common elements in the menu above, and the place it in the editor by\
								clicking somewhere into the white.</p>'
					},
					
					//3
					{
					trigger:function(obj) { return true; },
					text:	"You just created a KVM device.\n\
							KVM devices can be identified by a green screen.\n\
							Contary to OpenVZ, KVM devices run completely separate from their host systems.\n\
							This means that you can modify the kernel and/or use any system which supports the host's processor architecture.\n \n\
							By now, the two devices don't have any network connection.\n\
							To connect them, right-Click on one of them, select 'Connect', and then left-click on the other one.",
					help_page:'openvz'
					},
					
					//4
					{
					trigger:function(obj) { return false; },
					text:	"You have connected the two devices."
					}
		],
		
		devices: [
					{
					trigger:function(obj) { return false; },
					text:	"This tutorial has yet to be created."
					}
		],
		
		connections: [
					{
					trigger:function(obj) { return false; },
					text:	"This tutorial has yet to be created."
					}
		]
}

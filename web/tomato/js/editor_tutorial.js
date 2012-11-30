/*
 * TODO tutorial:
 * 
 * split text into explanation and directive
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
         */
		tutorials: [
		    //0: this is the one which will be loaded by default
			{
				name: "basic",
				title: "Basic Usage",
				description: "This tutorial will tell you the very basics of how to use the editor and topologies."
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
		 * 	text: the text shown on screen (HTML formatting possible)
		 */
		
		basic: [     	
					//0
					{
					trigger:function(obj) { return true; },
					text:	"Welcome to ToMaTo!. You have just created a new Topology.\n\
							This guide will tell you the basics of how to use this editor.\n\
							If you already know how to use this tool, you can disable this tutorial at any point by disabling 'Beginner mode' in 'Options'.\n \n\
							To add a first device to your topology, first click on 'OpenVZ' (blue screen) in 'Common elements' in the menu above, and then\n\
							click somewhere in the white field."
					},
					
					//1
					{
					trigger:function(obj) { return true; },
					text:	"Congratulations! You have placed your first OpenVZ device.\n\
							You can always identify OpenVZ devices by a blue screen.\n\
							OpenVZ devices are virtual machines which use their host's kernel to operate, but have their own virtual file system.\n\
							This makes them more efficient to run, but disallows modifying the kernel.\n\
							This also means, you can only run Linux systems in OpenVZ devices.\n \n\
							You can move your new device via drag-and-drop. Try it!"
					},
					
					//2
					{
					trigger:function(obj) { return true; },
					text:	"You will need more devices to get a whole topology. This time, let's create a KVM device.\n \n\
							Click 'KVM' in 'Common elements' in the menu above, and the place it in the editor by clicking somewhere into the white."
					},
					
					//3
					{
					trigger:function(obj) { return true; },
					text:	"You just created a KVM device.\n\
							KVM devices can be identified by a green screen.\n\
							Contary to OpenVZ, KVM devices run completely separate from their host systems.\n\
							This means that you can modify the kernel and/or use any system which supports the host's processor architecture.\n \n\
							By now, the two devices don't have any network connection.\n\
							To connect them, right-Click on one of them, select 'Connect', and then left-click on the other one."
					},
					
					//4
					{
					trigger:function(obj) { return true; },
					text:	"You have connected the two devices."
					}
		]
}

var tutorial_data = {
  templates: {
    node: "chat_node",
    monitor: "chat_monitor",
    sender: "chat_sender"
  },
  delay: 2000
};

var editor_tutorial = [
	{
		text: '<h2>ToMaTo Chat Tutorial</h2>\
<p class="tutorialExplanation">In this tutorial you will learn the basics of the Topology Management Tool in a simple scenario using a text-based chat client.</p>\
<p class="tutorialExplanation">Please read the full explanations of a step before working on it.</p>\
<h3>First part</h3>\
<p class="tutorialExplanation">In this part we will fill our topology with two virtual machines, connect them and test the chat client.</p>',
		skip_button: 'Start tutorial'
	},
	{
		text: '<p class="tutorialExplanation">As first step we add a virtual machine to the topology. This virtual machine will use OpenVZ technology since we only want to run a simple program on it.<br/>\
Click on the blue computer icon on the right of the menu and then click into the work space to position that element. You can later move it by dragging the icon in the work space.<br/>\
You can move this tutorial window if it covers your work space.</p>\
<br/><b>Task: Add an OpenVZ virtual machine to your topology</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "openvz"
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">For this chat tutorial we have a special template that contains the chat client. Currently your virtual machine has the default template, which is a plain debian installation. As your virtual machine is not yet started, we can still change its template.<br/>\
Right-click on the virtual machine icon in your work space and select <i>configure</i> to open the attribute window of this element.<br/>\
Change the template to <i>Chat Tutorial Node</i> and click on <i>Save</i> to apply the change.<br/>\
You can also change the name your virtual machine and its hostname if you want to.</p>\
<br/><b>Task: Change the template of the virtual machine to <i>Chat Tutorial Node</i></b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end",
				attrs: {
					template: tutorial_data.templates.node
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we need a chat partner, so we add another node to the topology. This time we give it the right template right from the start. To do this, open the <i>Devices</i> tab in the menu and select the <i>Chat Tutorial Node</i> from the menu.</p>\
<br/><b>Task: Add another virtual machine using the <i>Chat Tutorial Node</i> template</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "openvz",
					attrs: {
						template: tutorial_data.templates.node
					}
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">To be able to exchange messages between these VMs, we need to connect them. Right-click on one of the machines, select <i>Connect</i> and then click on the other node to establish a connection between the two topology elements.</p>\
<br/><b>Task: Create a connection between the two VMs</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Ok, now it is time to start the VMs. Right-click on one of the VMs and select <i>prepare</i>. This will create the VM on one of the testbed hosts but not start it yet. Afterwards you can start the VM by using the <i>start</i> command. The icons beside the element icon reflect the current state of the element.</p>\
<br/><b>Task: Start one of the VMs</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "action",
				component: "element",
				action: "start",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">For bigger topologies, this would be a lot of work. Therefore you can start, stop, prepare and destroy all of the topology elements at once using the buttons in the tag <i>Home</i> of the menu.<br/>\
These buttons are smart and know the states of the elements. If you select <i>start</i>, elements that are already running will not be touched and those that are not yet prepared will be prepared before they are started.</p>\
<br/><b>Task: Start the other VM</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "action",
				component: "element",
				action: "start",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Now both nodes are running and we can test the chat client. You can access the VMs using a VNC console. To open this console, right-click on the element and selct <i>Console</i>. There are different VNC clients available but the most compatible is <i>NoVNC</i>.</p>\
<b>Task: Open the consoles of both VMs</b>',
		trigger: function(event) {
			if (! tutorial_data.tmp) tutorial_data.tmp = 0;
			var match = compareToMask(event, {
				operation: "console-dialog",
				component: "element"
			});
			if (match) tutorial_data.tmp++;
			if (tutorial_data.tmp >= 2) {
				tutorial_data.tmp = 0;
				return true;
			}
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now you can test the chat client. Type <i>chat</i> into the consoles to start the software. This software will send every line that you type to all connected nodes using UDP broadcast. All received lines will be displayed together with a timestamp, a sequence number and the senders IP address.<br/>\
To quit the software type <i>ctrl-c (Control-C)</i>. You can close the consoles when you are finished.</p>\
<br/><b>Click on continue when you are done</b>',
		skip_button: 'Continue'
	},
	{
		text: '<h3>Second part</h3>\
<p class="tutorialExplanation">In this second part we will extend the topology and add two automated chat agents.<br/>\
These agents will use a different technology called Repy that basically just runs Python code that handles layer 2 traffic.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Before we add the chat agents, we first add a switch that we will use to connect all of our elements. Select the switch from the menu and position it in a central place.<br/>\
The switch is also a virtual element, it uses VPN technology to connect elements.</p>\
<br/><b>Task: Add a switch to the topology</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "tinc_vpn"
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">To be able to connect our two existing VMs to that switch, we first have to stop them.<br/>\
That is one advantage of using switches: Once your VM is connected to a switch, you just have to stop that switch to add other elements to it, your VM can stay online.</p>\
<br/><b>Task: Stop both existing VMs</b>',
		trigger: function(event) {
			if (! tutorial_data.tmp) tutorial_data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				component: "element",
				action: "stop",
				phase: "end"
			});
			if (match) tutorial_data.tmp++;
			if (tutorial_data.tmp >= 2) {
				tutorial_data.tmp = 0;
				return true;
			}
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we can change the connections. Remove the connection between the two VMs by clicking on the blue handle in the middle of the connection and select <i>Delete</i>.</p>\
<br/><b>Task: Delete the connection between the VMs</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "remove",
				component: "connection",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">You already know how to connect elements from the first part of the tutorial.</p>\
<br/><b>Task: Connect both VMs to the switch</b>',
		trigger: function(event) {
			if (! tutorial_data.tmp) tutorial_data.tmp = 0;
			var match = compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			});
			if (match) tutorial_data.tmp++;
			if (tutorial_data.tmp >= 2) {
				tutorial_data.tmp = 0;
				return true;
			}
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we can add the chat agents. First select the <i>Chat Tutorial Monitor</i> from the <i>Devices</i> tab of the menu and add it to the topology. The icon of this element will be orange as it uses the Repy technology.<br/>\
This chat agent is passive, it will just display all messages it receives.</p>\
<br/><b>Task: Add a <i>Chat Tutorial Monitor</i> to the topology</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "repy",
					attrs: {
						template: tutorial_data.templates.monitor
					}
				}
			}) || compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end",
				attrs: {
					template: tutorial_data.templates.monitor
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">As a second chat agent we will add the <i>Chat Tutorial Sender</i> to the topology.<br/>\
This chat agent will send a message every 3 seconds.</p>\
<br/><b>Task: Add a <i>Chat Tutorial Sender</i> to the topology</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "repy",
					attrs: {
						template: tutorial_data.templates.sender
					}
				}
			}) || compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end",
				attrs: {
					template: tutorial_data.templates.sender
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Do not forget to connect these agents to the switch.</p>\
<br/><b>Task: Connect both agents to the switch</b>',
		trigger: function(event) {
			if (! tutorial_data.tmp) tutorial_data.tmp = 0;
			var match = compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			});
			if (match) tutorial_data.tmp++;
			if (tutorial_data.tmp >= 2) {
				tutorial_data.tmp = 0;
				return true;
			}
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now you can start the whole topology again.</p>\
<br/><b>Task: Start the topology</b>',
		trigger: function(event) {
			if (! tutorial_data.tmp) tutorial_data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				component: "element",
				action: "start",
				phase: "end"
			});
			if (match) tutorial_data.tmp++;
			if (tutorial_data.tmp >= 5) {
				tutorial_data.tmp = 0;
				return true;
			}
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Start the chat clients again and after a few seconds you should see the periodic messages from the sender agent. If you open the VNC console of the monitor agent you should see all chat messages.<br/>\
Note that you can not type any text into the consoles of these agents as the Repy technology is not interactive.</p>\
<br/><b>Click on continue when you are done</b>',
		skip_button: 'Continue'
	},
	{
		text: '<h3>Third part</h3>\
<p class="tutorialExplanation">Now that we learned how to create and manage topologies we will have a look at some advanced functionality of ToMaTo. In this part we will change the link characteristics between the elements and have a look at the packets that travel over them.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now we will add a latency of 2 seconds to a link and check if we can see the difference. Open the attributes ofthe link of one OpenVZ VM as you learned in the the first part. Enable link emulation and add a latency of 2000 ms on one of the directions.</p>\
<br/><b>Task: Add 2 seconds delay to one link</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "connection",
				phase: "end",
				attrs: {
					delay_from: tutorial_data.delay
				}
			}) || compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end",
				attrs: {
					delay_to: tutorial_data.delay
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">You should see the delay when you send messages between your OpenVZ VMs. The delay should only exist in one direction.<br/>\
Now you can play around with the settings a little. Maybe add some jitter to the connection. If you apply packet duplication or packet loss you can use the sequence numbers to check this functionality.</p>\
<br/><b>Click continue when you want to continue</b>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now we will have a look at how the packets of our chat client look like. Open the attribute window of a connection again and activate packet capturing. Please keep the mode at <i>for download</i> and do not apply a filter.</p>\
<br/><b>Task: Enable packet capturing for one link</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "connection",
				phase: "end",
				attrs: {
					capturing: true
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Make sure that some chat messages go over that link and then we can have a look at them. To view them, we will use an online service called <i>Cloudshark</i>. Right click on the link and choose <i>View capture in Cloudshark</i>.</p>\
<br/><b>Task: Open the captured packets in Cloudshark</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "action",
				component: "connection",
				action: "download_grant",
				phase: "end"
			});
		}
	},
	{
 		text: '<p class="tutorialExplanation">Have a look at the packets and try to figure out how they are encoded and what the fields could mean.</p>\
<p class="tutorialExplanation">It might happen that your pop-up blocker prevents the Cloudshark window from opening. You should disable the blocker for ToMaTo.</p>\
<br/><b>Click on continue when you are done</b>',
		skip_button: 'Continue'
	},
	{
		text: '<h3>Fourth part</h3>\
<p class="tutorialExplanation">Ok, now you have seen some of the features of ToMaTo. The only important thing that is missing now is external connectivity.<br/>\
In this part we will open our topology to the Internet.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Select the Internet from the menu and add it to the topology. In the attribute window you can select the type of external network that you want but Internet is the default.<br/>\
This external network is an opening of your topology. Whatever is connected to this element is connected to that network, i.e. to the Internet in our case.</p>\
<br/><b>Task: Add an <i>Internet</i> external network to your topology</b>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "external_network"
				}
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we have to change the topology a litte:\
<ol>\
  <li>Stop the switch so you can change its connections.</li>\
  <li>Stop and disconnect the sender chat agent, you do not want to spam the Internet.</li>\
  <li>Connect the Internet to the switch.</li>\
  <li>Start everything again.</li>\
</ol>\
You know how to do this from the earlier tutorial parts.</p>\
<br/><b>Click on continue when you are finished</b>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">When your topology is connected to the Internet, you can reach the Internet from the connected VMs.<br/>\
Check that by typing the following into the console of one of the VMs: <pre><tt>ping www.google.com</tt></pre><br/>\
If you do not get a reply, you might need to obtain a network address first by running the following: <pre><tt>dhclient eth0</tt></pre><br/>\
If you see high latencies or lost packets, you might still have link emulation enabled.</br>\
You can use this connection to exchange files with your nodes and to use external services.</p><br/>\
<br/><b>Click on continue when you are done</b>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">If you want to, you can start a chat client on one of the VMs and maybe someone answers.</p>\
<br/><b>Click on continue when you are finished</b>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">To delete your VMs and free the resources, click the <i>Destroy</i> button in the top menu.</p>\
<br/><b>Task: Destroy the topology</b>',
		trigger: function(event) {
			if (! tutorial_data.tmp) tutorial_data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				component: "element",
				action: "destroy",
				phase: "end"
			});
			if (match) tutorial_data.tmp++;
			if (tutorial_data.tmp >= 5) {
				tutorial_data.tmp = 0;
				return true;
			}
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we are at the end of the tutorial, I hope you enjoyed it.</p>'
	}
];    


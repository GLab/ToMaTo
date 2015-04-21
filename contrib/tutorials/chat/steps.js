[
	{
		text: '<h2>ToMaTo Chat Tutorial</h2>\
<p class="tutorialExplanation">In this tutorial you will learn the basics of the Topology Management Tool in a simple scenario using a text-based chat client.</p>\
<p class="tutorialExplanation">Please read the full explanations of a step before working on it.</p>\
<h3>First part</h3>\
<p class="tutorialExplanation">In this part we will fill our topology with two virtual machines, connect them and test the chat client.</p>',
		skip_button: 'Start tutorial'
	},
	{
		text: '<p class="tutorialExplanation">For this tutorial you need 4 files. We will use them later to create our chat servers and show some aspects of ToMaTo.<br />\
			Please save them to your disk now.<br/>\
			<ul>\
			<li><a href="'+tutorial_base_url+'install_python.tar.gz" class="download" download="install_python.tar.gz">Python install package</a></li>\
			<li><a href="'+tutorial_base_url+'chat_client.tar.gz"  class="download" download="chat_client.tar.gz">Chat client software</a></li>\
			<li><a href="'+tutorial_base_url+'chat_monitor.repy"  class="download" download="chat_monitor.repy">Chat monitor script</a></li>\
			<li><a href="'+tutorial_base_url+'chat_sender.repy"  class="download" download="chat_sender.repy">Chat sender script</a></li>\
			</ul></p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">As first step we add two virtual machines to the topology. These virtual machines will use OpenVZ technology since we only want to run a simple program on it.<br/>\
			Click on the blue computer icon on the right of the menu and then click into the work space to position that element. You can later move it by dragging the icon in the work space.<br/>\
			You can move this tutorial window if it covers your work space.</p>\
			<p class="tutorialCommand">Add two OpenVZ devices to your topology</p>',
		trigger: function(event) {
			data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "openvz"
				},
				});
			if(match) data.tmp++;
			if (data.tmp >= 2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
			}
			setTutorialData(data);
			return false;
		},
		help_page: 'TopologyDesign'
	},
	{
		text: '<p class="tutorialExplanation">Currently your virtual machine has the default template, which is a plain debian installation. <br />\
			With a right-click on your virtual machine icon in your work space you can select <i>configure</i> to open the attribute window of this element.<br/>\
			As your virtual machine is not started yet you can change nearly every attribute of it, even the template. For this tutorial, we will use the default template, so please keep this setting.<br/>\
			You can also change the name of your devices and its hostname if you want to.</p>\
			<p class="tutorialCommand">Rename the devices to "alice" and "bob"</p>',
			trigger: function(event) {
				data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				if (compareToMask(event, {
					operation: "modify",
					component: "element",
					phase: "end"
				})) data.tmp++;
				if (data.tmp >= 2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
				}
				setTutorialData(data);
				return false;
			}
	},
	{
		text: '<p class="tutorialExplanation">To be able to exchange messages between these VMs, we need to connect them. Right-click on one of the machines, select <i>Connect</i> and then click on the other node to establish a connection between the two topology elements.</p>\
<p class="tutorialCommand">Create a connection between the two VMs</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Before we can install the chat client we have to prepare and start our virtual machines.<br/> Preparing will create the VM on one of the testbed hosts but not start it yet.<br /> We have two options to do this. The first option is to right-click our devices and select </i>Prepare</i><br />The other way to do this is to use the <i>Prepare</i>-Button in the menu.<br/></p>\
<p class="tutorialCommand">Prepare your virtual devices. This may take a few seconds.</p>',
		trigger: function(event) {
			data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				action: "prepare",
				component: "element",
				phase: "end",
			});
			if(match) data.tmp++;
			if (data.tmp >= 2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
			}
			setTutorialData(data);
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">After we prepared the VMs we have to start them. You can start the VM by using the <i>start</i> command. Just right-click on a device and select <i>Start</i>.<br /> The icons beside the element icon reflect the current state of the element.</p>\
<p class="tutorialCommand">Start one of the VMs</p>',
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
<p class="tutorialCommand">Start the other VM</p>',
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
		text: '<p class="tutorialExplanation">Now we will install python via executable archives. We will need it for the chat client. <br /> \
			This archive has a <i>auto_exec.sh</i> file in it.  <br /> \
			It will automaticly be executed after it is uploaded.<br /> \
			Right-click on the virtual machines and select <i>Executable archive &gt; Upload Archive</i>;</p>\
			<p>Download: <a href="'+tutorial_base_url+'install_python.tar.gz"  class="download" download="install_python.tar.gz">Python install package</a></p>\
			<p class="tutorialCommand">Upload the <i>install_python.tar.gz</i> archive to both VMs.</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				phase: "end", 
				action: "rextfv_upload_use",
				component: "element"
			});
			if(match) data.tmp++;
			if (data.tmp >= 2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
			}
			setTutorialData(data);
			return false;
		},
		help_page: 'ExecutableArchives'
	}, 
	{
		text: '<p class="tutorialExplanation">If you want to get information about the execution of your archive, just go to executable archive status window</p>\
<p class="tutorialCommand">Open the executable archive status page by right-clicking the virtual machine and selecting <i>Executable archive &gt; Status</i></p>',
		trigger: function(event) {
				return compareToMask(event, {
					operation: "rextfv-status",
					component: "element"
				});
		},
		help_page: 'ExecutableArchives'
	},
	{ 
		text: '<p class="tutorialCommand">Wait until the executable archive status page shows "Finish". Then click on "Continue".</p>',
		skip_button: 'Continue',
		help_page: 'ExecutableArchives'
	
	},
	{
		text: '<p class="tutorialExplanation">Now we will install the chat client via executable archives. <br /></p>\
		<p>Download: <a href="'+tutorial_base_url+'chat_client.tar.gz" class="download" download="chat_client.tar.gz">Chat client software</a></p>\
		<p class="tutorialCommand">Upload the <i>chat_client.tar.gz</i> archive to both VMs.</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
					operation: "action",
					phase: "end", 
					action: "rextfv_upload_use",
					component: "element"
				});
			if(match) data.tmp++;
			if (data.tmp >= 2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
			}
			setTutorialData(data);
			return false;
		},
		help_page: 'ExecutableArchives'
	}, 
	{
		text: '<p class="tutorialCommand">Again, open the executable archive status page by right-clicking the virtual machine and selecting <i>Executable archive &gt; Status</i> to get information about the status of your upload. </p>',
		trigger: function(event) {
				return compareToMask(event, {
					operation: "rextfv-status",
					component: "element"
				});
		},
		help_page: 'ExecutableArchives'
	},
	{ 
		text: '<p class="tutorialCommand">Wait until the executable archive status page shows "Finish". Then click on "Continue".</p>',
		skip_button: 'Continue',
	
	},
	{
		text: '<p class="tutorialExplanation">Now both nodes are running and we can test the chat client. You can access the VMs using a VNC console. To open this console, right-click on the element and selct <i>Console</i>. There are different VNC clients available but the most compatible is <i>NoVNC</i>.</p>\
<p class="tutorialCommand">Open the consoles of both VMs</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "console-dialog",
				component: "element"
			});
			if (match) data.tmp++;
			if (data.tmp >= 2) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		},
		help_page: 'TopologyInteraction'
	},
	{
		text: '<p class="tutorialExplanation">Now you can test the chat client. Type <i>chat</i> into the consoles to start the software. This software will send every line that you type to all connected nodes using UDP broadcast. All received lines will be displayed together with a timestamp, a sequence number and the senders IP address.<br/>\
To quit the software type <i>ctrl-c (Control-C)</i>. You can close the consoles when you are finished.</p>\
<p class="tutorialCommand">Click on continue when you are done</p>',
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
<p class="tutorialCommand">Add a switch to the topology</p>',
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
<p class="tutorialCommand">Stop both existing VMs</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				component: "element",
				action: "stop",
				phase: "end"
			});
			if (match) data.tmp++;
			if (data.tmp >= 2) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		},
		help_page: 'NetworkTypes'
	},
	{
		text: '<p class="tutorialExplanation">Now we can change the connections. Remove the connection between the two VMs by clicking on the blue handle in the middle of the connection and select <i>Delete</i>.</p>\
<p class="tutorialCommand">Delete the connection between the VMs</p>',
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
<p class="tutorialCommand">Connect both VMs to the switch</b>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			});
			if (match) data.tmp++;
			if (data.tmp >= 2) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we can add the chat agents. First select the <i>Repy Script</i> from the "upload own images" group at the <i>Devices</i> tab of the menu and add it to the topology. The icon of this element will be orange as it uses the Repy technology.<br/>\
You will later have to upload the Chat Tutorial Monitor Repy script from the beginning of the Tutorial.<br/>\
This chat agent is passive, it will just display all messages it receives.</p>\
<p>Download: <a href="'+tutorial_base_url+'chat_monitor.repy" class="download" download="chat_monitor.repy">Chat monitor script</a></p>\
<p class="tutorialCommand">Add a <i>Repy Script Device</i> to the topology and upload the script <i>chat_monitor.repy</i></p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				object: {
					data: {
						type: "repy",
					}
				}
			});
		},
		help_page: 'DeviceTypes'
	},
	{
		text: '<p class="tutorialCommand">Change the name of this repy device to "Chat Monitor"</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end",
			});
		}
	},
	{ 
		text: '<p class="tutorialCommand">Upload the script <a href="'+tutorial_base_url+'chat_monitor.repy" class="download" download="chat_monitor.repy"><i>chat_monitor.repy</i></a></p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "action",
				action: "upload_use",
				component: "element",
				phase: "end",
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">As a second chat agent we will add the <i>Chat Tutorial Sender</i> to the topology.<br/>\
This chat agent will send a message every 3 seconds.</p>\
<p>Download: <a href="'+tutorial_base_url+'chat_sender.repy" class="download" download="chat_sender.repy">Chat sender script</a></p>\
<p class="tutorialCommand">Add a second <i>Repy Script Device</i> to the topology and upload the file <i>chat_sender.repy</i></p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				object: {
					data: {
						type: "repy",
					}
				}
			});
		}
	},
	{
		text: '<p class="tutorialCommand">Change the name of this repy device to "Chat Sender"</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end",
			});
		}
	},
	{ 
		text: '<p class="tutorialCommand">Upload the script <a href="'+tutorial_base_url+'chat_sender.repy" class="download" download="chat_sender.repy"><i>chat_sender.repy</i></a></p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "action",
				action: "upload_use",
				component: "element",
				phase: "end",
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Do not forget to connect these agents to the switch.</p>\
<p class="tutorialCommand">Connect both agents to the switch</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			});
			if (match) data.tmp++;
			if (data.tmp >= 2) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now you can start the whole topology again.</p>\
<p class="tutorialCommand">Start the topology</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				component: "element",
				action: "start",
				phase: "end"
			});
			if (match) data.tmp++;
			if (data.tmp >= 5) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		},
		help_page: 'devices'
	},
	{
		text: '<p class="tutorialExplanation">When you open the device\'s consoles and start their chat clients again, you should see the periodic messages from the sender agent after a few seconds. If you open the VNC console of the monitor agent you should see all chat messages that have been sent since it has been started.<br/>\
Note that you can not type any text into the consoles of these agents as the Repy technology is not interactive.</p>\
<p class="tutorialCommand">Click on continue when you are done</p>',
		skip_button: 'Continue'
	},
	{
		text: '<h3>Third part</h3>\
<p class="tutorialExplanation">Now that we learned how to create and manage topologies we will have a look at some advanced functionality of ToMaTo. In this part we will change the link characteristics between the elements and have a look at the packets that travel over them.</p>',
		skip_button: 'Continue',
		help_page: 'LinkEmulation'
	},
	{
		text: '<p class="tutorialExplanation">Now we will add a delay of 2 seconds to a link and check if we can see the difference. Open the attributes of the link of one OpenVZ VM as you learned in the the first part. Enable link emulation and add a delay of 2000 ms on one of the directions.</p>\
<p class="tutorialCommand">Add 2 seconds delay to one link</p>',
		trigger: function(event) {
			var data = getTutorialData();
			return compareToMask(event, {
				operation: "modify",
				component: "connection",
				phase: "end",
				attrs: {
					delay_from: data.delay
				}
			}) || compareToMask(event, {
				operation: "modify",
				component: "connection",
				phase: "end",
				attrs: {
					delay_to: data.delay
				}
			});
		},
		help_page: 'LinkEmulation'
	},
	{
		text: '<p class="tutorialExplanation">You should see the delay when you send messages between your OpenVZ VMs. The delay should only exist in one direction.<br/>\
Now you can play around with the settings a little. Maybe add some jitter to the connection. If you apply packet duplication or packet loss you can use the sequence numbers to check this functionality.</p>\
<p class="tutorialCommand">Click continue when you want to continue</p>',
		skip_button: 'Continue',
		help_page: 'LinkEmulation'
	},
	{
		text: '<p class="tutorialExplanation">Now we will have a look at how the packets of our chat client look like. Open the attribute window of a connection again and activate packet capturing. Please keep the mode at <i>for download</i> and do not apply a filter.</p>\
<p class="tutorialCommand">Enable packet capturing for one link</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "connection",
				phase: "end",
				attrs: {
					capturing: true
				}
			});
		},
		help_page: 'PacketCapturing'
	},
	{
		text: '<p class="tutorialExplanation">Make sure that some chat messages go over that link and then we can have a look at them. To view them, we will use an online service called <i>Cloudshark</i>. Right click on the link and choose <i>View capture in Cloudshark</i>.</p>\
<p class="tutorialCommand">Open the captured packets in Cloudshark</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "action",
				component: "connection",
				action: "download_grant",
				phase: "end"
			});
		},
		help_page: 'PacketCapturing'
	},
	{
 		text: '<p class="tutorialExplanation">Have a look at the packets and try to figure out how they are encoded and what the fields could mean.</p>\
<p class="tutorialExplanation">It might happen that your pop-up blocker prevents the Cloudshark window from opening. You should disable the blocker for ToMaTo.</p>\
<p class="tutorialCommand">Click on continue when you are done</p>',
		skip_button: 'Continue',
		help_page: 'PacketCapturing'
	},
	{
		text: '<h3>Fourth part</h3>\
<p class="tutorialExplanation">Ok, now you have seen some of the features of ToMaTo. The only important thing that is missing now is external connectivity.<br/>\
In this part we will open our topology to the Internet.</p>',
		skip_button: 'Continue',
		help_page: 'NetworkTypes',
	},
	{
		text: '<p class="tutorialExplanation">Select the Internet from the menu and add it to the topology. In the attribute window you can select the type of external network that you want but Internet is the default.<br/>\
This external network is an opening of your topology. Whatever is connected to this element is connected to that network, i.e. to the Internet in our case.</p>\
<p class="tutorialCommand">Add an <i>Internet</i> external network to your topology</p>',
		help_page: 'NetworkTypes',
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
  <li>Stop and destroy the switch so you can change its connections.</li>\
  <li>Stop and disconnect the sender chat agent, you do not want to spam the Internet.</li>\
  <li>Connect the Internet to the switch.</li>\
  <li>Start everything again.</li>\
</ol>\
You know how to do this from the earlier tutorial parts.</p>\
<p class="tutorialCommand">Click on continue when you are finished</p>',
		skip_button: 'Continue',
		help_page: 'NetworkTypes'
	},
	{
		text: '<p class="tutorialExplanation">When your topology is connected to the Internet, you can reach the Internet from the connected VMs.<br/>\
Check that by typing the following into the console of one of the VMs: <pre><tt>ping www.google.com</tt></pre><br/>\
If you do not get a reply, you might need to obtain a network address first by running the following: <pre><tt>dhclient eth0</tt></pre><br/>\
If you see high latencies or lost packets, you might still have link emulation enabled.</br>\
You can use this connection to exchange files with your nodes and to use external services.</p><br/>\
<p class="tutorialCommand">Click on continue when you are done</p>',
		skip_button: 'Continue',
		help_page: 'NetworkTypes'
	},
	{
		text: '<p class="tutorialExplanation">If you want to, you can start a chat client on one of the VMs and maybe someone answers.</p>\
<p class="tutorialCommand">Click on continue when you are finished</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">To delete your VMs and free the resources, click the <i>Destroy</i> button in the top menu.</p>\
<p class="tutorialCommand">Destroy the topology</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			var match = compareToMask(event, {
				operation: "action",
				component: "element",
				action: "destroy",
				phase: "end"
			});
			if (match) data.tmp++;
			if (data.tmp >= 5) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we are at the end of the tutorial, I hope you enjoyed it.</p>'
	}
]

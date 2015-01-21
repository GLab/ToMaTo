[
	{
		text: '<h2>ToMaTo OpenFlow Tutorial</h2>\
<p class="tutorialExplanation">In this tutorial you will learn the basics of OpenFlow and how to do OpenFlow experiments in the Topology Management Tool.</p>\
<p class="tutorialExplanation">Please read the full explanations of a step before working on it.</p>\
<h3>First part</h3>\
<p class="tutorialExplanation">In this part we will set up our topology with one switch, three nodes and a controller.</p>',
		skip_button: 'Start tutorial'
	},
	{
		text: '<p class="tutorialExplanation">In this tutorial we will use the <i>OpenVSwitch</i> software to emulate an OpenFlow switch. It will behave like a hardware OpenFlow switch and support all OpenFlow commands. However it does not provide the same forwarding speed as a physical switch.</p>\
		<p class="tutorialExplanation">OpenVSwitch is available as a KVM template, so you can find it directly in the menu.</p>\
		<br/>\
		<p class="tutorialCommand">Add an <i>OpenFlow Switch</i> to your topology.</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "kvmqm",
					attrs: {
						template: "openvswitch"
					}
				},
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">As a next step we will prepare the switch.</p>\
		<br/>\
		<p class="tutorialCommand">Prepare the switch</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "action",
				component: "element",
				phase: "end",
				action: "prepare"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Ok now we will configure some things on the switch:<ul>\
		<li>Rename the switch to <i>switch</i>.</li>\
		<li>Since the switch is based on KVM, it has a keyboard layout. For the switch, this is <i>English (US)</i>, so we need to change the configuration to match this.</li>\
		<li>For KVM devices the editor assumes that network segments will end at the device. Being a switch, the device will connect network segments instead. We need to change that in the configuration to help the editor calculate network segment boundaries which will influence various aspects like automatically assigned IP addresses.</li>\
		</ul></p>\
		<br/>\
		<p class="tutorialCommand">Rename the switch and configure it to use <i>English (US)</i> keyboard layout and to <i>connect network segments</i></p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">In this tutorial, we will modify the communication between the connected nodes. For this, you need to add three nodes.</p>\
		<br/>\
		<p class="tutorialCommand">Add 3 OpenVZ nodes around the switch and name them <i>node1</i>, <i>node2</i> and <i>node3</i></p>',
		trigger: function(event) {
		    var data = getTutorialData();
			if (! data.tmp1) data.tmp1 = 0;
			if (! data.tmp2) data.tmp2 = 0;
			if (compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "openvz"
				},
			})) data.tmp1++;
			if (compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end"
			})) data.tmp2++;
			if (data.tmp1 >= 3 && data.tmp2 >= 3) {
				data.tmp1 = 0;
				data.tmp2 = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now connect everything with the switch. When we do that in order, the new interfaces will also be assigned addresses in that order.</p><br/>\
		<p class="tutorialCommand">Connect the 3 nodes to the switch in order.</p>',
		trigger: function(event) {
		    var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			if (compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			})) data.tmp++;
			if (data.tmp >= 3) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">To be able to ping between the nodes, they need to have proper IP addresses. You can configure them using the console of the nodes, but ToMaTo provides an easier way to configure interfaces on OpenVZ machines.</p>\
		<p class="tutorialExplanation">If you right-click on the network interfaces of the nodes and select configure, a configuration dialog will open and allow you to set the IPv4 address of the interface.</p>\
		<p class="tutorialExplanation">ToMaTo even assignes addresses automaticaly and if you configured the switch correctly, those IPs are correct too.</p>\
		<p class="tutorialExplanation">Make sure the nodes use the following addresses:\
		<dl class="dl-horizontal">\
			<dt>node1</dt><dd><tt>10.0.0.1/24</tt></dd>\
			<dt>node2</dt><dd><tt>10.0.0.2/24</tt></dd>\
			<dt>node3</dt><dd><tt>10.0.0.3/24</tt></dd>\
		</dl>\
		</p>\
		<p class="tutorialCommand">Configure the IP addresses of the nodes.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now we are ready to start the topology.</p>\
		<br/>\
		<p class="tutorialCommand">Start the topology.</p>',
		trigger: function(event) {
		    var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			if (compareToMask(event, {
				operation: "action",
				component: "element",
				phase: "end",
				action: "start"
			})) data.tmp++;
			if (data.tmp >= 4) {
				data.tmp = 0;
				setTutorialData(data);
				return true;
			}
			setTutorialData(data);
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">To be able to configure the switch later, we need to assign an IP address to it. Since the switch is based on KVM you cannot configure its interface using ToMaTo. Instead you can set the IP address by using the command <pre><tt>address 10.0.0.100</tt></pre> on the console of the switch. The switch will remember this address even after reboot. Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Set the IP address of the switch to <i>10.0.0.100</i>.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">To be able to see the connectivity we will now start some pings and keep them running during the rest of the experiment. You can ping a node using the ping command on the console: <pre><tt>ping ADDRESS</tt></pre></p>\
		<p class="tutorialExplanation">\
		Please set up the following pings and let them run:\
		<ul>\
		<li>node1 -> node2 (10.0.0.2)\
		<li>node2 -> node1 (10.0.0.1)\
		<li>node3 -> node1 (10.0.0.1)\
		</ul>\
		The pings will continue to run even if you close the console but there is no need to close it. Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Set up continous pings between the nodes.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Those pings should have worked and display a new line every second.</p>\
		<p class="tutorialExplanation">In its default setting the OpenFlow switch is configured to behave like a normal learning switch. We are now going to change this behaviour and set it secure mode. This means that if there is no controller that manages the switch, it will block all new flows.</p>\
		<p class="tutorialExplanation">You can set the switch to secure mode using the following command:<pre><tt>ovs-vsctl set-fail-mode br0 secure</tt></pre>\
		Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Set the <i>fail-mode</i> on the switch to <i>secure</i> and save that setting.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">If you check your ping commands, you will see that the switch currently blocks all communication between the nodes.</p>\
		<p class="tutorialExplanation">Now we will add an OpenFlow controller to the topology to control the switch. There are different controllers available but we will use the <i>Ryu</i> software.</p>\
		<br/>\
		<p class="tutorialCommand">Add a <i>Ryu OpenFlow Controller</i> to the topology.</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "openvz",
					attrs: {
						template: "ryu"
					}
				},
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we need to connect the controller to the switch. Since the switch is currently running, we have to stop it first.</p>\
		<br/>\
		<p class="tutorialCommand">Connect the controller to the switch.</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "connection",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Before we start the switch and the controller again, we will first configure the IP address of the controller. Again, ToMaTo should have automatically done this right but we should check that.</p>\
		<br/>\
		<p class="tutorialCommand">Configure the controller to use the IP <i>10.0.0.4/24</i>.</p>',
		skip_button: 'Continue',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "modify",
				component: "element",
				phase: "end"
			});
		}
	},
	{
		text: '<p class="tutorialExplanation">Now we are ready and can start the switch and controller again.</p><br/>\
		<p class="tutorialCommand">Start the switch and the controller.</p>',
		trigger: function(event) {
		    var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			if (compareToMask(event, {
				operation: "action",
				component: "element",
				phase: "end",
				action: "start"
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
		text: '<p class="tutorialExplanation">Ok, now the controller is connected but the switch does not know it yet. You can check this by executing the following command on the switch:<pre><tt>ovs-vsctl show</tt></pre></p>\
		<p class="tutorialExplanation">To configure the controller, just run the following commands on the switch:<pre><tt>ovs-vsctl set-fail-mode br0 standalone\n\
ovs-vsctl set-controller br0 tcp:10.0.0.4:6633</tt></pre>\
		These commands basically tell the switch to return to standalone mode and to communicate with the controller that will be located at 10.0.0.4 port 6633.</p>\
		<p class="tutorialExplanation">Later when the controller is running you can verify that the controller is connected by checking the <i>ovs-vsctl show</i> command again: It should contain <i>is_connected: true</i>.</p>\
		<p class="tutorialExplanation">Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Configure the switch to use the controller.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<h3>Second part</h3>\
<p class="tutorialExplanation">We have now set up a basic OpenFlow configuration. In this second part we use the switch as a firewall and configure some rules.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now we set up the controller. Since we want to run the controller and send commands to it at the same time, we need to start <pre><tt>screen -s bash</tt></pre> on the console.</p>\
		<p class="tutorialExplanation"><i>Screen</i> can run several programs in parallel on the same console. When you start it, it will open the first window which looks exactly like the console before. Screen can be controlled by a few commands:<ul>\
		<li><i>Ctrl-a c</i> (first Ctrl-a, then c) creates and opens a new window.</li>\
		<li><i>Ctrl-a n</i> cycles through the existing windows.</li>\
		<li><i>Ctrl-a "</i> (yes that is a double quote) shows a list of all existing windows and allows to choose one.</li>\
		<li><i>Ctrl-d</i> closes one window. If the last window is closed, screen terminates.</li>\
		</ul></p>\
		<p class="tutorialExplanation">We need a screen with two windows.</p>\
		<br/>\
		<p class="tutorialCommand">Start a screen with two windows.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Ok now we will start the firewall in the first window. Run <pre><tt>ryu run ryu.app.rest_firewall</tt></pre> to start the firewall controller. It will print debug messages and after some time will show that the switch is connected.</p>\
		<p class="tutorialCommand">Start the firewall controller.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">To send commands to the controller we will switch to the second window and use the <i>http</i> command to talk to the <a href="http://osrg.github.io/ryu-book/en/html/rest_firewall.html#rest-api-list" target="_blank">REST interface of the controller</a>.</p>\
		<p class="tutorialExplanation">To simplify our commands we will first define a variable: <pre><tt>FW="http://localhost:8080/firewall"</tt></pre>. This variable contains the URL base path so we do not need to type that all the time.</p>\
		<p class="tutorialExplanation">Since the controller does not know the switch, we first need to enable the firewall functionality there. We can do that now with the command <pre><tt>http put $FW/module/enable/all</tt></pre></p>\
		<br/>\
		<p class="tutorialCommand">Enable the firewall.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now we will allow traffic between <i>node1</i> and <i>node2</i> by adding two rules.</p>\
		<p class="tutorialExplanation">Traffic rules can be added with the following command: <pre><tt>http post $FW/rules/all nw_src=IP nw_dst=IP action=ACTION</tt></pre> where IP is any IP address and ACTION is either <i>allow</i> or <i>deny</i>.</p>\
		<p class="tutorialExplanation">You should see the effect on the ping command between those two nodes.</p>\
		<br/>\
		<p class="tutorialCommand">Allow traffic between <i>node1</i> and <i>node2</i></p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">To see the current rules of the firewall, you can use the command <pre><tt>http get $FW/rules/all</tt></pre></p>\
		<br/>\
		<p class="tutorialCommand">Check the firewall rules</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now we want to remove all firewall rules. Removing a rule is as simple as sending the command <pre><tt>http delete $FW/rules/all rule_id=RULE</tt></pre> where RULE is either the number of a rule or <i>all</i> to remove all rules.</p>\
		<p class="tutorialExplanation">When you delete the rules, the ping should stop working.</p>\
		<br/>\
		<p class="tutorialCommand">Remove all firewall rules</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now all tree pings should work again.</p>\
		<p class="tutorialExplanation">This tutorial is now at its end. You can play around with the controller and the switch if you want. Please think about shutting down your topology when you are done.</p><br/>'
	}
]

[
	{
		text: '<h2>ToMaTo OpenFlow Tutorial</h2>\
<p class="tutorialExplanation">In this tutorial you will learn the basics of OpenFlow and how to do OpenFlow experiments in the Topology Management Tool.</p>\
<p class="tutorialExplanation">Please read the full explanations of a step before working on it.</p>',
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
			setTutorialData(data)
			return false;
		}
	},
	{
		text: '<p class="tutorialExplanation">Now connect everything with the switch.</p><br/>\
		<p class="tutorialCommand">Connect the 3 nodes with to the switch.</p>',
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
		text: '<p class="tutorialExplanation">To be able to ping between the nodes we have to configure their IP addresses. You could do that using the console of the nodes, but ToMaTo provides an easier way to configure interfaces on OpenVZ machines.</p>\
		<p class="tutorialExplanation">Right-click on the network interfaces of the nodes and select configure. A configuration dialog will open and allow you to set the IPv4 address of the interface.</p>\
		<p class="tutorialExplanation">Configure the following addresses on the nodes:\
		<dl class="dl-horizontal">\
			<dt>node1</dt><dd><tt>10.0.0.1/24</tt></dd>\
			<dt>node2</dt><dd><tt>10.0.0.2/24</tt></dd>\
			<dt>node3</dt><dd><tt>10.0.0.3/24</tt></dd>\
		</dl>\
		</p>\
		<p class="tutorialCommand">Configure the IP addresses of the nodes.</p>',
		trigger: function(event) {
			var data = getTutorialData();
			if (! data.tmp) data.tmp = 0;
			if (compareToMask(event, {
				operation: "modify",
				component: "element",
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
		<p class="tutorialExplanation">Now we will add an OpenFlow controller to the topology to control the switch. There are different controllers available but we will use the <i>Floodlight</i> software.</p>\
		<br/>\
		<p class="tutorialCommand">Add an <i>Floodlight OpenFlow Controller</i> to the topology.</p>',
		trigger: function(event) {
			return compareToMask(event, {
				operation: "create",
				component: "element",
				phase: "end",
				attrs: {
					type: "openvz",
					attrs: {
						template: "floodlight"
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
		text: '<p class="tutorialExplanation">Before we start the switch and the controller again, we will first configure the IP address of the controller.</p>\
		<br/>\
		<p class="tutorialCommand">Configure the controller to use the IP <i>10.0.0.4/24</i>.</p>',
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
		These commands basically tell the switch to return to standalone mode and to communicate with the controller that is located at 10.0.0.4 port 6633. Afterwards you can verify that the controller is connected by checking the <i>ovs-vsctl show</i> command again: It should contain <i>is_connected: true</i>. Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Configure the switch to use the controller.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">If you now check the output of your pings, it should show that the connections are working. This is because the switch asked the controller what to do with the ping packets and the controller configured the flows for the MAC addresses like a learning switch would do. You can see the two flows by running the following command on the switch: <pre><tt>ovs-ofctl dump-flows br0</tt></pre></p>\
		<p class="tutorialExplanation">We will now disable this behavior in the controller and later configure the flows manually. Therefore open the file <i>/etc/floodlight.conf</i> on the controller and remove the line containinig <i>forwarding.Forwarding</i>. Afterwards, save the file and restart the Floodlight software using: <pre><tt>/etc/init.d/floodlight restart</tt></pre>Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Disable forwarding in the controller.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">After a short time (the dynamic flows added by the forwarding module have to time out first), you will notice that the pings stop working. You can also check that there are no flows present on the switch using the command <i>ovs-ofctl dump-flows br0</i></p>\
		<p class="tutorialExplanation">Now we can start defining our own static flows using the circuitpusher tool on the controller: <pre><tt>circuitpusher --add --type ip --src SRC_IP --dst DST_IP --name FLOW_NAME</tt></pre>\
		This command will establish a bidirectional flow between <i>SRC_IP</i> and </i>DST_IP</i> that allows for e.g. pings to work. The <i>FLOW_NAME</i> must be unique and is used to identify the flow. Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Push a static flow between <i>node1 (10.0.0.1)</i> and <i>node2 (10.0.0.2)</i>.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">You will now see that the pings between <i>node1</i> and <i>node2</i> work again while <i>node3</i> is still unable to ping. You can also see the new flows using <i>ovs-ofctl dump-flows br0</i>.</p>\
		<p class="tutorialExplanation">Now we will push a static flow between <i>node1</i> and <i>node3</i> to enable the ping on <i>node3</i>. Click on continue when you are done.</p>\
		<br/>\
		<p class="tutorialCommand">Push static flows between <i>node1 (10.0.0.1)</i> and <i>node3 (10.0.0.3)</i>.</p>',
		skip_button: 'Continue'
	},
	{
		text: '<p class="tutorialExplanation">Now all tree pings should work again.</p>\
		<p class="tutorialExplanation">This tutorial is now at its end. You can play around with the controller and the switch if you want. Please think about shutting down your topology when you are done.</p><br/>'
	}
]

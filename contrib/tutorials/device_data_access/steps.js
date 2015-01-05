[
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Device and Data Access tutorial!<br />\
						This tutorial will teach you how you can upload and/or download data to or from your devices and also how to use different remote control tools to get  access to your devices.</p>\
					<p class="tutorialExplanation">\
						<i>This tutorial requires knowledge which has been taught in the beginners\' tutorial, and a basic knowledge about the Linux command line (especially ifconfig, ssh, and scp)</i>.</p>',
			skip_button: 'Start tutorial'
			},
			{
			trigger:function(obj) {
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				var match = compareToMask(obj, {
					action: "prepare",
					component: "element",
					operation: "action",
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
			text:	'<p class="tutorialExplanation">\
						Let\'s assume you have created this topology, and now you need to put files on your devices to install software in order to execute your experiment.</p>\
<p class="tutorialExplanation">\
						Currently, your topology does only exist as a "plan". This means, that devices do not have any hard drive images or similar.</p>\
					<p class ="tutorialExplanation">\
						When you prepare the devices, those images will be created from the templates. We also need the devices to be running so start them too.</p>\
					<p class="tutorialCommand">\
						Prepare and Start your topology\'s devices.</p>'
			},
			{
			text:	'<p class="tutorialExplanation">\
					Wait for both devices to be prepared and started.</p>\
				<p class="tutorialExplanation">\
					Until this is finished you can already download the following executable archive we need for our next step. We will run it on one of our devices, so please download the following archive:\
			<ul>\
			<li><a href="'+tutorial_base_url+'simulation_installer.tar.gz" class="download" download="simulation_installer.tar.gz">Simulation</a></li>\
			</ul>\
					It will install a litte &quot;simulation&quot; for us in order to create some data.</p>\
				<p class="tutorialCommand">\
					Wait for both devices to be prepared and started and download the executable archive. Press "Continue" afterwards.</p>',
			skip_button: "Continue"
			},
			{
			trigger: function(event) {

					return compareToMask(event, {
						operation: "action",
						phase: "end", 
						action: "rextfv_upload_use",
						component: "element"
					});
				},
			text:	'<p class="tutorialExplanation">\
					Now after the devices started right click on the left device (openvz1) and use <pre>&gt; Executable archive &gt; Upload Archive</pre> to upload and run the archive on your device</p>\
<p class="tutorialExplanation">\
					After the upload, the archive will be automatically executed by running the <i>auto_exec.sh</i> file inside it if the file exists.\
Executable archives are a good way to run programms on a device. If you want to learn more about them feel free to visite the <i>Executable Archives tutorial</i>.</p>',
			skip_button: "Continue"
			},			
			{
			trigger: function(obj) { 
				var match = compareToMask(obj, {
					component: "element",
					operation: "console-dialog",
				});
				return match;
			},
			text:	'<p class="tutorialExplanation">\
					This archive will install a little programm, which we will run manually.</p>\
				<p class="tutorialExplanation">\
					Use right click again on your device and open a console using NoVNC. It is a HTML5 based VNC (Virtual Network Computing) client. <br/>\
					You could also use the Java VNC applet or directly copy the vnc link for any vnc client you prefer to use.</p>\
				<p class="tutorialCommand">\
					Right click on the left device and open a console using NoVNC</p>',
			},
			{
			text:	'<p class="tutorialExplanation">\
						Now let\'s start the simulation. Just run the command <pre>simulation</pre> on the device.<br/>\
The simulation will create some output on your console and also create data in a special file.</p>\
					<p class="tutorialCommand">\
						Run the simulation on your device using the <i>simulation</i> command. Press "Continue" afterwards.</p>',
			skip_button: "Continue"

			},
			{
			trigger: function(obj) { 
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				var match = compareToMask(obj, {
					action: "stop",
					component: "element",
					operation: "action",
					phase: "end"
				});
				if (match) data.tmp++;
				if (data.tmp >= 2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
				}
				setTutorialData(data)
				return false;
			},
			text:	'<p class="tutorialExplanation">\
						Maybe you want to create multiple copies of the fully configured device in your topology or run it in a virtual machine on your computer.\
						<br/>Therefor it is usefull to download your device image and use it as a template. <br/>\
						To do this you have to stop your device. <br/>\
						We also want to change our topology for a different reason so stop the whole topology.</p>\
					<p class="tutorialCommand">\
						Stop the topology.</p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						Now download the device image from the device. This might take a bit longer. <br/> \
						You can continue the tutorial during the download. We will do some changes first before we need the image again.</p>',
			skip_button: "Continue"
			},
			{
			trigger: function(obj) { 
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				var match = compareToMask(obj, {
					component: "element",
					operation: "create",
					phase: "end",
					object: {
						data: {
							attrs: {
								kind: "internet",
							}
						}
					},
				}); 
				if(match) data.tmp++;
				match = compareToMask(obj, {
					component: "connection",
					operation: "create",
					phase: "end",
				});
				if(match) data.tmp++;
				if(match>=2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
				}
				setTutorialData(data);
				return false;
			},
			text:	'</p>\
					<p class ="tutorialExplanation">\
						The easiest way to transmit files to or from your devices is the Internet.<br />\
						Devices don\'t have an Internet connection by default. To connect them, the first thing you need to do is to create an Internet interface</p>\
				<p class="tutorialExplanation">\
						If you want to get access to your device using SSH or similar technologies you need to connect them to the Internet too.\
						<br />VNC instead works also in topologys without an Internet connection.</p>\
						<p class="tutorialCommand">\
						Add an Internet element and connect it to the switch.</p>',
			skip_button: "Continue"
			},	
			{
			trigger: function(obj) { 
				var match = compareToMask(obj, {
					component: "element",
					operation: "action",
					action: "upload_grant",
					phase: "end",
				});
				return match;
			},
			text:	'<p clas s="tutorialExplanation">\
						You can upload any image to a device of the same technology. You can not use images accross technologies (e.g., you can\'t upload an OpenVZ image to a KVM device, and vice versa).</p>\
					<p class="tutorialCommand">\
						Upload your image again to the second device (openvz2).</p>\
					<p class="tutorialExplanation">\
					You can skip this step  if a big upload might cause you trouble. Then please run the executable archive on the second device so we can continue the tutorial.</p>\
					<p class="tutorialExplanation">\
						The tutorial will continue after the upload has been finished.<br />\
						If you need to create multiple devices with certain modifications to their template,\
						creating the image in one device, and then distributing it to many might be the best method to accomplish this.</p>'
			},
			{
			trigger: function(obj) { 
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				var match = compareToMask(obj, {
					action: "start",
					component: "element",
					operation: "action",
					phase: "end"
				});
				if (match) _data.tmp++;
				if (data.tmp >= 2) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
				}
				setTutorialData(data);
				return false;
			},
			text:	'<p class="tutorialExplanation">\
						If you want to learn more about images and templates feel free to try the Images & Templates tutorial after this tutorial.</p>\
				<p class="tutorialExplanation">\
						After the upload has finished please start your topology again.</p>\
					<p class="tutorialCommand">\
						Start the topology.</p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						SSH is deactivated by default. In order to use it we have to remote connect to our device (with NoVNC) and run <i>ssh-enable</i>. <br/> Let\'s do it, so we can use SSH to get access to our device.</p>\
				<p class="tutorialCommand">\
						Use NoVNC to run <i>ssh-enable</i> on the second device (openvz2). Press "Continue" if you did so.</p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						You can now use your local SSH client to get access to the device. You can find the ip address of your device by using <i>ipconfig</i>.</p>\
				<p class="tutorialExplanation">\
						If you want to copy data from or to a device you can use <i>SCP</i>. It is like SSH pre-installed in most of the templates.</p>\
				<p class="tutorialCommand">\
						Try to connect to your device using SSH. After that press "Continue".</p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
						That was it for this tutorial! More ways to access data will be coming soon. <br />\
						Don\'t forget to take a look at the <i>executable archives</i> and <i>template and images</i> tutorials</p>'
			}
]

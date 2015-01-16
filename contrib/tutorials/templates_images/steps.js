[
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Templates and Images tutorial!<br />\
						This tutorial will teach you how you can use pre-build templates for your devices or even upload or download images from/to devices.</p>\
					<p class="tutorialExplanation">\
						Let\'s assume you have created this topology, and now you realized you want to use different templates\
							without recreating and replacing all elements.</p>\
					<p class="tutorialExplanation">\
						<i>This tutorial requires knowledge which has been taught in the beginners\' tutorial, and a basic knowledge about the Linux command line.</i></p>',
			skip_button: 'Start tutorial'
			},
			{
			trigger:function(obj) {
				mask = {
					action: "change_template",
					component: "element",
					operation: "action",
					phase: "end"
				};
				return compareToMask(obj,mask);
				
			  },
			text:	'<p class="tutorialExplanation">\
						Right click on your device and use the <i>Configure</i> window to change the template from <i>Ubuntu 12.04 (x86_64)</i> to <i>Debian 7.0 (x86_64)</i></p>\
				<p class="tutorialExplanation">If you change the template of one of our devices the image will be deleted and there is no way to restore it.<br/>\
						So be careful with changing templates or uploading images.\
					<p class="tutorialCommand">\
						Change the template for your device to <i>Debian 7.0 (x86_64)</i></p>'
			},
			{
			trigger:function(obj) { 
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				mask = {
					action: "prepare",
					component: "element",
					operation: "action",
					phase: "begin"
				};
				if(compareToMask(obj,mask)) data.tmp +=1;
				mask = {
					action: "start",
					component: "element",
					operation: "action",
					phase: "begin"
				};				
				if(compareToMask(obj,mask) && data.tmp >= 1) {
					data.tmp++;
				}
				if(data.tmp >= 3) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
				}
				setTutorialData(data);
				return false;
				
			  },
			text:	'<p class="tutorialExplanation">\
						With preparing devices, images from those templates will be created.</p>\
				<p class="tutorialExplanation">\
						We also need to start our topologie for the next steps.</p>\
				<p class="tutorialCommand">\
						Prepare and start your device</p>',
			skip_button: "Continue"
			},
			{ 
			trigger:function(obj) { 
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;
				mask = {
					component: "element",
					operation: "console-dialog",
				};
				if(compareToMask(obj,mask)) data.tmp +=1;
				mask = {
					action: "start",
					component: "element",
					operation: "action",
					phase: "begin"
				};					
				if(compareToMask(obj,mask) && data.tmp >= 1) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
				}
				setTutorialData(data);
				return false;
				
				
			  },
			text:	'<p class="tutorialExplanation">\
					Now we want to install something on our device, so we can later use the image of the device to copie his installed configuration to other devices.</p>\
				<p class="tutorialExplanation">\
					Open a console on your device like NoVNC by right-clicking on the device using <i>Console &raquo; NoVNC</i></p>\
				<p class="tutorialCommand">\
					Open a NoVNC console for your device.</p>',		
			},
			{
			text:	'<p class="tutorialCommand">\
					Now use the follow command to install python on your device:\
					<pre>apt-get install python</pre>\
					<br />\
					Press <I>Continue</i> after python was installed.</p>',
			skip_button: "Continue"
			},
			{
			trigger:function(obj) { 
				
				mask = {
					action: 'download_grant',
					component: "element",
					operation: "action",
					phase: "end"
				};
				return compareToMask(obj,mask);
			
			  },
			text:	'<p class="tutorialExplanation">\
						Now we want to backup our device\'s disk image for use as a configured image on a new device.<br />\
						You can download the disk image of any prepared device by right-clicking on the device and select "Download image".<br/>\
						We have to stop the device first, bevor we can download or upload an image.</p>\
					<p class="tutorialCommand">\
						Stop the device and download a disk image.</p>\
					<p class="tutorialExplanation">\
						Warning: The download might be big. Skip this step if you are on a metered connection!</p>'
			},
			{
			trigger:function(obj) { 
				var data = getTutorialData();
				if (! data.tmp) data.tmp = 0;

				mask = {
					component: "element",
					operation: "create",
					phase: "end"
				};
				if(compareToMask(obj,mask) && data.tmp < 1) data.tmp +=1;
				mask = {
					action: "start",
					component: "element",
					operation: "action",
					phase: "begin"
				};				
				if(compareToMask(obj,mask) && data.tmp >= 1) {
					data.tmp = 0;
					setTutorialData(data);
					return true;
				}
				setTutorialData(data);
				return false;
			},
			text:	'<p class="tutorialExplanation">\
						The download might take a bit longer. You can do this step while the file is still downloading.</p>\
				<p class="tutorialExplanation">\
						You can upload any image to a device of the same technology. You can not use images accross technologies (e.g., you can\'t upload an OpenVZ image to a KVM device, and vice versa).</p>\
				<p class="tutorialExplanation">\
					Lets create another OpenVZ device and prepare it.</p>\
				<p class="tutorialCommand">\
					Create a OpenVZ device and prepare it.</p>',
					
			},
			{
			trigger:function(obj) {	
				mask = {
					action: 'upload_use',
					component: "element",
					operation: "action",
					phase: "end"
				};
				return compareToMask(obj,mask);
			
			  },
			text: 	'<p class="tutorialCommand">\
						After the download has been completed, upload your image to the new device.</p>\
					<p class="tutorialExplanation">\
						Again, you might want to skip this step if a big upload could cause you any troubles with your Internet connection.</p>\
					<p class="tutorialExplanation">\
						The tutorial will continue after the upload has been finished.<br /><br/>\
						If you need to create multiple devices with certain modifications to their template,\
						creating the image in one device, and then distributing it to many might be the best method to accomplish this.</p>',
			},
			{
			//TODO
			trigger:function(obj) {
				mask = {
					action: 'upload_use',
					component: "element",
					operation: "action",
					phase: "end"
				};
				return compareToMask(obj,mask);
			},
			text:	'<p class="tutorialExplanation">\
						There is another way to create a device and using your own image. In the "Devices" tab, on the right side, you can find "upload own images" devices.<br />\
						When you place such a device on your topology, it will be prepared immediately, and then you will be asked to upload an image</p>\
					<p class="tutorialCommand">\
						Place suche a device on your topology (cancel the upload if you want). If you do so, click "Continue"</p>\
					<p class="tutorialExplanation">\
						Ignore this device for the rest of the tutorial, or delete it.</p>',
			skip_button: "Continue"
			},
			{
				text: '<p class="tutorialExplanation">Now we are at the end of the tutorial, I hope you enjoyed it.</p>'
			}
]

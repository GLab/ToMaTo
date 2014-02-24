[
			{
			text:	'<p class="tutorialExplanation">\
						Welcome to the Executable Archives tutorial!<br />\
						This tutorial will teach you how you can upload and afterwards automatically execute archives on your devices.</p>\
					<p class="tutorialExplanation">\
						Let\'s assume you have created this topology, and now you want to install a new programm on a device to execute your experiment.</p>\
					<p class="tutorialExplanation">\
						<i>This tutorial requires knowledge which has been taught in the beginners\' tutorial, and a basic knowledge about the Linux command line (especially ifconfig, ssh, and scp)</i></p>',
			skip_button: 'Start tutorial'
			},
			{

			trigger: function(event) {
				var match = compareToMask(event, {
					operation: "action",
					component: "element",
					action: "start",
					phase: "end"
				});
				return match;
				},
			text:	'<p class="tutorialExplanation">\
						Currently, your topology does only exist as a "plan". We have to start our topology first to sucessfully run an executable archive.</p>\
					<p class="tutorialCommand">\
						Prepare and Start your topology</p>'
			},
			{
			text: 	'<p class="tutorialExplanation">\
						We start this tutorial with using an executable archive to explain the abilitys of executable archives and afterwards we will create our own archive\
						and run it.\</p>',
			skip_button: 'Continue'
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
			text: 	'<p class="tutorialExplanation">\
					Please download the following archive. It will start a little simulation on our devices and it will create some output we will take a look at.</p>\
				 <p class="tutorialExplanation">\
					Executable archives contain a bash script with the name <i>auto_exec.sh</i>. <br />\
					After the archive got uploaded our device will search for this script and execute it. <br />\
					We will look closesly to such a script later in the tutorial</p>\
				<p class="tutorialCommand"><a href="'+tutorial_base_url+'experiment.tar.gz" style="color: blue;"  download="expirement.tar.gz">experiment.tar.gz</a> </p>',
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
					After you have downloaded the simulation archive you can upload it to your devices by right-clicking\
					on them and using <pre>&gt; Executable archive &gt; Upload Archive</pre></p>\
				 <p class="tutorialExplanation">\
					The devices will directly execute the auto_exec.sh bash script from the archive and run our simulation.</p>\
				<p class="tutorialCommand">\
					Upload the simulation archive to the device</p>',
			},
			{
			
			trigger: function(event) {
							return compareToMask(event, {
								operation: "rextfv-status",
								component: "element"
							});
					},
			text:	'<p class="tutorialExplanation">\
					You can check the status of the executed bash script by right-clicking your device and using <pre>&gt; Executable archive &gt; Status</pre></p>\
				<p class="tutorialCommand">\
					Check the status of our simulation</p>',
			},
			{
			text: 	'<p class="tutorialExplanation">\
					There are two standard status types <i>running</i> and <i>finished</i>. Underneath them you can see a custom status. It is possible to create a own custom status. We will learn more about it later in this tutorial</p>\
				<p class="tutorialExplanation">\
					The important thing about statuses is, that the interval between updates gets longer with the time of the script execution.</p>',
			skip_button: 'Continue'
			},
			{
			text:	'<p class="tutorialExplanation">\
					Now lets have a look where we can find our archive on our device. Open a console for the device and change the directory to <i>/mnt/nlXTP/</i> using the <i>cd</i> command<br />\
					You will find the <i>auto_exec.sh</i> bash script. After you uploaded the archive it got copied and executed into this directory. <br/>\
					Also you can find the <i>my_own_output.txt</i> file. The bash script created this file to show an example about creating own output files. <br/>\
					The <i>exec_status</i> directory contains four automatic created files. We will take later a look at them.</p>\
				<p class="tutorialCommand">Open a console for the device and take a look at the executable archive directory. Press Continue when you are finished.</p>',
			skip_button: 'Continue' 
					
					
			},			
			{
			trigger: function(event) {

					return compareToMask(event, {
						operation: "action",
						phase: "end", 
						action: "rextfv_download_grant",
						component: "element"
					});
				},
			text:	'<p class="tutorialExplanation">\
					You can also download your archive even when it\'s still running. This is usefull for getting output from programs.\
					Download the archive with right-clicking on the device using <pre>&gt; Executable archive &gt; Download Archive</pre></p>\
				<p class="tutorialCommand">Download the archive directly from the device</p>',
			},
			{
			text:	'<p class="tutorialExplanation">\
					Open the archive and take a closer look into it. You will find a bash script called <i>auto_exec.sh</i> and a file called <i>my_own_output.txt</i>.\
					</p>\
				<p class="tutorialExplanation">\
					Take also a look into the <i>exec_status</i> directory. You will find four files inside it. We will take a look at the <i>out</i> file. It contains the standard and error outputs of the auto_exec.sh script. This is similar to the output you would have gotten when running the script in a console. </p>\
				<p class="tutorialCommand">\
					You may examine the files if you like. Press Continue when you are finished.</p>',
			skip_button: 'Continue'
			},
			{
			text:	'<p class="tutorialExplanation">\
					We will now create an executable archive step by step. <br />\
					The first step is to create a bash script called <i>auto_exec.sh<i/> .<br />\
					Create and open this document with a text editor so we can create a bash script.\
					</p>\
					<p class="tutorialExplanation">\
						If you put an <i>auto_exec.sh<i> file to the root directory of your archive it will \
						be automatically executed by a device after the archive got uploaded.\
					</p>\
				<p class="tutorialCommand">\
					Create a file with name <i>auto_exec.sh</i> and open it with a text editor. Click <i>Continue</i> if you did so.</p>',
			skip_button: "Continue",
			},
			{
			text:	'<p class="tutorialExplanation">\
					The bash script has to start with a shebang, so that Linux knows how to execute it. Write the following line at the top of your new script: <br /> <pre>#!/bin/bash</pre></p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
					Now we will create some output and actualize the custom status by adding following lines of code \
					<pre>archive_setstatus "This is our custom server status"<br/>\
echo "This will be written into the out file of our archive"<br/>\
sleep 10</pre>\
					</p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
					The last step is to put our bash script into a gzipped tarball archive (.tar.gz).\
					</p>\
				 <p class="tutorialCommand">Create a gzipped tarball archive and put the auto_exec.sh into the root path of the archive</p>',
			skip_button: "Continue"
			},
			{
			text:	'<p class="tutorialExplanation">\
					Now upload and run your executable archive. You can check the status and after it finished you can download it to check the created output.</p>\
				<p class="tutorialCommand">Press Continue after you finished.</p>',
			skip_button: "Continue"			
			},			
			{
			text:	'<p class="tutorialExplanation">\
						That was it for this tutorial!</p>'
			}
]

<?php
#
# Copyright (c) 2000-2007 University of Utah and the Flux Group.
# All rights reserved.
# This file is part of the Emulab network testbed software.
# 
# Emulab is free software, also known as "open source;" you can
# redistribute it and/or modify it under the terms of the GNU Affero
# General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# 
# Emulab is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
# more details, which can be found in the file AGPL-COPYING at the root of
# the source tree.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
chdir("..");
require("defs.php3");
chdir("buildui");

PAGEHEADER("NetBuild");

#
# Only known and logged in users can do this.
#
$this_user = CheckLoginOrDie();
$uid       = $this_user->uid();
$isadmin   = ISADMIN();

#
# Verify page arguments.
#
$optargs = OptionalPageArguments("action", PAGEARG_STRING,
				 "experiment", PAGEARG_EXPERIMENT);

if (isset($action) && $action == "modify") {
    if (!isset($experiment)) {
	USERERROR("Must provide experiment to modify!", 1);
    }
    $pid = $experiment->pid();
    $eid = $experiment->eid();
    echo "<h3>Modifying $pid/$eid:</h3>";
}

?>

<applet code="Netbuild.class" width=800 height=600 MAYSCRIPT>
  <param name='exporturl'
         value="<?php echo $TBBASE?>/buildui/nssave.php3">
  <param name='importurl'
         value="<?php echo $TBBASE?>/shownsfile.php3">
  <param name='modifyurl'
         value="<?php echo $TBBASE?>/modifyexp.php3">
  <param name='uid'
	 value="<?php echo $uid?>">
  <param name='auth'
	 value="<?php echo $HTTP_COOKIE_VARS[$TBAUTHCOOKIE]?>">
  <param name='expcreateurl'
         value="<?php echo $TBBASE?>/beginexp_html.php3">
<?php
    if (isset($action) && $action == "modify") {
	echo "<param name='action' value='modify'>";
	echo "<param name='pid' value='$pid'>";
	echo "<param name='eid' value='$eid'>";
    }
?>
<pre>
NetBuild requires Java.

If you want to use NetBuild,
you should either enable Java in your browser 
or use the latest version of a Java-compliant browser 
(such as Mozilla, Netscape or Internet Explorer.)

Once you've gotten your Java on, 
please come back and enjoy NetBuild.
We'll still be here waiting for you.	

   - Testbed Ops
</pre>
</applet>

<hr>
<h2>Basic usage:</h2>
<ul>
<li>
  Drag Nodes and LANs from the <i>Palette</i> on the left into the <i>Workarea</i> in the middle.
</li>
<li>
  To link a Node to a Node (or to a LAN,) select the node (by clicking it,) then hold "ctrl" and click on the node (or LAN) you wish to link it to.
</li>
<li>
  Clicking the "create experiment" button will send you to the Emulab "create experiment" web page, automatically generating and sending an NS file for your designed topology along. From that page, you may create the experiment and/or view the generated NS file.
</li>
</ul>
<p>
<a href="../doc/docwrapper.php3?docname=netbuilddoc.html">Netbuild Full Reference</a>
</p>

<?php
#
# Standard Testbed Footer
# 
PAGEFOOTER();
?>

package buildui.connectors;
/*
 * Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
 * This file is part of ToMaTo (Topology management software)
 *
 * Emulab is free software, also known as "open source;" you can
 * redistribute it and/or modify it under the terms of the GNU Affero
 * General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 *
 * Emulab is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
 * more details, which can be found in the file AGPL-COPYING at the root of
 * the source tree.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import buildui.Netbuild;
import buildui.devices.Device;
import buildui.devices.Interface;
import java.awt.*;

import buildui.paint.NetElement;
import buildui.paint.PropertiesArea;
import java.applet.Applet;
import org.w3c.dom.Element;


public class EmulatedConnection extends Connection {

	public void drawIcon(Graphics g) {
		g.setColor(Color.lightGray);
		g.fillRect(-6, -6, 16, 16);

		g.setColor(Netbuild.glab_red_light);
		g.fillRect(-8, -8, 16, 16);

		g.setColor(Color.black);
		g.drawRect(-8, -8, 16, 16);
	}

	public EmulatedConnection(String newName, Connector con, Device dev) {
		super(newName, con, dev);
                setProperty("delay", "0");
                setProperty("lossratio", "0.0");
                setProperty("bandwidth", "10000");
                setProperty("capture", "false");
	}

  static PropertiesArea propertiesArea ;

  public static void init ( Applet parent ) {
    propertiesArea = new EmulatedConnectionPropertiesArea();
  }

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  public void readAttributes (Element xml) {
    super.readAttributes(xml);
    setProperty("delay", xml.getAttribute("delay"));
    if ( getProperty("delay", "").equals("") ) setProperty("delay", "0");
    setProperty("lossratio", xml.getAttribute("lossratio"));
    if ( getProperty("lossratio", "").equals("") ) setProperty("lossratio", "0.0");
    setProperty("bandwidth", xml.getAttribute("bandwidth"));
    if ( getProperty("bandwidth", "").equals("") ) setProperty("bandwidth", "10000");
    setProperty("capture", xml.getAttribute("capture").toLowerCase());
    if ( getProperty("capture", "").equals("") ) setProperty("capture", "false");
  }

  public String getInterfaceIpHint () {
    return "10."+getConnector().subnetId+".1."+hostIp+"/24" ;
  }

}

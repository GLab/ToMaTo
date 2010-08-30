package buildui.connectors;
/*
 * Copyright (c) 2002-2006 University of Utah and the Flux Group.
 * All rights reserved.
 * This file is part of the Emulab network testbed software.
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
import org.w3c.dom.Element;


public class EmulatedRouterConnection extends EmulatedConnection {

	public void drawIcon(Graphics g) {
		g.setColor(Color.lightGray);
		g.fillRect(-6, -6, 16, 16);

		g.setColor(Netbuild.glab_red_light);
		g.fillRect(-8, -8, 16, 16);

		g.setColor(Color.black);
		g.drawRect(-8, -8, 16, 16);
	}

	public EmulatedRouterConnection(String newName, Connector con, Device dev) {
		super(newName, con, dev);
	}

  static PropertiesArea propertiesArea = new EmulatedRouterConnectionPropertiesArea() ;

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  @Override
  public void writeAttributes(Element xml) {
    super.writeAttributes(xml);
    xml.setAttribute("gateway_ip", getProperty("gateway_ip", ""));
    xml.setAttribute("gateway_netmask", getProperty("gateway_netmask", ""));
  }

  public void readAttributes (Element xml) {
    super.readAttributes(xml);
    setProperty("gateway_ip", xml.getAttribute("gateway_ip"));
    setProperty("gateway_netmask", xml.getAttribute("gateway_netmask"));
  }
  
}

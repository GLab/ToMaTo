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


import buildui.devices.Device;
import buildui.paint.IconElement;
import org.w3c.dom.Element;

public abstract class Connector extends IconElement {

  public static Connector readFrom (Element x_con) {
    String type = x_con.getAttribute("type");
    if ( type.equals("real") ) return InternetConnector.readFrom(x_con);
    if ( type.equals("hub") ) return HubConnector.readFrom(x_con);
    if ( type.equals("switch") ) return SwitchConnector.readFrom(x_con);
    if ( type.equals("router") ) return RouterConnector.readFrom(x_con);
    return null;
  }

  public Connector (String newName, String iconName) {
    super(newName, true, iconName);
  }

  public abstract Connection createConnection ( Device dev ) ;

  public void writeAttributes(Element xml) {
    xml.setAttribute("id", getName());
    xml.setAttribute("pos", getX()+","+getY()) ;
  }

  public void readAttributes (Element xml) {
    String pos = xml.getAttribute("pos");
    try {
      int x = Integer.parseInt(pos.split(",")[0]);
      int y = Integer.parseInt(pos.split(",")[1]);
      move(x,y);
    } catch ( NumberFormatException ex ) {}
  }
}

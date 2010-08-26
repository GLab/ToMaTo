package buildui.devices;
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


import buildui.connectors.Connection;
import buildui.paint.IconElement;
import java.util.HashSet;
import java.util.Set;
import org.w3c.dom.Element;

public abstract class Device extends IconElement {

  public static Device readFrom (Element x_dev) {
    String type = x_dev.getAttribute("type");
    if ( type.equals("openvz") ) return OpenVzDevice.readFrom(x_dev);
    if ( type.equals("kvm") ) return KvmDevice.readFrom(x_dev);
    if ( type.equals("dhcpd") ) return DhcpdDevice.readFrom(x_dev);
    return null;
  }

  public Device (String newName, String iconName) {
    super(newName, true, iconName);
  }

  private Set<Interface> interfaces = new HashSet<Interface> () ;

  public Set<Interface> interfaces() {
    return interfaces ;
  }

  public void addInterface(Interface iface) {
    interfaces.add(iface);
  }

  public void removeInterface(Interface iface) {
    interfaces.remove(iface);
  }

  public Interface getInterface (String ifName) {
    for (Interface iface: interfaces) if ( iface.getName().equals(ifName)) return iface;
    return null;
  }

  public Interface createInterface (Connection con) {
    int ifaceNum = 0 ;
    while ( getInterface("eth"+ifaceNum) != null ) ifaceNum++;
    return createInterface("eth"+ifaceNum, con);
  }
  public abstract Interface createInterface (String name, Connection con);

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

};

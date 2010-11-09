package buildui.devices;
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

import buildui.Modification;
import buildui.connectors.Connection;
import buildui.paint.IconElement;
import java.applet.Applet;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashSet;
import java.util.Set;
import org.w3c.dom.Element;

public abstract class Device extends IconElement {

  public static Collection<String> hostGroups = new ArrayList<String> () ;

  public static void init ( Applet parent ) {
    hostGroups.clear();
    hostGroups.add("<auto>");
    hostGroups.addAll(Arrays.asList(parent.getParameter("host_groups").split(",")));
  }

  public static Device readFrom (Element x_dev) {
    String type = x_dev.getAttribute("type");
    if ( type.equals("openvz") ) return OpenVzDevice.readFrom(x_dev);
    if ( type.equals("kvm") ) return KvmDevice.readFrom(x_dev);
    return null;
  }

  public Device (String newName, String iconName) {
    super(newName, true, iconName);
    setProperty("type", getType());
    setProperty("hostgroup", "<auto>");
    setProperty("template", "<auto>");
  }

  public abstract String getType();

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

  public void readAttributes (Element xml) {
    String pos = xml.getAttribute("pos");
    try {
      int x = Integer.parseInt(pos.split(",")[0]);
      int y = Integer.parseInt(pos.split(",")[1]);
      move(x,y);
    } catch ( NumberFormatException ex ) {}
  }

  public void onNameChanged(String oldName, String newName) {
      Modification.add(Modification.DeviceRename(oldName, newName));
  }

  public void onPropertyChanged(String property, String oldValue, String newValue) {
      Modification.add(Modification.DeviceConfigure(this, property, newValue));
  }

}

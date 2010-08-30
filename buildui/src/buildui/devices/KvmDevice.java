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
import buildui.paint.NetElement;

import buildui.paint.PropertiesArea;
import java.util.ArrayList;
import java.util.Collection;
import org.w3c.dom.Element;

public class KvmDevice extends Device {

  public static Collection<String> templates = new ArrayList<String> () ;
  static int num = 1;

  public KvmDevice (String newName) {
    super(newName, "/icons/computer.png");
  }

  public NetElement createAnother () {
    return new KvmDevice("kvm"+(num++)) ;
  }

  static PropertiesArea propertiesArea = new KvmPropertiesArea() ;

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  @Override
  public Interface createInterface (String name, Connection con) {
    return new Interface(name, this, con);
  }

  @Override
  public void writeAttributes(Element xml) {
    super.writeAttributes(xml);
    xml.setAttribute("type", "kvm");
    xml.setAttribute("hostgroup", getProperty("hostgroup", ""));
    xml.setAttribute("template", getProperty("template", ""));
  }

  public void readAttributes (Element xml) {
    super.readAttributes(xml);
    setProperty("hostgroup", xml.getAttribute("hostgroup"));
    setProperty("template", xml.getAttribute("template"));
  }

  public static Device readFrom (Element x_dev) {
    String name = x_dev.getAttribute("id") ;
    KvmDevice dev = new KvmDevice(name);
    dev.readAttributes(x_dev);
    return dev ;
  }
}

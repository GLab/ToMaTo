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


import buildui.connectors.Connection;
import buildui.paint.NetElement;

import buildui.paint.PropertiesArea;
import java.applet.Applet;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import org.w3c.dom.Element;

public class OpenVzDevice extends Device {

  public static Collection<String> templates = new ArrayList<String> () ;
  static int num;

  public static void init ( Applet parent ) {
    num = 0 ;
    propertiesArea = new OpenVzPropertiesArea();
    templates.clear();
    templates.add("<auto>");
    templates.addAll(Arrays.asList(parent.getParameter("tpl_openvz").split(",")));
  }

  public OpenVzDevice () {
    this("openvz"+num);
  }

  public OpenVzDevice (String newName) {
    super(newName, "/icons/computer.png");
    num++;
    setProperty("root_password", "glabroot" );
    setProperty("gateway", "");
  }

  public NetElement createAnother () {
    return new OpenVzDevice("openvz"+num) ;
  }

  static PropertiesArea propertiesArea = new OpenVzPropertiesArea() ;

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  @Override
  public Interface createInterface (String name, Connection con) {
    return new ConfiguredInterface(name, this, con);
  }

  public void readAttributes (Element xml) {
    super.readAttributes(xml);
    setProperty("hostgroup", xml.getAttribute("hostgroup"));
    setProperty("template", xml.getAttribute("template"));
    setProperty("root_password", xml.getAttribute("root_password"));
    setProperty("gateway", xml.getAttribute("gateway"));
  }

  public static Device readFrom (Element x_dev) {
    String name = x_dev.getAttribute("id") ;
    OpenVzDevice dev = new OpenVzDevice(name);
    dev.readAttributes(x_dev);
    return dev ;
  }

    @Override
    public String getType() {
        return "openvz";
    }
}

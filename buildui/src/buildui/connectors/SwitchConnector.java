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

import buildui.devices.Device;
import buildui.paint.NetElement;

import buildui.paint.PropertiesArea;
import java.applet.Applet;
import org.w3c.dom.Element;

public class SwitchConnector extends Connector {

  static int num;
  static PropertiesArea propertiesArea ;

  public static void init ( Applet parent ) {
    num = 0;
    propertiesArea = new SwitchPropertiesArea();
    nextSubnetId = 1;
  }

  public SwitchConnector () {
    this("switch"+num);
  }

  public SwitchConnector (String newName) {
    super(newName, "/icons/switch.png");
    num++;
    subnetId = nextSubnetId++;
  }

  public NetElement createAnother () {
    return new SwitchConnector("switch"+num) ;
  }

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  @Override
  public Connection createConnection (Device dev) {
    return new EmulatedConnection("", this, dev);
  }

  public void readAttributes (Element xml) {
    super.readAttributes(xml);
  }

  public static Connector readFrom (Element x_con) {
    String name = x_con.getAttribute("id") ;
    SwitchConnector con = new SwitchConnector(name);
    con.readAttributes(x_con);
    return con ;
  }

    @Override
    public String getType() {
        return "switch" ;
    }

}

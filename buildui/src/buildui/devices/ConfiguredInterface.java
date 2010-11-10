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
import buildui.paint.PropertiesArea;
import java.applet.Applet;
import org.w3c.dom.Element;

public class ConfiguredInterface extends Interface {

  public ConfiguredInterface (String newName, Device dev, Connection con) {
    super(newName, dev, con);
    String ip = con.getInterfaceIpHint();
    if ( ip != null ) setProperty("ip4address", ip);
    else setProperty("use_dhcp", "true");
  }

  static PropertiesArea propertiesArea ;

  public static void init ( Applet parent ) {
    propertiesArea = new ConfiguredInterfacePropertiesArea();
  }

  @Override
  public PropertiesArea getPropertiesArea () {
    return propertiesArea ;
  }

  public void readAttributes (Element xml) {
    super.readAttributes(xml);
    setProperty("ip4address", xml.getAttribute("ip4address"));
    setProperty("use_dhcp", xml.getAttribute("use_dhcp").toLowerCase());
  }

}

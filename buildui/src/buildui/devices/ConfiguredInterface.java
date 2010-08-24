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
import buildui.paint.PropertiesArea;
import org.w3c.dom.Element;

public class ConfiguredInterface extends Interface {

  public ConfiguredInterface (String newName, Device dev, Connection con) {
    super(newName, dev, con);
  }

  static PropertiesArea propertiesArea = new ConfiguredInterfacePropertiesArea () ;

  @Override
  public PropertiesArea getPropertiesArea () {
    return propertiesArea ;
  }

  @Override
  public void writeAttributes(Element xml) {
    super.writeAttributes(xml);
    xml.setAttribute("ip4address", getProperty("ip", ""));
    xml.setAttribute("ip4netmask", getProperty("netmask", ""));
    xml.setAttribute("use_dhcp", getProperty("usedhcp", "true"));
  }

}

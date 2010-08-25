package buildui.devices;

import buildui.paint.PropertiesArea;
import buildui.paint.NetElement;

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
public class ConfiguredInterfacePropertiesArea extends PropertiesArea {

  public boolean iCare (NetElement t) {
    return (t instanceof Interface);
  }

  public String getName () {
    return "Interface properties";
  }

  public ConfiguredInterfacePropertiesArea () {
    super();
    addProperty("name", "name:", "", true, false);
    addProperty("usedhcp", "use dhcp:", "false", true, false);
    addProperty("ip", "ip:", "", false, false);
    addProperty("netmask", "netmask:", "", false, false);
  }
};

/* lanlink
delay/b/loss */

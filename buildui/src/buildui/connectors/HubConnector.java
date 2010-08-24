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

import buildui.paint.Element;
import java.awt.*;

import buildui.paint.IconElement;
import buildui.paint.PropertiesArea;

public class HubConnector extends IconElement {

  static Image icon;
  static int num = 1 ;

  public String getIconName () {
    return "/icons/hub.png";
  }

  public void drawIcon (Graphics g) {
    if (icon == null) icon = loadIcon();
    super.drawIcon(g, icon);
  }

  public HubConnector (String newName) {
    super(newName);
  }

  public Element createAnother () {
    return new HubConnector("hub"+(num++)) ;
  }

  static PropertiesArea propertiesArea = new HubPropertiesArea() ;

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

};

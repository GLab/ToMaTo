package buildui.paint;
/*
 * NEW CODE:
 *   Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
 *   This file is part of ToMaTo (Topology management software)
 *
 * OLD CODE:
 *   Copyright (c) 2002-2006 University of Utah and the Flux Group.
 *   All rights reserved.
 *   This file is part of the Emulab network testbed software.
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

import java.awt.*;
import java.awt.image.*;

import buildui.Netbuild;

// OLD CODE FROM HERE ON (owned by Emulab)

abstract public class IconElement extends NetElement implements ImageObserver {

  protected Image icon;

  protected Image loadIcon (String iconName) {
    return Netbuild.getImage(iconName);
  }

  @Override
  public void drawIcon (Graphics g) {
    try {
      int height = icon.getHeight(this);
      int width = icon.getWidth(this);
      if (icon != null) g.drawImage(icon, -width/2, -height/2, this);
    } catch (Exception e) {
      Netbuild.exception (e) ;
    }
  }

  @Override
  public int textDown() {
    return 12 + icon.getHeight(this)/2;
  }

  public IconElement (String newName, boolean displayName, String icon) {
    super(newName, displayName);
    this.icon = loadIcon(icon);
  }

  public boolean imageUpdate (Image img,
   int infoflags,
   int x, int y,
   int width, int height) {
    if (infoflags == ALLBITS) {
      Netbuild.redrawAll();
      return false;
    }
    return true;
  }
}

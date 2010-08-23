package buildui.paint;
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

import java.awt.*;
import java.awt.image.*;

import buildui.Netbuild;

abstract public class IconElement extends Element
 implements ImageObserver {

  abstract public String getIconName ();

  protected Image loadIcon () {
    Image i = Netbuild.getImage(getIconName());
    /*
    if (i != null) {
    System.out.println("loadIcon(): " + i.toString() );
    } else {
    System.out.println("loadIcon(): NULL" );
    }
     */
    return i;
    //return null;
  }

  public void drawIcon (Graphics g, Image icon) {
    /*g.setColor( Color.lightGray );
    g.fillRect( -12, -12, 32, 32 );
    g.setColor( Color.white );
    g.fillRect( -16, -16, 32, 32 );
    g.setColor( Color.black );
    g.drawRect( -16, -16, 32, 32 );
     */
    try {
      if (icon != null) g.drawImage(icon, -16, -16, this);
    } catch (Exception e) {
      System.out.println(e.getMessage());
      e.printStackTrace();
    }
  }

  public IconElement (String newName) {
    super(newName);
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
};

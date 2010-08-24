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

import java.awt.*;

import buildui.paint.Element;
import buildui.paint.PropertiesArea;

public class Connection extends Element {

  private Element a, b;
  private static Color paleGreen;

  static {
    paleGreen = new Color(0.8f, 1.0f, 0.8f);
  }

  public Element getA () {
    return a;
  }

  public Element getB () {
    return b;
  }

  public Connection (String newName, Element na, Element nb) {
    super(newName);
    linkable = false;
    moveable = false;
    a = na;
    b = nb;
    super.move((a.getX() + b.getX()) / 2,
     (a.getY() + b.getY()) / 2);
  }

  public void move (int nx, int ny) {
    // nope. can't allow this.
  }

  public void drawIcon (Graphics g) {
    g.setColor(Color.lightGray);
    g.fillRect(-6, -6, 16, 16);

    g.setColor(paleGreen);
    g.fillRect(-8, -8, 16, 16);

    g.setColor(Color.black);
    g.drawRect(-8, -8, 16, 16);
  }

  public int size () {
    return 10;
  }
  /*
  public boolean clicked( int cx, int cy ) {
  return (Math.abs(cx - getX()) < 10 && Math.abs(cy - getY()) < 9);
  }
   */

  public void draw (Graphics g) {
    super.move((a.getX() + b.getX()) / 2,
     (a.getY() + b.getY()) / 2);
    g.setColor(Color.darkGray);
    g.drawLine(a.getX(), a.getY(), b.getX(), b.getY());
    super.draw(g);
  }

  public Rectangle getRectangle () {
    if (0 == getName().compareTo(""))
      return new Rectangle(getX() - 12, getY() - 12, 26, 26);
    else
      return super.getRectangle();
  }

  public int textDown () {
    return 20;
  }

  public boolean isConnectedTo (Element t) {
    return (a == t | b == t);
  }

  static PropertiesArea propertiesArea = new ConnectionPropertiesArea() ;

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }
}

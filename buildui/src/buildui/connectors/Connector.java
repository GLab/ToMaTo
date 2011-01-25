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

import buildui.Modification;
import buildui.Netbuild;
import buildui.devices.Device;
import buildui.paint.IconElement;
import java.awt.Color;
import java.awt.Graphics;
import java.awt.Rectangle;
import java.util.HashSet;
import java.util.Set;
import org.w3c.dom.Element;

public abstract class Connector extends IconElement {

  private static Color blue = new Color(0.0f, 107.0f/256, 153.0f/256);

  public static Connector readFrom (Element x_con) {
    String type = x_con.getAttribute("type");
    if ( type.equals("special") ) return SpecialFeatureConnector.readFrom(x_con);
    if ( type.equals("hub") ) return HubConnector.readFrom(x_con);
    if ( type.equals("switch") ) return SwitchConnector.readFrom(x_con);
    if ( type.equals("router") ) return RouterConnector.readFrom(x_con);
    return null;
  }

  public static void init () {
    nextSubnetId = 1;
  }

  public Connector (String newName, String iconName) {
    super(newName, true, iconName);
    setProperty("type", getType());
  }

  public abstract String getType();

  public abstract Connection createConnection ( Device dev ) ;
  protected static int nextSubnetId = 1;

  private Set<Connection> connections = new HashSet<Connection> () ;
  protected int subnetId;

  protected int nextHostIp = 1 ;

  public Set<Connection> connections() {
    return connections ;
  }

  public void addConnection(Connection con) {
    connections.add(con);
    checkImplicit();
  }

  public void removeConnection(Connection con) {
    connections.remove(con);
    checkImplicit() ;
  }

  public void readAttributes (Element xml) {
    String pos = xml.getAttribute("pos");
    try {
      int x = Integer.parseInt(pos.split(",")[0]);
      int y = Integer.parseInt(pos.split(",")[1]);
      move(x,y);
    } catch ( NumberFormatException ex ) {}
  }

  public boolean isImplicit () {
    return connections.size() == 2;
  }

  private void moveToMiddle() {
    Connection[] cons = connections.toArray(new Connection[2]) ;
    int oldx = getX();
    int oldy = getY();
    int x = ( cons[0].getDevice().getX() + cons[1].getDevice().getX() ) / 2 ;
    int y = ( cons[0].getDevice().getY() + cons[1].getDevice().getY() ) / 2 ;
    if ( x == oldx && y == oldy ) return;
    super.move(x, y);
  }

  public void onConnectionMoved() {
    if ( ! isImplicit() ) return;
    moveToMiddle();
    onPropertyChanged("pos", "", getX()+","+getY());
  }

  public void checkImplicit () {
    moveable = !isImplicit() ;
    displayName = !isImplicit();
    if ( isImplicit() ) {
        onConnectionMoved();
        Netbuild.ensureNonOverlapping();
    }
  }

  @Override
  public void move(int x, int y) {
    if ( ! isImplicit() ) super.move(x, y);
    else moveToMiddle();
  }

  @Override
  public void drawIcon(Graphics g) {
    if ( isImplicit() ) {
      g.setColor(blue);
      g.fillRect(-6, -4, 12, 8);
      g.setColor(Color.black);
      g.drawRect(-6, -4, 12, 8);
    } else super.drawIcon(g);
  }

  @Override
  public Rectangle getRectangle() {
		if ( isImplicit() ) return new Rectangle(getX() + -6 - 4, getY() + -4 - 4, 12+8, 8+8);
    else return super.getRectangle() ;
	}

  @Override
  public void draw(Graphics g) {
    super.draw(g);
  }

  public void onNameChanged(String oldName, String newName) {
      Modification.add(Modification.ConnectorRename(oldName, newName));
  }

  public void onPropertyChanged(String property, String oldValue, String newValue) {
      Modification.add(Modification.ConnectorConfigure(this, property, newValue));
  }

}

package buildui.connectors;
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
import buildui.Modification;
import buildui.devices.Device;
import buildui.devices.Interface;
import java.awt.*;

import buildui.paint.NetElement;
import buildui.paint.PropertiesArea;
import java.applet.Applet;
import org.w3c.dom.Element;

// OLD CODE FROM HERE ON (owned by Emulab)

public class Connection extends NetElement {

  private Connector con;
  private Device dev;
  private Interface iface;
  protected int hostIp ;

  public Connector getConnector () {
    return con;
  }

  public Connection (String newName, Connector con, Device dev) {
    super(newName, true);
    linkable = false;
    moveable = false;
    this.con = con;
    this.dev = dev;
    this.hostIp = con.nextHostIp++;
    super.move((con.getX() + dev.getX()) / 2,
     (con.getY() + dev.getY()) / 2);
  }

  public void move (int nx, int ny) {
    // nope. can't allow this.
  }

  public void drawIcon (Graphics g) {
    g.setColor(Color.lightGray);
    g.fillRect(-6, -6, 16, 16);

    g.setColor(Color.gray);
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
    super.move((con.getX() + dev.getX()) / 2,
     (con.getY() + dev.getY()) / 2);
    g.setColor(Color.darkGray);
    g.drawLine(con.getX(), con.getY(), dev.getX(), dev.getY());
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

// NEW CODE FROM HERE ON (owned by University of Kaiserslautern)
  
  public boolean isConnectedTo (NetElement t) {
    return (con == t | dev == t);
  }

  static PropertiesArea propertiesArea;

  public static void init ( Applet parent ) {
    propertiesArea = new ConnectionPropertiesArea();
  }


  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  public void writeAttributes(Element xml) {
    //nothing to do
  }

  public void readAttributes (Element xml) {
    //nothing to do
  }

  /**
   * @return the iface
   */
  public Interface getIface () {
    return iface;
  }

  /**
   * @param iface the iface to set
   */
  public void setIface (Interface iface) {
    this.iface = iface;
  }

  public String getInterfaceIpHint () {
    return null ;
  }

  /**
   * @return the dev
   */
  public Device getDevice () {
    return dev;
  }

  public void onNameChanged(String oldName, String newName) {
      //impossible, connections do not have names
  }

  public void onPropertyChanged(String property, String oldValue, String newValue) {
      Modification.add(Modification.ConnectionConfigure(this, property, newValue));
  }

}

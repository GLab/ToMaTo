package buildui;
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
import java.io.IOException;
import java.util.*;

import buildui.connectors.Connection;
import buildui.connectors.Connector;
import buildui.devices.Device;
import buildui.devices.Interface;
import buildui.paint.NetElement;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

// OLD CODE FROM HERE ON (owned by Emulab)

// Code for the "workarea" of the applet,
// which contains the node graph.
// Contains code to add/remove/select/draw "Thingees".
//
// A lot of this code deals with loading and saving the
// work area as NS, and could probably be in a separate class.
//
public class WorkArea {

  private Set<Device> devices = new HashSet<Device>() ;
  public Set<Device> getDevices() {
	return devices;
  }

  private Set<Connector> connectors = new HashSet<Connector>() ;
  public TopologyPropertiesArea topologyProperties = new TopologyPropertiesArea();

  private void selectOneInRectangle (Rectangle r, NetElement t, boolean xor) {
    int xDiff = t.getX() - r.x;
    int yDiff = t.getY() - r.y;
    if (xDiff > 0 && xDiff < r.width && yDiff > 0 && yDiff < r.height)
      if (!xor || !t.isSelected())
        t.select();
      else
        t.deselect();
  }

// NEW CODE FROM HERE ON (owned by University of Kaiserslautern)

  public void selectRectangle (Rectangle r, boolean xor) {
    for (Device dev: devices) {
      selectOneInRectangle(r, dev, xor);
      for (Interface iface: dev.interfaces()) selectOneInRectangle(r, iface, xor);
    }
    for (Connector con: connectors) {
      selectOneInRectangle(r, con, xor);
      for (Connection c: con.connections()) selectOneInRectangle(r, c, xor);
    }
  }

  public int getElementCount () {
    return devices.size() + connectors.size();
  }

  public void paint (Graphics g) {
    for (Connector con: connectors) {
      con.checkImplicit();
      for (Connection c: con.connections()) c.draw(g);
      con.draw(g);
    }
    for (Device dev: devices) {
      dev.draw(g);
      for (Interface iface: dev.interfaces()) iface.draw(g);
    }
  }

  public NetElement clicked (int x, int y) {
    for (Device dev: devices) {
      for (Interface iface: dev.interfaces()) if (iface.clicked(x, y)) return iface;
      if (dev.clicked(x, y)) return dev;
    }
    for (Connector con: connectors) {
      for (Connection c: con.connections()) if(c.clicked(x, y)) return c;
      if (con.clicked(x, y)) return con;
    }
    return null ;
  }

  public void remove (NetElement t) {
    if (t instanceof Device) {
      devices.remove((Device)t);
      for (Interface iface: new HashSet<Interface>(((Device)t).interfaces())) remove(iface);
      Modification.add(Modification.DeviceDelete((Device)t));
    } else if (t instanceof Connector) {
      connectors.remove((Connector)t);
      for (Connection c: new HashSet<Connection>(((Connector)t).connections())) remove(c);
      Modification.add(Modification.ConnectorDelete((Connector)t));
    } else if (t instanceof Interface) {
      ((Interface)t).getDevice().removeInterface((Interface)t);
      Connection c = ((Interface)t).getCon();
      if ( c != null ) {
        Modification.add(Modification.ConnectionDelete(c));
        c.setIface(null);
        remove(c);
      }
      Modification.add(Modification.InterfaceDelete((Interface)t));
    } else if (t instanceof Connection) {
      ((Connection)t).getConnector().removeConnection((Connection)t);
      Interface iface = ((Connection)t).getIface();
      if (iface != null) {
        iface.setCon(null);
        remove(iface);
      }
    }
  }

  public void add (NetElement t) {
    if (t instanceof Device) {
      devices.add((Device)t);
      Modification.add(Modification.DeviceCreate((Device)t));
    } else if (t instanceof Connector) {
      connectors.add((Connector)t);
      Modification.add(Modification.ConnectorCreate((Connector)t));
    } else if (t instanceof Interface) {
      ((Interface)t).getDevice().addInterface((Interface)t);
      Modification.add(Modification.InterfaceCreate((Interface)t));
    } else if (t instanceof Connection) {
      ((Connection)t).getConnector().addConnection((Connection)t);
      Modification.add(Modification.ConnectionCreate((Connection)t));
    }
  }

  public void decode (InputStream in) {
    try {
      Hashtable<String, Device> deviceMap = new Hashtable<String, Device> ();
      DocumentBuilderFactory dbfac = DocumentBuilderFactory.newInstance();
      DocumentBuilder docBuilder = dbfac.newDocumentBuilder();
      Document doc = docBuilder.parse(in);
      Element topology = (Element)doc.getElementsByTagName("topology").item(0);
      topologyProperties.setNameValue(topology.getAttribute("name"));
      NodeList x_devices = topology.getElementsByTagName("device");
      for (int i = 0; i < x_devices.getLength(); i++) {
        Element x_dev = (Element)x_devices.item(i);
        Device dev = Device.readFrom(x_dev);
        add(dev);
        deviceMap.put(dev.getName(), dev);
      }
      Hashtable<String, Connection> connectionMap = new Hashtable<String, Connection> ();
      NodeList x_connectors = topology.getElementsByTagName("connector");
      for (int i = 0; i < x_connectors.getLength(); i++) {
        Element x_con = (Element)x_connectors.item(i);
        Connector con = Connector.readFrom(x_con);
        add(con);
        NodeList connections = x_con.getElementsByTagName("connection");
        for (int j = 0; j < connections.getLength(); j++) {
          Element x_c = (Element)connections.item(j);
          String devName = x_c.getAttribute("device");
          String ifName = x_c.getAttribute("interface");
          Device dev = deviceMap.get(devName);
          Connection c = con.createConnection(dev);
          c.readAttributes(x_c);
          connectionMap.put(devName+"."+ifName, c);
        }
      }
      for (int i = 0; i < x_devices.getLength(); i++) {
        Element x_dev = (Element)x_devices.item(i);
        String devName = x_dev.getAttribute("id");
        Device dev = deviceMap.get(devName);
        NodeList interfaces = x_dev.getElementsByTagName("interface");
        for (int j = 0; j < interfaces.getLength(); j++) {
          Element x_iface = (Element)interfaces.item(j);
          String ifName = x_iface.getAttribute("id");
          Connection c = connectionMap.get(dev.getName()+"."+ifName);
          if (c!=null) {
            Interface iface = dev.createInterface(ifName, c);
            c.setIface(iface);
            iface.readAttributes(x_iface);
            add(iface);
            add(c);
          }
        }
      }
      Modification.clear();
    } catch (SAXException ex) {
      Netbuild.exception (ex) ;
      Logger.getLogger(WorkArea.class.getName()).log(Level.SEVERE, null, ex);
    } catch (IOException ex) {
      Netbuild.exception (ex) ;
      Logger.getLogger(WorkArea.class.getName()).log(Level.SEVERE, null, ex);
    } catch (ParserConfigurationException ex) {
      Netbuild.exception (ex) ;
      Logger.getLogger(WorkArea.class.getName()).log(Level.SEVERE, null, ex);
    }

  }

}

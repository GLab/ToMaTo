package buildui;
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

// Code for the "workarea" of the applet,
// which contains the node graph.
// Contains code to add/remove/select/draw "Thingees".
//
// A lot of this code deals with loading and saving the
// work area as NS, and could probably be in a separate class.
//
public class WorkArea {

  private Vector<NetElement> elements;
  private Vector<Connection> connectionElements;
  private Vector<Interface> interfaceElements;

  public WorkArea (int w, int h) {
    super();
    elements = new Vector<NetElement>();
    connectionElements = new Vector<Connection>();
    interfaceElements = new Vector<Interface>();
  }

  private void selectOneInRectangle (Rectangle r, NetElement t, boolean xor) {
    int xDiff = t.getX() - r.x;
    int yDiff = t.getY() - r.y;
    if (xDiff > 0 && xDiff < r.width && yDiff > 0 && yDiff < r.height)
      if (!xor || !t.isSelected())
        t.select();
      else
        t.deselect();
  }

  public void selectRectangle (Rectangle r, boolean xor) {
    Enumeration linkThingeeEnum = connectionElements.elements();

    while (linkThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)linkThingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }

    Enumeration thingeeEnum = elements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }

    Enumeration iFaceThingeeEnum = interfaceElements.elements();

    while (iFaceThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)iFaceThingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }
  }

  public int getElementCount () {
    return connectionElements.size() + elements.size() + interfaceElements.size();
  }

  public void paint (Graphics g) {
    Enumeration linkThingeeEnum = connectionElements.elements();

    while (linkThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)linkThingeeEnum.nextElement();
      t.draw(g);
    }

    Enumeration thingeeEnum = elements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      t.draw(g);
    }

    Enumeration iFaceThingeeEnum = interfaceElements.elements();

    while (iFaceThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)iFaceThingeeEnum.nextElement();
      t.draw(g);
    }
  }

  public NetElement clicked (int x, int y) {
    Enumeration thingeeEnum;

    NetElement got = null;

    thingeeEnum = connectionElements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    thingeeEnum = elements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    thingeeEnum = interfaceElements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    return got;
  }

  public void remove (NetElement t) {
    if (t instanceof Interface)
      interfaceElements.removeElement(t);
    else if (t instanceof Connection) {
      boolean done = false;
      while (!done) {
        done = true;
        Enumeration e = interfaceElements.elements();
        while (e.hasMoreElements() && done) {
          Interface i = (Interface)e.nextElement();
          if (i.isConnectedTo(t)) {
            remove(i);
            done = false;
          }
        }
      }
      connectionElements.removeElement(t);
    } else {
      boolean done = false; // stupid hack.
      while (!done) {
        done = true;
        Enumeration thingeeEnum = connectionElements.elements();
        while (thingeeEnum.hasMoreElements() && done) {
          Connection u = (Connection)thingeeEnum.nextElement();
          if (u.isConnectedTo(t)) {
            remove(u);
            done = false;
          }
        }
      }
      elements.removeElement(t);
    }
  }

  public void add (NetElement t) {
    if (t instanceof Connection)
      connectionElements.addElement((Connection)t);
    else if (t instanceof Interface)
      interfaceElements.addElement((Interface)t);
    else
      elements.addElement(t);
  }

  public void encode (OutputStream out) {
    try {
      DocumentBuilderFactory dbfac = DocumentBuilderFactory.newInstance();
      DocumentBuilder docBuilder = dbfac.newDocumentBuilder();
      Document doc = docBuilder.newDocument();
      Element root = doc.createElement("topology");
      doc.appendChild(root);
      Element devices = doc.createElement("devices");
      root.appendChild(devices);
      Element connectors = doc.createElement("connectors");
      root.appendChild(connectors);
      for ( NetElement el: elements) {
        if ( el instanceof Device ) {
          Element x_dev = doc.createElement("device") ;
          ((Device)el).writeAttributes(x_dev);
          for ( Interface iface: interfaceElements ) {
            if ( iface.getDevice() == el ) {
              Element x_iface = doc.createElement("interface") ;
              iface.writeAttributes(x_iface);
              x_dev.appendChild(x_iface);
            }
          }
          devices.appendChild(x_dev);
        } else if ( el instanceof Connector ) {
          Element x_con = doc.createElement("connector") ;
          ((Connector)el).writeAttributes(x_con);
          for ( Connection con: connectionElements ) {
            if ( con.getConnector() == el ) {
              Element x_c = doc.createElement("connection") ;
              con.writeAttributes(x_c);
              for ( Interface iface: interfaceElements ) {
                if ( iface.getConnection() == con ) {
                  x_c.setAttribute("device", iface.getDevice().getName());
                  x_c.setAttribute("interface", iface.getName());
                  break;
                }
              }
              x_con.appendChild(x_c);
            }
          }
          connectors.appendChild(x_con);
        }
      }
      TransformerFactory transfac = TransformerFactory.newInstance();
      Transformer trans = transfac.newTransformer();
      trans.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "yes");
      trans.setOutputProperty(OutputKeys.INDENT, "yes");
      StreamResult result = new StreamResult(out);
      DOMSource source = new DOMSource(doc);
      trans.transform(source, result);
    } catch (TransformerException ex) {
      Netbuild.exception (ex) ;
      Logger.getLogger(WorkArea.class.getName()).log(Level.SEVERE, null, ex);
    } catch (ParserConfigurationException ex) {
      Netbuild.exception (ex) ;
      Logger.getLogger(Netbuild.class.getName()).log(Level.SEVERE, null, ex);
    }
  }

  public void decode (InputStream in) {
    try {
      Hashtable<String, Device> deviceMap = new Hashtable<String, Device> ();
      DocumentBuilderFactory dbfac = DocumentBuilderFactory.newInstance();
      DocumentBuilder docBuilder = dbfac.newDocumentBuilder();
      Document doc = docBuilder.parse(in);
      Element topology = (Element)doc.getElementsByTagName("topology").item(0);
      NodeList devices = topology.getElementsByTagName("device");
      for (int i = 0; i < devices.getLength(); i++) {
        Element x_dev = (Element)devices.item(i);
        Device dev = Device.readFrom(x_dev);
        add(dev);
        deviceMap.put(dev.getName(), dev);
      }
      Hashtable<String, Connection> connectionMap = new Hashtable<String, Connection> ();
      NodeList connectors = topology.getElementsByTagName("connector");
      for (int i = 0; i < connectors.getLength(); i++) {
        Element x_con = (Element)connectors.item(i);
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
          add(c);
          connectionMap.put(devName+"."+ifName, c);
          System.out.println("adding " + devName+"."+ifName);
        }
      }
      for (int i = 0; i < devices.getLength(); i++) {
        Element x_dev = (Element)devices.item(i);
        String devName = x_dev.getAttribute("id");
        Device dev = deviceMap.get(devName);
        NodeList interfaces = x_dev.getElementsByTagName("interface");
        for (int j = 0; j < interfaces.getLength(); j++) {
          Element x_iface = (Element)interfaces.item(j);
          String ifName = x_iface.getAttribute("id");
          System.out.println("searching " + devName+"."+ifName);
          Connection c = connectionMap.get(dev.getName()+"."+ifName);
          Interface iface = dev.createInterface(ifName, c);
          iface.readAttributes(x_iface);
          add(iface);
        }
      }
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

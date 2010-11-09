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

package buildui;

import buildui.connectors.Connection;
import buildui.connectors.Connector;
import buildui.devices.Device;
import buildui.devices.Interface;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
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

public class Modification {

    public enum Type {
        TopologyRename("topology-rename"),
        DeviceCreate("device-create"),
        DeviceConfigure("device-configure"),
        DeviceRename("device-rename"),
        DeviceDelete("device-delete"),
        InterfaceCreate("interface-create"),
        InterfaceConfigure("interface-configure"),
        InterfaceRename("interface-rename"),
        InterfaceDelete("interface-delete"),
        ConnectorCreate("connector-create"),
        ConnectorConfigure("connector-configure"),
        ConnectorRename("connector-rename"),
        ConnectorDelete("connector-delete"),
        ConnectionCreate("connection-create"),
        ConnectionConfigure("connection-configure"),
        ConnectionDelete("connection-delete");

        private String rep;
        Type (String rep) {
            this.rep = rep;
        }
        public String getRep() {
            return rep;
        }
    }

    public Type type ;
    private String element, subelement;
    private Map<String,String> parameters = new HashMap<String, String> ();

    private Modification ( Type type, String element, String subelement, String... parameters) {
        this.type = type ;
        this.element = element;
        this.subelement = subelement;
        int i = 0;
        while ( i < parameters.length ) {
            String name = parameters[i++];
            String value = parameters[i++];
            if ( value.equals("<auto>") ) value = "*" ;
            this.parameters.put(name, value);
        }
    }

    private Modification ( Type type, String element, String subelement, Map<String,String> parameters, String... parameters2) {
        this.type = type ;
        this.element = element;
        this.subelement = subelement;
        for ( Entry<String,String> entr: parameters.entrySet() ) {
            String key = entr.getKey();
            String value = entr.getValue();
            if ( value.equals("<auto>") ) value = "*";
            this.parameters.put(key, value);
        }
        int i = 0;
        while ( i < parameters2.length ) {
            String name = parameters2[i++];
            String value = parameters2[i++];
            if ( value.equals("<auto>") ) value = "*" ;
            this.parameters.put(name, value);
        }
    }

    private static ArrayList<Modification> modifications = new ArrayList<Modification> ();

    public static void add (Modification mod) {
        modifications.add(mod);
        System.out.println(mod);
    }
    
    public static List<Modification> list() {
        return modifications ;
    }

    public static void clear() {
        modifications.clear();
    }

    public String toString() {
        return type + " " + element + " " + subelement + " (" + parameters + ")";
    }

    public static Modification TopologyRename ( String name ) {
        return new Modification(Type.TopologyRename, null, null, "name", name);
    }

    public static Modification DeviceCreate ( Device dev ) {
        return new Modification(Type.DeviceCreate, null, null, dev.getProperties(), "name", dev.getName());
    }

    public static Modification DeviceConfigure ( Device dev, String property, String value) {
        return new Modification(Type.DeviceConfigure, dev.getName(), null, property, value);
    }

    public static Modification DeviceRename ( String oldname, String newname ) {
        return new Modification(Type.DeviceRename, oldname, null, "name", newname);
    }

    public static Modification DeviceDelete ( Device dev ) {
        return new Modification(Type.DeviceDelete, dev.getName(), null);
    }

    public static Modification InterfaceCreate ( Interface iface ) {
        return new Modification(Type.InterfaceCreate, iface.getDevice().getName(), null, iface.getProperties(), "name", iface.getName());
    }

    public static Modification InterfaceConfigure ( Interface iface, String property, String value) {
        return new Modification(Type.InterfaceConfigure, iface.getDevice().getName(), iface.getName(), property, value);
    }

    public static Modification InterfaceRename ( Interface iface, String oldname, String newname ) {
        return new Modification(Type.InterfaceRename, iface.getDevice().getName(), oldname, "name", newname);
    }

    public static Modification InterfaceDelete ( Interface iface ) {
        return new Modification(Type.InterfaceDelete, iface.getDevice().getName(), iface.getName());
    }

    public static Modification ConnectorCreate ( Connector con ) {
        return new Modification(Type.ConnectorCreate, null, null, con.getProperties(), "name", con.getName());
    }

    public static Modification ConnectorConfigure ( Connector con, String property, String value) {
        return new Modification(Type.ConnectorConfigure, con.getName(), null, property, value);
    }

    public static Modification ConnectorRename ( String oldname, String newname ) {
        return new Modification(Type.ConnectorRename, oldname, null, "name", newname);
    }

    public static Modification ConnectorDelete ( Connector con ) {
        return new Modification(Type.ConnectorDelete, con.getName(), null);
    }

    public static Modification ConnectionCreate ( Connection con ) {
        return new Modification(Type.ConnectionCreate, con.getConnector().getName(), null, con.getProperties(), "interface", con.getDevice().getName()+"."+con.getIface().getName());
    }

    public static Modification ConnectionConfigure ( Connection con, String property, String value) {
        return new Modification(Type.ConnectionConfigure, con.getName(), null, property, value);
    }

    public static Modification ConnectionDelete ( Connection con ) {
        return new Modification(Type.ConnectionDelete, con.getConnector().getName(), con.getDevice().getName()+"."+con.getIface().getName());
    }

    public static void encodeModifications (OutputStream out) {
        try {
          DocumentBuilderFactory dbfac = DocumentBuilderFactory.newInstance();
          DocumentBuilder docBuilder = dbfac.newDocumentBuilder();
          Document doc = docBuilder.newDocument();
          Element root = doc.createElement("modifications");
          doc.appendChild(root);
          for ( Modification mod: modifications ) {
            Element x_mod = doc.createElement("modification");
            root.appendChild(x_mod);
            x_mod.setAttribute("type", mod.type.getRep());
            if ( mod.element != null ) x_mod.setAttribute("element", mod.element);
            if ( mod.subelement != null ) x_mod.setAttribute("subelement", mod.subelement);
            if ( ! mod.parameters.isEmpty() ) {
                Element x_prop = doc.createElement("properties");
                x_mod.appendChild(x_prop);
                for ( Entry<String, String> entr: mod.parameters.entrySet() )
                    x_prop.setAttribute(entr.getKey(), entr.getValue());
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

}

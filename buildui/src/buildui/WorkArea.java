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
import java.util.*;
import java.lang.*;

import buildui.connectors.EmulatedConnection;
import buildui.connectors.InternetConnector;
import buildui.connectors.Connection;
import buildui.devices.Interface;
import buildui.devices.KvmDevice;
import buildui.paint.Element;

// Code for the "workarea" of the applet,
// which contains the node graph.
// Contains code to add/remove/select/draw "Thingees".
//
// A lot of this code deals with loading and saving the
// work area as NS, and could probably be in a separate class.
//
public class WorkArea {

  private Vector thingees;
  private Vector linkThingees;
  private Vector iFaceThingees;
  private int width;
  private int height;

  public WorkArea (int w, int h) {
    super();
    thingees = new Vector();
    linkThingees = new Vector();
    iFaceThingees = new Vector();
    width = w;
    height = h;
    //Element foo = new Element( "Some Node" );
    //foo.move( 100, 100 );
    //thingees.addElement( foo  );
  }

  /*
  private Element lookupNodeThingee (String name) {
    Enumeration thingeeEnum = thingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      if (t.getName().equals(name) && (t instanceof KvmDevice))
        return t;
    }

    return null;
  }
*/
  private Element lookupLanThingee (String name) {
    Enumeration thingeeEnum = thingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      if (t.getName().equals(name) && (t instanceof InternetConnector))
        return t;
    }

    return null;
  }

  private Element lookupLinkThingee (String name) {
    Enumeration thingeeEnum = linkThingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      if (t.getName().equals(name))
        return t;
    }

    return null;
  }

  /*
  private Element findInterface (String nodeName,
   Element linkOrLan) {
    Element node = lookupNodeThingee(nodeName);
    if (node == null) return null;

    Enumeration thingeeEnum = iFaceThingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Interface t = (Interface)thingeeEnum.nextElement();
      if (t.isConnectedTo(node) && t.isConnectedTo(linkOrLan))
        return t;
    }

    return null;
  }
*/
  /*
  private Element findLanLink (String nodeName,
   String lanName) {
    Element node = lookupNodeThingee(nodeName);
    Element lan = lookupLanThingee(lanName);
    if (node == null || lan == null) return null;

    Enumeration thingeeEnum = linkThingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Connection t = (Connection)thingeeEnum.nextElement();
      if (t.isConnectedTo(node) && t.isConnectedTo(lan))
        return t;
    }

    return null;
  }
*/
  private boolean doNSCreateNode (String name) {
    Element foo = new KvmDevice(name);
    foo.move(100 + thingees.size(), 100 + thingees.size());
    foo.fixName(true);
    add(foo);
    return true;
  }
/*
  private boolean doNSCreateLink (String name, String a, String b) {
    Element aNode = lookupNodeThingee(a);
    Element bNode = lookupNodeThingee(b);
    if (aNode == null || bNode == null) {
      System.out.println("doNSCreateLink(" + a + ", " + b + ") failed.");
      return false;
    }
    Element foo = new Connection(name, aNode, bNode);
    foo.fixName(true);
    add(foo);
    return true;
  }
*/
  /*
  private boolean doNSCreateLan (String name, Vector nodes, int first, int count) {
    Element foo = new InternetConnector(name);
    foo.move(120 + thingees.size(), 120 + thingees.size());
    foo.fixName(true);
    add(foo);
    // add individual lan members
    for (int i = 0; i != count; i++) {
      Element bar = lookupNodeThingee((String)(nodes.elementAt(first + i)));
      if (bar == null) {
        System.out.println("doNSCreateLan(" + name + ",...) failed.");
        return false;
      }
      add(new EmulatedConnection("", foo, bar));
    }
    return true;
  }
*/
  private boolean doNSSetLinkProp (String linkName, String prop, String val) {
    Element foo = lookupLinkThingee(linkName);
    if (foo == null) {
      System.out.println("doNSSetLinkProp(" + linkName + ", " + prop + ", " + val + ") failed.");
      return false;
    }
    foo.setProperty(prop, val);
    return true;
  }

  private boolean doNSSetLanProp (String lanName, String prop, String val) {
    Element foo = lookupLanThingee(lanName);
    if (foo == null) {
      System.out.println("doNSSetLanProp(" + lanName + ", " + prop + ", " + val + ") failed.");
      return false;
    }
    foo.setProperty(prop, val);
    return true;
  }
/*
  private boolean doNSSetNodeProp (String nodeName, String prop, String val) {
    Element foo = lookupNodeThingee(nodeName);
    if (foo == null) {
      System.out.println("doNSSetNodeProp(" + nodeName + ", " + prop + ", " + val + ") failed.");
      return false;
    }
    foo.setProperty(prop, val);
    return true;
  }
*/
  /*
  private boolean doNSSetIFaceProp (String nodeName, String linkName,
   String prop, String val) {
    Element link = lookupLinkThingee(linkName);
    if (link == null) {
      System.out.println("doNSSetIFaceProp(" + nodeName + ", " + linkName + " ," + prop + ", " + val + ") failed.");
      return false;
    }
    Element iFace = findInterface(nodeName, link);
    if (iFace == null) {
      System.out.println("doNSSetIFaceProp(" + nodeName + ", " + linkName + " ," + prop + ", " + val + ") failed.");
      return false;
    }
    iFace.setProperty(prop, val);
    return true;
  }

  private boolean doNSSetLanIFaceProp (String nodeName, String lanName,
   String prop, String val) {
    Element lanLink = findLanLink(nodeName, lanName);
    if (lanLink == null) {
      System.out.println("doNSSetLanIFaceProp(" + nodeName + ", " + lanName + " ," + prop + ", " + val + ") failed.");
      return false;
    }
    // find iface between node and lanLink
    Element lanIFace = findInterface(nodeName, lanLink);
    if (lanIFace == null) {
      System.out.println("doNSSetLanIFaceProp(" + nodeName + ", " + lanName + " ," + prop + ", " + val + ") failed.");
      return false;
    }
    lanIFace.setProperty(prop, val);
    return true;
  }

  private boolean doNSSetLanLinkProp (String nodeName, String lanName,
   String prop, String val) {
    Element lanLink = findLanLink(nodeName, lanName);
    if (lanLink == null) {
      System.out.println("doNSSetLanLinkProp(" + nodeName + ", " + lanName + " ," + prop + ", " + val + ") failed.");
      return false;
    }
    lanLink.setProperty(prop, val);
    return true;
  }
*/
  private boolean doNSSetVisPosition (String name, String x, String y) {
    Enumeration thingeeEnum = thingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      if (t.getName().equals(name)) {
        t.move((new Integer(x)).intValue(),
         (new Integer(y)).intValue());
        return true;
      }
    }

    return false;
  }

  private String getNumPre (String i) {
    int validChars = 0;
    while (true) {
      if (validChars == i.length()) break;
      char x = i.charAt(validChars);
      if (!((x >= '0' && x <= '9') || (x == '.')))
        break;
      validChars++;
    }
    return i.substring(0, validChars);
  }

  /*
  private boolean doNSCommand (Vector arglist) {
    int siz = arglist.size();
    String command = siz <= 0 ? null : (String)arglist.elementAt(0);
    String arg1 = siz <= 1 ? null : (String)arglist.elementAt(1);
    String arg2 = siz <= 2 ? null : (String)arglist.elementAt(2);
    String arg3 = siz <= 3 ? null : (String)arglist.elementAt(3);
    String arg4 = siz <= 4 ? null : (String)arglist.elementAt(4);
    String arg5 = siz <= 5 ? null : (String)arglist.elementAt(5);
    String arg6 = siz <= 6 ? null : (String)arglist.elementAt(6);
    String arg7 = siz <= 7 ? null : (String)arglist.elementAt(7);

    Element t;

    //System.out.println("doNSCommand(\""+command+"\")");

    if (command.equalsIgnoreCase("ns") || command.equalsIgnoreCase("source"))
      // totally ignore "$ns ..." and "source ..." forms.
      return true;

    if (command.equalsIgnoreCase("set")) {
      if (arg1.equalsIgnoreCase("ns") && arg2.equalsIgnoreCase("new") && arg3.equalsIgnoreCase("simulator"))
        // this is boilerplate and is therefore ignored.
        return true;

      if (!arg2.equalsIgnoreCase("ns")) {
        System.out.println("doNSCommand: invalid 'set'.");
        return false;
      }

      if (arg3.equalsIgnoreCase("node"))
        // !!! create node named arg1
        return doNSCreateNode(arg1);
      else if (arg3.equalsIgnoreCase("duplex-link"))
        return doNSCreateLink(arg1, arg4, arg5) && doNSSetLinkProp(arg1, "bandwidth", getNumPre(arg6)) && doNSSetLinkProp(
         arg1, "latency", getNumPre(arg7));
      else if (arg3.equalsIgnoreCase("make-lan"))
        // create lan named arg1 from arg4....arglast-2, bw arglast-1, lat arglast
        return doNSCreateLan(arg1, arglist, 4, arglist.size() - 2 - 4) && doNSSetLanProp(arg1, "bandwidth", getNumPre((String)arglist.
         elementAt(arglist.size() - 2))) && doNSSetLanProp(arg1, "latency", getNumPre((String)arglist.elementAt(arglist.
         size() - 1)));
    } else if (command.equalsIgnoreCase("tb-set-node-os"))
      return doNSSetNodeProp(arg1, "osid", arg2);
    else if (command.equalsIgnoreCase("tb-set-hardware"))
      return doNSSetNodeProp(arg1, "hardware", arg2);
    else if (command.equalsIgnoreCase("tb-set-link-loss"))
      return doNSSetLinkProp(arg1, "loss", arg2);
    else if (command.equalsIgnoreCase("tb-set-ip-link"))
      return doNSSetIFaceProp(arg1, arg2, "ip", arg3);
    else if (command.equalsIgnoreCase("tb-set-lan-loss"))
      return doNSSetLanProp(arg1, "loss", arg2);
    else if (command.equalsIgnoreCase("tb-set-node-lan-params"))
      return doNSSetLanLinkProp(arg1, arg2, "latency", getNumPre(arg3)) && doNSSetLanLinkProp(arg1, arg2, "bandwidth", getNumPre(
       arg4)) && doNSSetLanLinkProp(arg1, arg2, "loss", arg5);
    else if (command.equalsIgnoreCase("tb-set-ip-lan"))
      return doNSSetLanIFaceProp(arg1, arg2, "ip", arg3);
    else if (command.equalsIgnoreCase("tb-set-vis-position"))
      return doNSSetVisPosition(arg1, arg2, arg3);

    System.out.println("doNSCommand(): Unknown command '" + command + "'\n");
    return false;
  }

  // loop by line
  // eat comments
  // set {N} [$ns node]
  //   set os, hardware to <auto>
  // tb-set-node-os ${N} {OS}
  // tb-set-hardware ${N} {HW}
  // set {NODELINK} [$ns duplex-link ${A} ${B} {bw}Mb {lat}ms DropTail]
  //   set link loss 0
  // tb-set-link-loss ${LINK} {loss}
  // tb-set-ip-link ${N} ${L} {IP}
  // set {LAN} [$ns make-lan "${1} ${2} " {BW}Mb {lat}ms]
  // tb-set-lan-loss ${LAN} {loss}
  // tb-set-node-lan-params ${N} ${L} {lat}ms {bw}Mb {loss}
  // tb-set-ip-lan ${N} ${L} {IP}
  // "$ns rtproto Static"
  // "$ns run"
  private boolean isTerminatorEOLEOS (String s, int pos) {
    if (pos >= s.length()) return true;
    char v = s.charAt(pos);
    // yup; as far as my parser is concerned, these are all whitespace.
    if (v == '#' || v == '\n' || v == '\t' || v == '\r' || v == ' ' || v == '[' || v == '"' || v == ']' || v == '$')
      return true;
    return false;
  }

  private boolean isEOLEOS (String s, int pos) {
    return pos >= s.length() || s.charAt(pos) == '\n';
  }

  private boolean isEOS (String s, int pos) {
    return pos >= s.length();
  }

  public boolean fromNS (String ns) {
    Vector arglist = new Vector();
    String newarg = new String();
    boolean commentBit = false;
    int pos = 0;

    while (true) {
      if (!isTerminatorEOLEOS(ns, pos)) {
        // if '#' wasn't already encountered this line,
        // append char under head to string.
        if (!commentBit)
          newarg = newarg.concat((new Character(ns.charAt(pos))).toString());
      } else {
        // At EOS, EOL, or Terminator, current arg ends.
        if (newarg.length() != 0) {
          arglist.addElement(newarg);
          newarg = new String();
        }

        // At EOL or EOS, run command and end comment.
        if (isEOLEOS(ns, pos)) {
          commentBit = false;
          if (!arglist.isEmpty()) {
            // if there is an error, propagate it.
            if (!doNSCommand(arglist)) {
              System.out.println("NS Error, command \"" + (String)arglist.elementAt(0) + "\".");
              return false;
            }
            // Clear it, but clear isn't in Java 1.1
            arglist = new Vector();
          }
        } else
          // At '#', begin comment.
          if (ns.charAt(pos) == '#')
            commentBit = true;
      }
      pos++;
    }
  }
*/
  public String toNS () {
    Dictionary lanConnections = new Hashtable();
    String r = "";

    r += "#generated by Netbuild 1.03\n";
    r += "set ns [new Simulator]\n";
    r += "source tb_compat.tcl\n\n";

    Enumeration e;

    String s;
    String n;

    Dictionary names;

    boolean good = false;
    while (!good) {
      names = new Hashtable();
      good = true;
      e = thingees.elements();
      while (good && e.hasMoreElements()) {
        Element t = (Element)e.nextElement();
        if (t.getName().compareTo("") == 0) {
          good = false;
          // t += "# WARNING! Changed name for
          t.setName(t.genName("gen_name_"));
          Netbuild.setStatus("!Duplicate and/or blank names were changed.");
        } else if (names.get(t.getName()) != null) {
          good = false;
          t.setName(t.genName(t.getName()));
          Netbuild.redrawAll();
          Netbuild.setStatus("!Duplicate and/or blank names were changed.");
        } else
          names.put(t.getName(), t);
      }
    }


    e = thingees.elements();
    while (e.hasMoreElements()) {
      Element t = (Element)e.nextElement();
      if (t instanceof KvmDevice) {
        n = t.getName();
        r += "set " + n + " [$ns node]\n";
        s = t.getProperty("osid", "");
        if (0 != s.compareTo("<auto>") && 0 != s.compareTo(""))
          r += "tb-set-node-os $" + n + " " + s + "\n";
        s = t.getProperty("hardware", "");
        if (0 != s.compareTo("<auto>") && 0 != s.compareTo(""))
          r += "tb-set-hardware $" + n + " " + s + "\n";
        // Hack! This should be done in the ns parser.
        // Should match on "ixp*".
        if (0 == s.compareTo("ixp-bv")) {
          r += "# Create a host for the ixp and associate them.\n";
          r += "set " + n + "host" + " [$ns node]\n";
          r += "tb-bind-parent $" + n + " $" + n + "host\n";
        }
      }
    }

    r += "\n";

    e = linkThingees.elements();
    while (e.hasMoreElements()) {
      Element t1 = (Element)e.nextElement();
      if (!(t1 instanceof EmulatedConnection)) {
        // it's a node link
        Connection t = (Connection)t1;
        n = t.getName();
        String a = t.getA().getName();
        String b = t.getB().getName();
        String bandwidth = t.getProperty("bandwidth", "100") + "Mb";
        String latency = t.getProperty("latency", "0") + "ms";
        r += "set " + n + " [$ns duplex-link $" + a + " $" + b + " " + bandwidth + " " + latency + " DropTail]\n";
        try {
          Float loss = new Float(t.getProperty("loss", "0.0"));
          float l = loss.floatValue();
          if (l > 1.0f) l = 1.0f;
          if (l > 0.0f)
            r += "tb-set-link-loss $" + n + " " + String.valueOf(l) + "\n";
        } catch (Exception ex) {
        }
      } else {
        // it's a lan link
        Connection t = (EmulatedConnection)t1;
        Element node, lan;
        if (t.getA() instanceof InternetConnector) {
          lan = t.getA();
          node = t.getB();
        } else {
          lan = t.getB();
          node = t.getA();
        }
        Vector v = (Vector)lanConnections.get(lan.getName());
        if (v == null) {
          v = new Vector();
          lanConnections.put(lan.getName(), v);
        }
        v.addElement(node);
        //tb-set-node-lan-params $node0 $lan0 40ms 20Mb 0.05
      }
    }

    r += "\n";

    e = iFaceThingees.elements();

    while (e.hasMoreElements()) {
      Element t1 = (Element)e.nextElement();
      if (t1 instanceof Interface) {
        Interface t = (Interface)t1;
        Connection lt = null;
        KvmDevice nt = null;
        if (t.getA() instanceof Connection) {
          lt = (Connection)t.getA();
          nt = (KvmDevice)t.getB();
        } else if (t.getB() instanceof Connection) {
          lt = (Connection)t.getB();
          nt = (KvmDevice)t.getA();
        }

        if (lt != null && !(lt instanceof EmulatedConnection)) {
          s = t.getProperty("ip", "<auto>");
          if (0 != s.compareTo("<auto>") && 0 != s.compareTo(""))
            r += "tb-set-ip-link $" + nt.getName() + " $" + lt.getName() + " " + s + "\n";
        }
      }
    }

    r += "\n";

    e = thingees.elements();
    while (e.hasMoreElements()) {
      Element t = (Element)e.nextElement();
      if (t instanceof InternetConnector) {
        Vector v = (Vector)lanConnections.get(t.getName());
        if (v != null) {
          r += "set " + t.getName() + " [$ns make-lan \"";
          Enumeration ce = v.elements();
          while (ce.hasMoreElements()) {
            Element cet = (Element)ce.nextElement();
            r += "$" + cet.getName() + " ";
          }
          String bandwidth = t.getProperty("bandwidth", "100")
           + "Mb";
          String latency = t.getProperty("latency", "0") + "ms";
          r += "\" " + bandwidth + " " + latency + "]\n";

          try {
            Float loss = new Float(t.getProperty("loss", "0.0"));
            float l = loss.floatValue();
            if (l > 1.0f) l = 1.0f;
            if (l > 0.0f)
              r += "tb-set-lan-loss $" + t.getName() + " " + String.valueOf(l) + "\n";
          } catch (Exception ex) {
          }
        }
      }
    }

    r += "\n";

    e = linkThingees.elements();
    while (e.hasMoreElements()) {
      Element t1 = (Element)e.nextElement();
      if (t1 instanceof EmulatedConnection) {
        // it's a lan link
        EmulatedConnection t = (EmulatedConnection)t1;
        Element node, lan;
        if (t.getA() instanceof InternetConnector) {
          lan = t.getA();
          node = t.getB();
        } else {
          lan = t.getB();
          node = t.getA();
        }
        //tb-set-node-lan-params $node0 $lan0 40ms 20Mb 0.05

        String bandwidth = t.getProperty("bandwidth", "<auto>");
        String latency = t.getProperty("latency", "<auto>");
        String loss = t.getProperty("loss", "<auto>");

        // only spit out a node-lan-params if parameters are not cascaded from LAN.
        if (0 != bandwidth.compareTo("<auto>") || 0 != latency.compareTo("<auto>") || 0 != loss.compareTo("<auto>")) {

          if (0 == bandwidth.compareTo("<auto>"))
            bandwidth = lan.getProperty("bandwidth", "100");
          if (0 == latency.compareTo("<auto>"))
            latency = lan.getProperty("latency", "0");
          if (0 == loss.compareTo("<auto>"))
            loss = lan.getProperty("loss", "0.0");

          bandwidth = bandwidth + "Mb";
          latency = latency + "ms";

          float l = 0.0f;
          try {
            Float lossf = new Float(loss);
            l = lossf.floatValue();
            if (l > 1.0f) l = 1.0f;
          } catch (Exception ex) {
          }
          r += "tb-set-node-lan-params $" + node.getName() + " $" + lan.getName() + " " + latency + " " + bandwidth
           + " " + String.valueOf(l) + "\n";
        }
      }
    }

    r += "\n";

    e = iFaceThingees.elements();

    while (e.hasMoreElements()) {
      Element t1 = (Element)e.nextElement();
      if (t1 instanceof Interface) {
        Interface t = (Interface)t1;
        Connection lt = null;
        KvmDevice nt = null;
        if (t.getA() instanceof Connection) {
          lt = (Connection)t.getA();
          nt = (KvmDevice)t.getB();
        } else if (t.getB() instanceof Connection) {
          lt = (Connection)t.getB();
          nt = (KvmDevice)t.getA();
        }

        if (lt != null && (lt instanceof EmulatedConnection)) {
          EmulatedConnection llt = (EmulatedConnection)lt;
          InternetConnector lant;
          if (llt.getA() instanceof InternetConnector)
            lant = (InternetConnector)llt.getA();
          else
            lant = (InternetConnector)llt.getB();
          s = t.getProperty("ip", "<auto>");
          if (0 != s.compareTo("<auto>") && 0 != s.compareTo(""))
            r += "tb-set-ip-lan $" + nt.getName() + " $" + lant.getName() + " " + s + "\n";
        }
      }
    }

    r += "\n$ns rtproto Static\n";
    r += "$ns run\n";
    r += "#netbuild-generated ns file ends.\n";

    return r;

    // #generated by Netbuild
    // set ns [new Simulator]
    // source tb_compat.tcl
    //
    // set NodeA [$ns node]
    // set NodeB [$ns node]
    //
    // tb-set-node-os $NodeA FBSD-STD
    //
    // set LinkA [$ns duplex-link $NodeA $NodeB 100Mb 50ms DropTail]
    // set LinkB [$ns duplex-link $NodeA $NodeB 100Mb .1ms DropTail]
    // tb-set-link-loss $LinkA 0.05
    // tb-set-ip-link $NodeB $linkA 192.168.42.42
    //
    // set lan0 [$ns make-lan "$node0 $node1" 100Mb .1ms]
    // tb-set-lan-loss $Lan1 0.3
    //
    // tb-set-ip-lan $NodeB $lan1 123.4.5.6
    // tb-set-node-lan-delay     $lan0 $node0 40ms
    // tb-set-node-lan-bandwidth $lan0 $node0 20Mb
    // tb-set-node-lan-loss      $lan0 $node0 0.2
    //
    // $ns run

  }

  public void copySelected () {
    Dictionary map = new Hashtable();
    Vector newIFaces = new Vector();
    Enumeration e = Element.selectedElements();

    // copy selected nodes
    while (e.hasMoreElements()) {
      Element t = (Element)e.nextElement();

      if (t instanceof KvmDevice) {
        KvmDevice nt = new KvmDevice(Element.genName(t.getName()));
        nt.move(t.getX() + 16, t.getY() + 16);
        nt.copyProps(t);
        add(nt);
        map.put(t, nt);
      } else if (t instanceof InternetConnector) {
        InternetConnector nt = new InternetConnector(Element.genName(t.getName()));
        nt.move(t.getX() + 16, t.getY() + 16);
        nt.copyProps(t);
        add(nt);
        map.put(t, nt);
      }
    }

    e = Element.selectedElements();

    // now copy selected links
    while (e.hasMoreElements()) {
      Element t = (Element)e.nextElement();

      if ((t instanceof Connection) && !(t instanceof EmulatedConnection)) {
        Connection lt = (Connection)t;
        Element a = (Element)map.get(lt.getA());
        Element b = (Element)map.get(lt.getB());
        String name = lt.getName();
        if (0 != name.compareTo(""))
          name = Element.genName(name);
        if (a != null && b != null) {
          Connection nt = new Connection(name, a, b);
          nt.copyProps(t);
          add(nt);
          map.put(t, nt);

          Interface i = new Interface("", a, nt);
          Interface i2 = new Interface("", b, nt);

          add(i);
          add(i2);
          newIFaces.addElement(i);
          newIFaces.addElement(i2);
        }
      } else if (t instanceof EmulatedConnection) {
        EmulatedConnection lt = (EmulatedConnection)t;
        Element a = (Element)map.get(lt.getA());
        Element b = (Element)map.get(lt.getB());
        if (a != null && b != null) {
          EmulatedConnection nt = new EmulatedConnection("", a, b);
          nt.copyProps(t);
          add(nt);
          map.put(t, nt);

          Element node;
          if (a instanceof KvmDevice) node = a;
          else node = b;
          Interface i = new Interface("", node, nt);
          add(i);
          newIFaces.addElement(i);
        }
      }
    }


    Element.deselectAll();

    e = map.elements();
    while (e.hasMoreElements()) {
      Element t = (Element)e.nextElement();
      t.select();
    }

    e = newIFaces.elements();
    while (e.hasMoreElements()) {
      Element t = (Element)e.nextElement();
      t.select();
    }

  }

  private void selectOneInRectangle (Rectangle r, Element t, boolean xor) {
    int xDiff = t.getX() - r.x;
    int yDiff = t.getY() - r.y;
    if (xDiff > 0 && xDiff < r.width && yDiff > 0 && yDiff < r.height)
      if (!xor || !t.isSelected())
        t.select();
      else
        t.deselect();
  }

  public void selectRectangle (Rectangle r, boolean xor) {
    Enumeration linkThingeeEnum = linkThingees.elements();

    while (linkThingeeEnum.hasMoreElements()) {
      Element t = (Element)linkThingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }

    Enumeration thingeeEnum = thingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }

    Enumeration iFaceThingeeEnum = iFaceThingees.elements();

    while (iFaceThingeeEnum.hasMoreElements()) {
      Element t = (Element)iFaceThingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }
  }

  public int getThingeeCount () {
    return linkThingees.size() + thingees.size() + iFaceThingees.size();
  }

  public void paint (Graphics g) {
    Enumeration linkThingeeEnum = linkThingees.elements();

    while (linkThingeeEnum.hasMoreElements()) {
      Element t = (Element)linkThingeeEnum.nextElement();
      t.draw(g);
    }

    Enumeration thingeeEnum = thingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      t.draw(g);
    }

    Enumeration iFaceThingeeEnum = iFaceThingees.elements();

    while (iFaceThingeeEnum.hasMoreElements()) {
      Element t = (Element)iFaceThingeeEnum.nextElement();
      t.draw(g);
    }
  }

  public Element clicked (int x, int y) {
    Enumeration thingeeEnum;

    Element got = null;

    thingeeEnum = linkThingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    thingeeEnum = thingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    thingeeEnum = iFaceThingees.elements();

    while (thingeeEnum.hasMoreElements()) {
      Element t = (Element)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    return got;
  }

  public void remove (Element t) {
    if (t instanceof Interface)
      iFaceThingees.removeElement(t);
    else if (t instanceof Connection) {
      boolean done = false;
      while (!done) {
        done = true;
        Enumeration e = iFaceThingees.elements();
        while (e.hasMoreElements() && done) {
          Interface i = (Interface)e.nextElement();
          if (i.isConnectedTo(t)) {
            remove(i);
            done = false;
          }
        }
      }
      linkThingees.removeElement(t);
    } else {
      boolean done = false; // stupid hack.
      while (!done) {
        done = true;
        Enumeration thingeeEnum = linkThingees.elements();
        while (thingeeEnum.hasMoreElements() && done) {
          Connection u = (Connection)thingeeEnum.nextElement();
          if (u.isConnectedTo(t)) {
            remove(u);
            done = false;
          }
        }
      }
      thingees.removeElement(t);
    }
  }

  public void add (Element t) {
    if (t instanceof Connection)
      linkThingees.addElement(t);
    else if (t instanceof Interface)
      iFaceThingees.addElement(t);
    else
      thingees.addElement(t);
  }
};

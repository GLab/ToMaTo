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

/******** 
 * TODO:
 *
 * fix netscape icon issue
 * better validate (incl. IPs)
 * scroll workarea
 * (?) scroll property area
 * X lanlink stuff.
 * X respect loss pct   
 * X validate user input
 * X auto button
 * X validate name (e.g. no collisions)
 *
 */
import buildui.paint.FlatButton;
import buildui.paint.PropertiesArea;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.util.*;
import java.lang.*;
import java.net.*;

import buildui.connectors.EmulatedConnection;
import buildui.connectors.InternetConnector;
import buildui.connectors.EmulatedConnectionPropertiesArea;
import buildui.connectors.InternetPropertiesArea;
import buildui.connectors.ConnectionPropertiesArea;
import buildui.connectors.Connection;
import buildui.devices.IFacePropertiesArea;
import buildui.devices.IFaceThingee;
import buildui.devices.KvmPropertiesArea;
import buildui.devices.KvmDevice;
import buildui.paint.Palette;
import buildui.paint.Element;
//import netscape.javascript.*;
//import java.io.*;

public class Netbuild extends java.applet.Applet
 implements MouseListener, MouseMotionListener, ActionListener,
 KeyListener {

  private WorkArea workArea;
  private Palette palette;
  private Panel propertiesPanel;
  private PropertiesArea linkPropertiesArea;
  private PropertiesArea lanPropertiesArea;
  private PropertiesArea nodePropertiesArea;
  private PropertiesArea iFacePropertiesArea;
  private PropertiesArea lanLinkPropertiesArea;
  private boolean modify;
  private boolean mouseDown;
  private boolean clickedOnSomething;
  private boolean allowMove;
  private boolean dragStarted;
  private boolean shiftWasDown;
  private boolean selFromPalette;
  private int lastDragX, lastDragY;
  private int downX, downY;
  private static Netbuild me;
  private static Color cornflowerBlue;
  private static Color lightBlue;
  private static Color darkBlue;
  private String status;
  private int appWidth, appHeight;
  private int propAreaWidth;
  private int paletteWidth;
  private int workAreaWidth;
  private int workAreaX;
  private int propAreaX;
  //    private Linko exportButton;
  private FlatButton exportButton;
  private FlatButton copyButton;
  private boolean copyButtonActive;
  private static boolean fatalError;
  private static String fatalErrorMessage;

  static {
    fatalError = false;
    cornflowerBlue = new Color(0.95f, 0.95f, 1.0f);
    lightBlue = new Color(0.9f, 0.9f, 1.0f);
    darkBlue = new Color(0.3f, 0.3f, 0.5f);
  }
  private Dialog d;

  private void dialog (String title, String message) {
    Frame window = new Frame();

    // Create a modal dialog
    d = new Dialog(window, title, true);

    // Use a flow layout
    d.setLayout(new FlowLayout());

    d.setLocation(new Point(20, 20));

    // Create an OK button
    Button ok = new Button("OK");
    ok.addActionListener(new ActionListener() {

      public void actionPerformed (ActionEvent e) {
        // Hide dialog
        me.d.setVisible(false);
      }
    });

    d.add(new Label(title + ": "));
    d.add(new Label(message));
    d.add(ok);

    // Show dialog
    d.pack();
    d.setVisible(true);
  }

  private void fatalError (String message) {
    //dialog( "NetBuild Fatal Error", message );
    //System.exit(0);
    fatalErrorMessage = message;
    fatalError = true;
  }

  private void warningError (String message) {
    dialog("NetBuild Warning", message);
  }

  // returns true if anything was added.
  private boolean doittoit (boolean needed, PropertiesArea which, boolean forceExpand) {
    if (needed)
      if (which.isStarted())
        //		System.out.println("Refreshing");
        which.refresh();
      else {
        //System.out.println("Vising");
        which.setVisible(false);
        //System.out.println("v1");
        propertiesPanel.add(which);
        //System.out.println("v2");
        which.start();
        //System.out.println("v3");
        if (forceExpand)
          which.showProperties();
        else
          which.hideProperties();
        //System.out.println("v4");
        which.setVisible(true);
        //System.out.println("Done.");
        return true;
      }
    else //System.out.println("Leaving alone.");
    if (which.isStarted()) {
      //System.out.println("Stopping");
      which.stop();
      propertiesPanel.remove(which);
    }
    return false;
  }

  private void precachePropertiesAreas () {
    // this hack makes it so
    // the widget creating goes on at app startup,
    // not when the user places the first node (that is very annoying)

    doittoit(true, nodePropertiesArea, false);
    doittoit(true, linkPropertiesArea, false);
    doittoit(true, lanPropertiesArea, false);
    doittoit(true, lanLinkPropertiesArea, false);
    doittoit(true, iFacePropertiesArea, false);
    propertiesPanel.doLayout();
    propertiesPanel.setVisible(false);
    propertiesPanel.repaint();
  }

  private void startAppropriatePropertiesArea () {
    int typeCount = 0;
    int selCount = 0;
    boolean needLanLink = false;
    boolean needLink = false;
    boolean needLan = false;
    boolean needIFace = false;
    boolean needNode = false;

    Enumeration en = Element.selectedElements();

    while (en.hasMoreElements()) {
      Element t = (Element)en.nextElement();

      if (t.propertyEditable)
        if (t instanceof EmulatedConnection) {
          if (!needLanLink) typeCount++;
          needLanLink = true;
        } else if (t instanceof Connection) {
          if (!needLink) typeCount++;
          needLink = true;
        } else if (t instanceof InternetConnector) {
          if (!needLan) typeCount++;
          needLan = true;
          selCount++;
        } else if (t instanceof IFaceThingee) {
          if (!needIFace) typeCount++;
          needIFace = true;
        } else if (t instanceof KvmDevice) {
          if (!needNode) typeCount++;
          needNode = true;
          selCount++;
        }
    }

    boolean exp = typeCount <= 1;
    propertiesPanel.setVisible(false);
    boolean changes = false;
    changes |= doittoit(needNode, nodePropertiesArea, exp);
    changes |= doittoit(needLink, linkPropertiesArea, exp);
    changes |= doittoit(needLan, lanPropertiesArea, exp);
    changes |= doittoit(needLanLink, lanLinkPropertiesArea, exp);
    changes |= doittoit(needIFace, iFacePropertiesArea, exp);

    if (selCount > 0) {
      if (!copyButton.isVisible()) {
        copyButton.setVisible(true);
        propertiesPanel.add(copyButton);
      } else // this is so it is always on the bottom.
      if (changes) {
        // if a panel got added.. re-cycle to the bottom.
        propertiesPanel.remove(copyButton);
        propertiesPanel.add(copyButton);
      }
    } else if (copyButton.isVisible()) {
      propertiesPanel.remove(copyButton);
      copyButton.setVisible(false);
    }

    propertiesPanel.doLayout();
    propertiesPanel.setVisible(true);
  }

  private boolean isInWorkArea (int x, int y) {
    return x > workAreaX && y > 0 && x < workAreaX + workAreaWidth && y < appHeight;
  }

  public static void redrawAll () {
    if (fatalError) return;

    me.repaint();
  }

  public static void setStatus (String newStatus) {
    me.status = newStatus;
    //	g.drawString( status, workAreaX + 4, 474 );
    me.repaint(me.workAreaX + 4, 420, 640 - (me.workAreaX + 4), 60);
  }

  public static Image getImage (String name) {
    try {
      System.out.println("Trying to load image" + name);
      URL url = Netbuild.class.getResource(name);
      System.out.println(url);
      Image im = me.getImage(url);
      if (im == null) System.out.println("Failed to load image.");
      return im;
    } catch (Exception e) {
      System.out.println("Error getting image.");
      e.printStackTrace();
      return null;
    }
    //return me.getImage( me.getCodeBase(), name );
  }

  public void keyTyped (KeyEvent e) {
  }

  public void keyPressed (KeyEvent e) {
    if (fatalError) return;

    System.out.println("Woo.");
    if (e.getKeyCode() == KeyEvent.VK_C) {
      prePaintSelChange();
      workArea.copySelected();
      paintSelChange();
    }
  }

  public void keyReleased (KeyEvent e) {
  }

  public void mouseMoved (MouseEvent e) {
  }

  public void mouseDragged (MouseEvent e) {
    if (fatalError) return;

    if (!mouseDown) return;
    Graphics g = getGraphics();
    g.setXORMode(Color.white);

    if (clickedOnSomething) {
      if (allowMove) {
        if (dragStarted) {
          if (palette.hitTrash(lastDragX + downX, lastDragY + downY))
            palette.funktasticizeTrash(g);
          Enumeration en = Element.selectedElements();

          while (en.hasMoreElements()) {
            Element t = (Element)en.nextElement();
            if (t.moveable || t.trashable)
              if (selFromPalette)
                g.drawRect(t.getX() + lastDragX - 16, t.getY() + lastDragY - 16, 32, 32);
              else
                g.drawRect(t.getX() + lastDragX - 16 + workAreaX,
                 t.getY() + lastDragY - 16,
                 32, 32);
          }
        }

        dragStarted = true;

        lastDragX = e.getX() - downX;
        lastDragY = e.getY() - downY;

        if (palette.hitTrash(e.getX(), e.getY()))
          palette.funktasticizeTrash(g);

        Enumeration en = Element.selectedElements();

        while (en.hasMoreElements()) {
          Element t = (Element)en.nextElement();
          if (t.moveable || t.trashable)
            if (selFromPalette)
              g.drawRect(t.getX() + lastDragX - 16, t.getY() + lastDragY - 16, 32, 32);
            else
              g.drawRect(t.getX() + lastDragX - 16 + workAreaX,
               t.getY() + lastDragY - 16,
               32, 32);
        }
      }
    } else {
      int leastX = downX;
      int sizeX = lastDragX;
      int leastY = downY;
      int sizeY = lastDragY;
      if (downX + lastDragX < leastX) {
        leastX = downX + lastDragX;
        sizeX = -lastDragX;
      }
      if (downY + lastDragY < leastY) {
        leastY = downY + lastDragY;
        sizeY = -lastDragY;
      }

      if (dragStarted)
        //g.drawRect( downX, downY, lastDragX, lastDragY );
        g.drawRect(leastX, leastY, sizeX, sizeY);
      dragStarted = true;
      lastDragX = e.getX() - downX;
      lastDragY = e.getY() - downY;

      {
        int leastX2 = downX;
        int sizeX2 = lastDragX;
        int leastY2 = downY;
        int sizeY2 = lastDragY;
        if (downX + lastDragX < leastX2) {
          leastX2 = downX + lastDragX;
          sizeX2 = -lastDragX;
        }
        if (downY + lastDragY < leastY2) {
          leastY2 = downY + lastDragY;
          sizeY2 = -lastDragY;
        }

        g.drawRect(leastX2, leastY2, sizeX2, sizeY2);
        //g.drawRect( downX2, downY2, lastDragX2, lastDragY2 );
      }
    }
    g.setPaintMode();
  }

  /*
  public boolean grabIt () {
    try {
      String action = getParameter("action");
      if (action == null || !action.equals("modify")) {
        System.out.println("Not modifying...");
        return false;
      }
      String eid = getParameter("eid");
      String pid = getParameter("pid");
      String uid = getParameter("uid");
      String auth = getParameter("auth");

      if (eid == null || pid == null || uid == null || auth == null)
        fatalError("Insufficient Parameters.");

      String ns = new String("");
      int linesRecd = 0;

      System.out.println("Getting NS...");
      {
        URL url;
        URLConnection urlConn;
        DataOutputStream printout;
        DataInputStream input;
        // URL of CGI-Bin script.
        //url = new URL (getCodeBase().toString() + "env.tcgi");
        url = new URL(getParameter("importurl"));
        // URL connection channel.
        urlConn = url.openConnection();
        // Let the run-time system (RTS) know that we want input.
        urlConn.setDoInput(true);
        // Let the RTS know that we want to do output.
        urlConn.setDoOutput(true);
        // No caching, we want the real thing.
        urlConn.setUseCaches(false);
        // Specify the content type.
        urlConn.setRequestProperty("Content-Type",
         "application/x-www-form-urlencoded");
        // Send POST output.
        printout = new DataOutputStream(urlConn.getOutputStream());
        String content =
         "eid=" + URLEncoder.encode(eid) + "&pid=" + URLEncoder.encode(pid) + "&nocookieuid=" + URLEncoder.encode(uid)
         + "&justns=1" + "&nocookieauth=" + URLEncoder.encode(auth);
        printout.writeBytes(content);
        printout.flush();
        printout.close();
        // Get response data.
        input = new DataInputStream(urlConn.getInputStream());
        String str;
        System.out.println("BEGIN NS FROM SERVER:");
        while (null != ((str = input.readLine()))) {
          //System.out.println (str);
          ns = ns.concat(str);
          ns = ns.concat("\n");
          linesRecd++;
        }
        System.out.println("END NS FROM SERVER.");
        input.close();
      }

      //System.out.println("Modify = '" + modify + "'");
      if (linesRecd == 0) {
        fatalError("NS file was blank!");
        //System.out.println("Got blank NS file!");
        return false;
      }
      System.out.println("Successfully (?) obtained NS file.");
      // System.out.print(ns);
      // call fromNS on ns.
      if (!workArea.fromNS(ns)) {
        fatalError("parsefail");
        //System.out.println("NS failed to parse!");
        return false;
      } else
        System.out.println("Successfully parsed NS!");
      return true;
    } catch (Exception ex) {
      System.out.println("grabIt(): exception '" + ex.getMessage() + "'");
      ex.printStackTrace();
      fatalError("Failed to get and parse NS file!");
      return false;
    }
  }
*/
  public String modifyIt (String s) {
    String eid = getParameter("eid");
    String pid = getParameter("pid");
    String uid = getParameter("uid");
    String auth = getParameter("auth");

    if (eid == null || pid == null || uid == null || auth == null) {
      warningError("Failed to modify experiment.");
      //System.out.println("Insufficient parameters...");
      return "Bad applet parameters";
    }

    String response = new String("Could not contact server.");

    try {
      URL url;
      URLConnection urlConn;
      DataOutputStream printout;
      DataInputStream input;
      // URL of CGI-Bin script.
      //url = new URL (getCodeBase().toString() + "env.tcgi");
      url = new URL(getParameter("modifyurl"));
      // URL connection channel.
      urlConn = url.openConnection();
      // Let the run-time system (RTS) know that we want input.
      urlConn.setDoInput(true);
      // Let the RTS know that we want to do output.
      urlConn.setDoOutput(true);
      // No caching, we want the real thing.
      urlConn.setUseCaches(false);
      // Specify the content type.
      urlConn.setRequestProperty("Content-Type",
       "application/x-www-form-urlencoded");
      // Send POST output.
      printout = new DataOutputStream(urlConn.getOutputStream());
      String content =
       "nsdata=" + URLEncoder.encode(s) + "&go=1&reboot=1" + "&eid=" + URLEncoder.encode(eid) + "&pid=" + URLEncoder.
       encode(pid) + "&nocookieuid=" + URLEncoder.encode(uid) + "&nocookieauth=" + URLEncoder.encode(auth);
      printout.writeBytes(content);
      printout.flush();
      printout.close();
      // Get response data.
      input = new DataInputStream(urlConn.getInputStream());
      String str;
      while (null != ((str = input.readLine())))
        //System.out.println (str);
        if (str.toLowerCase().startsWith("<!-- netbuild!"))
          //System.out.println( "Registered response!");
          response = str;
      input.close();

      System.out.println("Response = " + response);
      return response.substring(15, response.length() - 4);
    } catch (Exception ex) {
      //warningError("Failed to modify experiment");
      System.out.println("modifyIt() exception: " + ex.getMessage());
      ex.printStackTrace();
      return "Exception";
    }

    //return "nsref=" + String.valueOf(hash) +
    //       "&guid=" + randVal;
    //return response;
  }

  public String postIt (String s) {
    int hash = s.hashCode();
    Random rand = new Random();
    int randInt = rand.nextInt() % 102010201;
    if (randInt < 0) randInt = -randInt;
    String randVal = String.valueOf(randInt);

    if (hash < 0) hash = -hash;
    if (hash == 0) hash = 1;
    try {
      URL url;
      URLConnection urlConn;
      DataOutputStream printout;
      DataInputStream input;
      // URL of CGI-Bin script.
      //url = new URL (getCodeBase().toString() + "env.tcgi");
      url = new URL(getParameter("exporturl"));
      // URL connection channel.
      urlConn = url.openConnection();
      // Let the run-time system (RTS) know that we want input.
      urlConn.setDoInput(true);
      // Let the RTS know that we want to do output.
      urlConn.setDoOutput(true);
      // No caching, we want the real thing.
      urlConn.setUseCaches(false);
      // Specify the content type.
      urlConn.setRequestProperty("Content-Type",
       "application/x-www-form-urlencoded");
      // Send POST output.
      printout = new DataOutputStream(urlConn.getOutputStream());
      String content =
       "nsdata=" + URLEncoder.encode(s) + "&nsref=" + String.valueOf(hash) + "&guid=" + randVal;
      printout.writeBytes(content);
      printout.flush();
      printout.close();
      // Get response data.
      input = new DataInputStream(urlConn.getInputStream());
      String str;
      while (null != ((str = input.readLine())))
        System.out.println(str);
      input.close();

    } catch (Exception ex) {
      System.out.println("exception: " + ex.getMessage());
      ex.printStackTrace();
      return "posterror=1";
    }
    return "nsref=" + String.valueOf(hash) + "&guid=" + randVal;
  }

  // public void toCookie( String s ) {
  //   java.util.Calendar c = java.util.Calendar.getInstance();
  //   c.add(java.util.Calendar.MONTH, 1);
  //   String expires = "; expires=" + c.getTime().toString();
  //   String s1 = s + expires;
  //   System.out.println(s1);
  //   JSObject myBrowser = JSObject.getWindow(this);
  //   JSObject myDocument =  (JSObject) myBrowser.getMember("document");
  //   myDocument.setMember("cookie", s1);
  //}
  public void actionPerformed (ActionEvent e) {
    if (fatalError) return;
    if (e.getSource() == exportButton) {
      startAppropriatePropertiesArea(); // make sure strings are up'd
      String ns = workArea.toNS();
      System.out.println(ns);

      if (!modify) {
        String ref = postIt(ns);
        //String url = getParameter("exporturl") + "?nsdata=" +
        //URLEncoder.encode( ns );
        //toCookie( ns );
        //String url = getParameter("exporturl") + "?nsdataincookie=1";
        String url = getParameter("expcreateurl") + "?" + ref;
        System.out.println(url);
        try {
          getAppletContext().showDocument(new URL(url), "_blank");
        } catch (Exception ex) {
          System.out.println("exception: " + ex.getMessage());
          ex.printStackTrace();
        }
      } else {
        String ret = modifyIt(ns);
        if (ret.equalsIgnoreCase("success")) {
          System.out.println("actionPerformed: modify success");
          String url = getParameter("modifyurl") + "?" + "&eid=" + URLEncoder.encode(getParameter("eid")) + "&pid=" + URLEncoder.
           encode(getParameter("pid")) + "&justsuccess=1";
          System.out.println(url);
          try {
            getAppletContext().showDocument(new URL(url), "_blank");
          } catch (Exception ex) {
            System.out.println("exception: " + ex.getMessage());
            ex.printStackTrace();
          }
        } else {
          System.out.println("actionPerformed: failed.");
          warningError(ret);
        }
      }
    } else if (e.getSource() == copyButton) {
      prePaintSelChange();
      workArea.copySelected();
      paintSelChange();
      startAppropriatePropertiesArea();
    }
  }

  public void mousePressed (MouseEvent e) {
    if (fatalError) return;

    mouseDown = true;
    int x = e.getX();
    int y = e.getY();
    /*
    if (x < 8 && y < 8) {

    try {
    File foo = new File( "out.txt" );
    FileOutputStream fos = new FileOutputStream( foo );
    FilterOutputStream foos = new FilterOutputStream( fos );
    PrintWriter pw = new PrintWriter( foos );
    pw.println( workArea.toNS() );
    pw.flush();
    } catch (Exception ex ) {
    System.out.println("exception: " + ex.getMessage());
    ex.printStackTrace();
    //System.out.println( workArea.toNS());

    }
    }
     */

    shiftWasDown = e.isShiftDown();
    downX = x;
    downY = y;

    lastDragX = 0;
    lastDragY = 0;

    Element clickedOn;

    prePaintSelChange();

    if (isInWorkArea(x, y)) {
      clickedOn = workArea.clicked(x - paletteWidth, y);
      selFromPalette = false;
    } else {
      Element.deselectAll();
      clickedOn = palette.clicked(x, y);
      selFromPalette = true;
    }

    clickedOnSomething = (clickedOn != null);

    if (e.isControlDown()) {
      allowMove = false;
      if (clickedOnSomething) {
        Enumeration en = Element.selectedElements();

        while (en.hasMoreElements()) {
          Element a = (Element)en.nextElement();
          Element b = clickedOn;

          if (a != b && a != null && b != null && a.linkable && b.linkable)
            if (a instanceof KvmDevice && b instanceof KvmDevice) {
              Connection t = new Connection(Element.genName("link"), a, b);
              workArea.add(t);
              IFaceThingee it = new IFaceThingee("", a, t);
              workArea.add(it);
              IFaceThingee it2 = new IFaceThingee("", b, t);
              workArea.add(it2);
              paintThingee(t);
              paintThingee(it);
              paintThingee(it2);
            } else if (a instanceof KvmDevice && b instanceof InternetConnector) {
              Connection t = new EmulatedConnection("", a, b);
              workArea.add(t);
              IFaceThingee it = new IFaceThingee("", a, t);
              workArea.add(it);
              paintThingee(t);
              paintThingee(it);
            } else if (b instanceof KvmDevice && a instanceof InternetConnector) {
              Connection t = new EmulatedConnection("", a, b);
              workArea.add(t);
              IFaceThingee it = new IFaceThingee("", b, t);
              workArea.add(it);
              paintThingee(t);
              paintThingee(it);
            } else if (a instanceof InternetConnector && b instanceof InternetConnector)
              Netbuild.setStatus("!LAN to LAN connection not allowed.");
            else {
            }

        }
      }
    } else {// if (e.controlDown())
      allowMove = true;
      if (clickedOn == null) {
        if (!e.isShiftDown())
          Element.deselectAll();
      } else if (clickedOn.isSelected())
        if (!e.isShiftDown()) {
        } else
          clickedOn.deselect();
      else {
        if (!e.isShiftDown())
          Element.deselectAll();
        clickedOn.select();
      }
    }

    paintSelChange();
    startAppropriatePropertiesArea();

    //repaint();

    dragStarted = false;
  }

  private void paintThingee (Element t) {
    Rectangle r = t.getRectangle();

    // HACK!
    if (palette.has(t))
      repaint(r.x, r.y, r.width, r.height);
    else
      repaint(r.x + workAreaX, r.y, r.width, r.height);
  }
  private Dictionary wasSelected;

  private void prePaintSelChange () {
    wasSelected = new Hashtable();
    Enumeration en = Element.selectedElements();

    while (en.hasMoreElements()) {
      Element t = (Element)en.nextElement();
      wasSelected.put(t, new Integer(1));
    }
  }

  private void paintSelChange () {
    Enumeration en = Element.selectedElements();

    while (en.hasMoreElements()) {
      Element t = (Element)en.nextElement();

      if (wasSelected.get(t) == null) {
        paintThingee(t);
        wasSelected.remove(t);
      }
    }

    en = wasSelected.keys();

    while (en.hasMoreElements()) {
      Element t = (Element)en.nextElement();
      paintThingee(t);
    }
  }

  public void mouseReleased (MouseEvent e) {
    if (fatalError) return;

    if (!mouseDown) return;
    mouseDown = false;
    if (clickedOnSomething) {
      if (dragStarted) {
        Graphics g = getGraphics();
        g.setXORMode(Color.white);

        if (palette.hitTrash(lastDragX + downX, lastDragY + downY))
          palette.funktasticizeTrash(g);

        {
          Enumeration en = Element.selectedElements();

          while (en.hasMoreElements()) {
            Element t = (Element)en.nextElement();
            if (t.moveable || t.trashable)
              if (selFromPalette)
                g.drawRect(t.getX() + lastDragX - 16, t.getY() + lastDragY - 16, 32, 32);
              else
                g.drawRect(t.getX() + lastDragX - 16 + workAreaX,
                 t.getY() + lastDragY - 16,
                 32, 32);
          }
        }

        g.setPaintMode();

        int x = e.getX();
        int y = e.getY();

        if (selFromPalette)
          // from palette..
          if (x < paletteWidth) {
            // back to palette -- nothing happens.
          } else {
            // into workarea. Create.
            prePaintSelChange();
            Element t = (Element)Element.selectedElements().nextElement() ;
            Element el = t.createAnother() ;
            el.move(x-paletteWidth, y);
            workArea.add(el);
            Element.deselectAll();
            t.select();
            selFromPalette = false;
            startAppropriatePropertiesArea();
            //paintThingee(t);
            paintSelChange();
            exportButton.setEnabled(true);
            //repaint();
          }
        else // from workarea..
        if (!isInWorkArea(x, y)) {
          // out of work area.. but to where?
          if (palette.hitTrash(x, y)) {
            Enumeration en = Element.selectedElements();

            while (en.hasMoreElements()) {
              Element t = (Element)en.nextElement();
              if (t.trashable) {
                // into trash -- gone.
                t.deselect();
                workArea.remove(t);
                Netbuild.setStatus("Selection trashed.");
              } else if (t instanceof IFaceThingee)
                t.deselect();
            }
            repaint();
            startAppropriatePropertiesArea();

            if (workArea.getThingeeCount() < 1)
              exportButton.setEnabled(false);
          } else if (palette.hitCopier(x, y)) {
            prePaintSelChange();
            workArea.copySelected();
            paintSelChange();
          }
        } else {
          Enumeration en = Element.selectedElements();

          while (en.hasMoreElements()) {
            Element t = (Element)en.nextElement();

            if (t.moveable)
              t.move(t.getX() + lastDragX, t.getY() + lastDragY);
            repaint();
          }
        }
      }
    } else { // if clickedonsomething
      // dragrect

      if (lastDragX != 0 && lastDragY != 0)
        prePaintSelChange();

      Graphics g = getGraphics();
      g.setXORMode(Color.white);

      int leastX = downX;
      int sizeX = lastDragX;
      int leastY = downY;
      int sizeY = lastDragY;
      if (downX + lastDragX < leastX) {
        leastX = downX + lastDragX;
        sizeX = -lastDragX;
      }
      if (downY + lastDragY < leastY) {
        leastY = downY + lastDragY;
        sizeY = -lastDragY;
      }

      if (dragStarted)
        //		    g.drawRect( downX, downY, lastDragX, lastDragY );
        g.drawRect(leastX, leastY, sizeX, sizeY);
      g.setPaintMode();
      /*
      workArea.selectRectangle( new Rectangle( downX - workAreaX,
      downY - workAreaY,
      lastDragX,
      lastDragY), shiftWasDown );
       */
      if (lastDragX != 0 && lastDragY != 0) {
        workArea.selectRectangle(new Rectangle(leastX - workAreaX,
         leastY,
         sizeX,
         sizeY), shiftWasDown);

        paintSelChange();
        startAppropriatePropertiesArea();
      }
    }
    dragStarted = false;
    lastDragX = 0;
    lastDragY = 0;
  }

  public void mouseEntered (MouseEvent e) {
  }

  public void mouseExited (MouseEvent e) {
  }

  public void mouseClicked (MouseEvent e) {
  }

  public String getAppletInfo () {
    return "Designs a network topology.";
  }

  //    public Netbuild() {
  //super();
  public void init () {
    fatalError = false;
    status = "Netbuild v1.03 started.";
    me = this;
    mouseDown = false;

    setLayout(null);

    //setLayout( new FlowLayout( FlowLayout.RIGHT, 4, 4 ) );
    addMouseListener(this);
    addMouseMotionListener(this);
    addKeyListener(this);

    Dimension d = getSize();
    appWidth = d.width - 1; //640;
    appHeight = d.height - 1; //480;

    propAreaWidth = 160;
    paletteWidth = 80;
    workAreaWidth = appWidth - propAreaWidth - paletteWidth;

    workArea = new WorkArea(workAreaWidth, appHeight);
    palette = new Palette();
    propertiesPanel = new Panel();

    //modify = grabIt();

    if (!fatalError) {
      nodePropertiesArea = new KvmPropertiesArea();
      linkPropertiesArea = new ConnectionPropertiesArea();
      iFacePropertiesArea = new IFacePropertiesArea();
      lanPropertiesArea = new InternetPropertiesArea();
      lanLinkPropertiesArea = new EmulatedConnectionPropertiesArea();

      dragStarted = false;


      workAreaX = paletteWidth;
      propAreaX = paletteWidth + workAreaWidth;

      setBackground(darkBlue);
      propertiesPanel.setBackground(darkBlue);
      propertiesPanel.setVisible(true);

      if (!modify) {
        exportButton = new FlatButton("create experiment");
        exportButton.addActionListener(this);
      } else {
        exportButton = new FlatButton("modify experiment");
        exportButton.addActionListener(this);
      }

      copyButton = new FlatButton("copy selection");
      copyButton.addActionListener(this);

      add(propertiesPanel);

      propertiesPanel.setLocation(propAreaX + 8, 0 + 8 + 24);
      propertiesPanel.setSize(propAreaWidth - 16, appHeight - 16 - 32 - 22);

      exportButton.setVisible(true);
      exportButton.setEnabled(workArea.getThingeeCount() > 0);
      add(exportButton);

      exportButton.setLocation(propAreaX + 8, appHeight - 24 - 2 - 2);
      exportButton.setSize(propAreaWidth - 16, 20);

      copyButton.setVisible(false);
      copyButton.setSize(propAreaWidth - 16, 20);

      precachePropertiesAreas();
    }
  }

  public void paint (Graphics g) {
    if (fatalError) {
      g.setColor(Color.black);
      g.drawString("Fatal Error!", 10, 30);
      if (fatalErrorMessage.equals("parsefail")) {
        g.drawString("Failed to parse NS file!", 10, 55);
        g.drawString("This may be due to attempting to edit an experiment which", 10, 70);
        g.drawString("used an NS file that wasn't generated by NetBuild,", 10, 85);
        g.drawString("or was modified by hand to be more complicated than", 10, 100);
        g.drawString("NetBuild can understand, or if an experiment no longer exists at all.", 10, 115);
        g.drawString("If this is a problem, please contact Testbed Ops.", 10, 145);
      } else {
        g.drawString(fatalErrorMessage, 10, 50);
        g.drawString("If this is a problem, please contact Testbed Ops.", 10, 80);
      }
      super.paint(g);
      return;
    }
    g.setColor(lightBlue);
    g.fillRect(0, 0, paletteWidth, appHeight);

    g.setColor(cornflowerBlue);
    g.fillRect(workAreaX, 0, workAreaX + workAreaWidth, appHeight);

    g.setColor(darkBlue);
    g.fillRect(propAreaX, 0,
     propAreaX + propAreaWidth, appHeight);

    g.setColor(Color.black);
    g.drawRect(0, 0, appWidth, appHeight);
    g.drawRect(0, 0, paletteWidth, appHeight);
    g.drawRect(workAreaX, 0, workAreaWidth, appHeight);
    g.drawRect(propAreaX, 0,
     propAreaWidth, appHeight);


    if (status.compareTo("") != 0 && status.charAt(0) == '!')
      g.setColor(Color.red);

    g.drawString(status, workAreaX + 4, appHeight - 6);

    palette.paint(g);
    //propertiesArea.paint( g );

    g.setColor(Color.black);
    g.fillRect(propAreaX + 8 - 3, appHeight - 24 - 2 - 8,
     propAreaWidth - 16 + 6, 1);

    g.setColor(Color.darkGray);
    g.fillRect(propAreaX + 8 - 3, appHeight - 24 - 2 - 7,
     propAreaWidth - 16 + 6, 1);

    g.translate(workAreaX, 0);
    g.setClip(1, 1, workAreaWidth - 1, appHeight - 1);
    workArea.paint(g);
    g.translate(-workAreaX, 0);
    g.setClip(0, 0, appWidth, appHeight);
    super.paint(g);
  }
}







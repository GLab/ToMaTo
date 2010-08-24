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
 * FIXME: Glab colors
 * FIXME: Implement download
 * FIXME: Initialize properties
 * FIXME: Popup on exception
 * FIXME: Fix chrome browser
 */
import buildui.paint.FlatButton;
import buildui.paint.PropertiesArea;
import java.awt.*;
import java.awt.event.*;
import java.io.IOException;
import java.util.*;
import java.net.*;

import buildui.connectors.InternetConnector;
import buildui.connectors.Connection;
import buildui.connectors.Connector;
import buildui.devices.Device;
import buildui.devices.Interface;
import buildui.paint.Palette;
import buildui.paint.NetElement;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

public class Netbuild extends java.applet.Applet
 implements MouseListener, MouseMotionListener, ActionListener,
 KeyListener {

  private WorkArea workArea;
  private Palette palette;
  private Panel propertiesPanel;
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
  private FlatButton exportButton;
  private FlatButton copyButton;
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
    fatalErrorMessage = message;
    fatalError = true;
  }

  private void warningError (String message) {
    dialog("NetBuild Warning", message);
  }

  // returns true if anything was added.
  private boolean doittoit (boolean needed, PropertiesArea which, boolean forceExpand) {
    if (needed)
      if (which.isStarted()) which.refresh();
      else {
        which.setVisible(false);
        propertiesPanel.add(which);
        which.start();
        if (forceExpand)
          which.showProperties();
        else
          which.hideProperties();
        which.setVisible(true);
        return true;
      }
    else if (which.isStarted()) {
      which.stop();
      propertiesPanel.remove(which);
    }
    return false;
  }

  private void startAppropriatePropertiesArea () {
    Set<PropertiesArea> oldPanels = new HashSet<PropertiesArea>();
    for (Component c: propertiesPanel.getComponents())
      if (c instanceof PropertiesArea) oldPanels.add((PropertiesArea)c);
    Enumeration en = NetElement.selectedElements();
    Set<PropertiesArea> newPanels = new HashSet<PropertiesArea>();
    while (en.hasMoreElements()) {
      NetElement t = (NetElement)en.nextElement();
      if (t.propertyEditable) newPanels.add(t.getPropertiesArea());
    }
    boolean exp = newPanels.size() <= 1;
    propertiesPanel.setVisible(false);
    for (PropertiesArea pa: newPanels) if (!oldPanels.contains(pa))
        doittoit(true, pa, exp);
    for (PropertiesArea pa: oldPanels) if (!newPanels.contains(pa))
        doittoit(false, pa, exp);
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
    me.repaint(me.workAreaX + 4, 420, 640 - (me.workAreaX + 4), 60);
  }

  public static Image getImage (String name) {
    try {
      URL url = Netbuild.class.getResource(name);
      Image im = me.getImage(url);
      if (im == null) System.out.println("Failed to load image.");
      return im;
    } catch (Exception e) {
      System.out.println("Error getting image.");
      e.printStackTrace();
      return null;
    }
  }

  public void keyTyped (KeyEvent e) {
  }

  public void keyPressed (KeyEvent e) {
    //ignore
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
          Enumeration en = NetElement.selectedElements();

          while (en.hasMoreElements()) {
            NetElement t = (NetElement)en.nextElement();
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

        Enumeration en = NetElement.selectedElements();

        while (en.hasMoreElements()) {
          NetElement t = (NetElement)en.nextElement();
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
      }
    }
    g.setPaintMode();
  }

  public void actionPerformed (ActionEvent e) {
    if (fatalError) return;
    if (e.getSource() == exportButton) {
      startAppropriatePropertiesArea(); // make sure strings are up'd
      upload(modify);
    }
  }

  public void mousePressed (MouseEvent e) {
    if (fatalError) return;

    mouseDown = true;
    int x = e.getX();
    int y = e.getY();

    shiftWasDown = e.isShiftDown();
    downX = x;
    downY = y;

    lastDragX = 0;
    lastDragY = 0;

    NetElement clickedOn;

    prePaintSelChange();

    if (isInWorkArea(x, y)) {
      clickedOn = workArea.clicked(x - paletteWidth, y);
      selFromPalette = false;
    } else {
      NetElement.deselectAll();
      clickedOn = palette.clicked(x, y);
      selFromPalette = true;
    }

    clickedOnSomething = (clickedOn != null);

    if (e.isControlDown()) {
      allowMove = false;
      if (clickedOnSomething) {
        Enumeration en = NetElement.selectedElements();

        while (en.hasMoreElements()) {
          NetElement a = (NetElement)en.nextElement();
          NetElement b = clickedOn;

          if (a != b && a != null && b != null && a.linkable && b.linkable)
            if (a instanceof Device && b instanceof Device)
              Netbuild.setStatus("!Device to device connection not allowed.");
            else if (a instanceof Device && b instanceof Connector) {
              Connection con = ((Connector)b).createConnection((Device)a);
              workArea.add(con);
              Interface iface = ((Device)a).createInterface(con);
              workArea.add(iface);
              paintThingee(con);
              paintThingee(iface);
            } else if (b instanceof Device && a instanceof Connector) {
              Connection con = ((Connector)a).createConnection((Device)b);
              workArea.add(con);
              Interface iface = ((Device)b).createInterface(con);
              workArea.add(iface);
              paintThingee(con);
              paintThingee(iface);
            } else if (a instanceof InternetConnector && b instanceof InternetConnector)
              Netbuild.setStatus("!Connector to connector connection not allowed.");
            else {
            }

        }
      }
    } else {// if (e.controlDown())
      allowMove = true;
      if (clickedOn == null) {
        if (!e.isShiftDown())
          NetElement.deselectAll();
      } else if (clickedOn.isSelected())
        if (!e.isShiftDown()) {
        } else
          clickedOn.deselect();
      else {
        if (!e.isShiftDown())
          NetElement.deselectAll();
        clickedOn.select();
      }
    }

    paintSelChange();
    startAppropriatePropertiesArea();

    //repaint();

    dragStarted = false;
  }

  private void paintThingee (NetElement t) {
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
    Enumeration en = NetElement.selectedElements();

    while (en.hasMoreElements()) {
      NetElement t = (NetElement)en.nextElement();
      wasSelected.put(t, new Integer(1));
    }
  }

  private void paintSelChange () {
    Enumeration en = NetElement.selectedElements();

    while (en.hasMoreElements()) {
      NetElement t = (NetElement)en.nextElement();

      if (wasSelected.get(t) == null) {
        paintThingee(t);
        wasSelected.remove(t);
      }
    }

    en = wasSelected.keys();

    while (en.hasMoreElements()) {
      NetElement t = (NetElement)en.nextElement();
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

        {//prevent name clash of en
          Enumeration en = NetElement.selectedElements();

          while (en.hasMoreElements()) {
            NetElement t = (NetElement)en.nextElement();
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
            NetElement t = (NetElement)NetElement.selectedElements().nextElement();
            NetElement el = t.createAnother();
            el.move(x - paletteWidth, y);
            workArea.add(el);
            NetElement.deselectAll();
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
            Enumeration en = NetElement.selectedElements();

            while (en.hasMoreElements()) {
              NetElement t = (NetElement)en.nextElement();
              if (t.trashable) {
                // into trash -- gone.
                t.deselect();
                workArea.remove(t);
                Netbuild.setStatus("Selection trashed.");
              } else if (t instanceof Interface)
                t.deselect();
            }
            repaint();
            startAppropriatePropertiesArea();

            if (workArea.getElementCount() < 1)
              exportButton.setEnabled(false);
          }
        } else {
          Enumeration en = NetElement.selectedElements();

          while (en.hasMoreElements()) {
            NetElement t = (NetElement)en.nextElement();

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
        g.drawRect(leastX, leastY, sizeX, sizeY);
      g.setPaintMode();
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

  public void init () {
    fatalError = false;
    status = "Netbuild v1.03 started.";
    me = this;
    mouseDown = false;

    setLayout(null);

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

    modify = download();

    if (!fatalError) {
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
      exportButton.setEnabled(workArea.getElementCount() > 0);
      add(exportButton);

      exportButton.setLocation(propAreaX + 8, appHeight - 24 - 2 - 2);
      exportButton.setSize(propAreaWidth - 16, 20);

      copyButton.setVisible(false);
      copyButton.setSize(propAreaWidth - 16, 20);
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

  public void upload (boolean modify) {
    try {
      URL url = new URL ( getParameter("upload_url") );
      URLConnection con = url.openConnection();
      con.setDoOutput(true);
      con.setDoInput(true);
      OutputStream oStream = con.getOutputStream();

      workArea.encode(oStream);

      InputStream iStream = con.getInputStream();
      iStream.skip(iStream.available());
      iStream.close();

      oStream.flush();
      oStream.close();

      URL backurl = new URL ( getParameter("back_url") );
      getAppletContext().showDocument(backurl);
    } catch (Exception ex) {
      System.out.println (ex) ;
      Logger.getLogger(Netbuild.class.getName()).log(Level.SEVERE, null, ex);
    }
  }

  public boolean download () {
    try {
      String urlStr = getParameter("download_url") ;
      if (urlStr == null) return false;
    } catch ( Exception ex ) {
      return false;
    }
    try {
      URL url = new URL ( getParameter("download_url") );
      URLConnection con = url.openConnection();
      con.setDoOutput(false);
      con.setDoInput(true);
      InputStream iStream = con.getInputStream();

      workArea.decode(iStream);

      iStream.close();
    } catch (IOException ex) {
      Logger.getLogger(Netbuild.class.getName()).log(Level.SEVERE, null, ex);
    }
    return true;
  }
}

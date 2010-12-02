package buildui;
/*
 * NEW CODE:
 *   Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
 *   Copyright (C) 2010 David Hock, University of Würzburg
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

import buildui.paint.FlatButton;
import buildui.paint.PropertiesArea;
import java.awt.*;
import java.awt.event.*;
import java.io.IOException;
import java.util.*;
import java.net.*;

import buildui.connectors.Connection;
import buildui.connectors.Connector;
import buildui.connectors.EmulatedConnection;
import buildui.connectors.EmulatedRouterConnection;
import buildui.connectors.HubConnector;
import buildui.connectors.RouterConnector;
import buildui.connectors.SpecialFeatureConnector;
import buildui.connectors.SwitchConnector;
import buildui.devices.ConfiguredInterface;
import buildui.devices.Device;
import buildui.devices.Interface;
import buildui.devices.KvmDevice;
import buildui.devices.OpenVzDevice;
import buildui.paint.Palette;
import buildui.paint.NetElement;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.HashSet;
import java.util.logging.Level;
import java.util.logging.Logger;

public class Netbuild extends java.applet.Applet
 implements MouseListener, MouseMotionListener, ActionListener,
 KeyListener {

  private WorkArea workArea;
  public WorkArea getWorkArea() {
    return workArea;
  }

  public void setWorkArea(WorkArea workArea) {
    this.workArea = workArea;
  }
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
  public static Color glab_red = new Color(0.5664f, 0.10156f, 0.125f);
  public static Color glab_red_light = new Color(0.5664f, 0.28516f, 0.3008f);
  private String status;
  private int appWidth, appHeight;
  private int propAreaWidth;
  private int paletteWidth;
  private int workAreaWidth;
  private int workAreaX;
  private int propAreaX;
  private FlatButton exportButton;
  private FlatButton copyButton;
  private boolean readOnly = false;
  private String versionstring="Netbuild v1.03c started.";
  private boolean tcClicked;

  private static void dialog (String title, String message) {
    Frame window = new Frame();

    // Create a modal dialog
    final Dialog d = new Dialog(window, title, false);

    // Use a flow layout
    d.setLayout(new FlowLayout());

    d.setLocation(new Point(20, 20));

    // Create an OK button
    Button ok = new Button("OK");
    ok.addActionListener(new ActionListener() {

      public void actionPerformed (ActionEvent e) {
        // Hide dialog
        d.setVisible(false);
      }
    });

    d.add(new Label(title + ": "));
    d.add(new Label(message));
    d.add(ok);

    // Show dialog
    d.pack();
    d.setVisible(true);
  }

// NEW CODE FROM HERE ON (owned by University of Kaiserslautern)
  
  public static void exception (Throwable t) {
    try {
      t.printStackTrace();
      fatalError(t.toString());
    } catch (Throwable ex) {
      t.printStackTrace();
      ex.printStackTrace();
    }
  }

  private static void fatalError (String message) {
    dialog("Fatal error", message);
  }

  private static void warningError (String message) {
    dialog("Warning", message);
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

  public static void ensureNonOverlapping() {
    me.workArea.ensureNonOverlapping();
  }

  private void startAppropriatePropertiesArea () {
    Set<PropertiesArea> oldPanels = new HashSet<PropertiesArea>();
    for (Component c: propertiesPanel.getComponents())
      if (c instanceof PropertiesArea) oldPanels.add((PropertiesArea)c);
    Set<PropertiesArea> newPanels = new HashSet<PropertiesArea>();
    newPanels.add(workArea.topologyProperties);
    for (NetElement el: NetElement.selectedElements()) {
      if (el.propertyEditable) newPanels.add(el.getPropertiesArea());
    }
    boolean exp = newPanels.size() <= 3;
    propertiesPanel.setVisible(false);
    for (PropertiesArea pa: newPanels) doittoit(true, pa, exp);
    for (PropertiesArea pa: oldPanels) if (!newPanels.contains(pa))
        doittoit(false, pa, exp);
    propertiesPanel.doLayout();
    propertiesPanel.setVisible(true);
  }

// OLD CODE FROM HERE ON (owned by Emulab)

  private boolean isInWorkArea (int x, int y) {
    return x > workAreaX && y > 0 && x < workAreaX + workAreaWidth && y < appHeight;
  }

  public static void redrawAll () {
    me.repaint();
  }

  public static void setStatus (String newStatus) {
    me.status = newStatus;
    me.repaint(me.workAreaX + 4, 420, 640 - (me.workAreaX + 4), 60);
    me.repaint();
  }

  public static Image getImage (String name) {
    try {
      URL url = Netbuild.class.getResource(name);
      Image im = me.getImage(url);
      if (im == null) System.out.println("Failed to load image.");
      return im;
    } catch (Exception e) {
      Netbuild.exception (e) ;
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
    if (readOnly) return;
    if (!mouseDown) return;
    Graphics g = getGraphics();
    g.setXORMode(Color.white);

    if (clickedOnSomething) {
      if (allowMove) {
        if (dragStarted) {
          if (palette.hitTrash(lastDragX + downX, lastDragY + downY))
            palette.funktasticizeTrash(g);
          for (NetElement el: NetElement.selectedElements()) {
            if (el.moveable || el.trashable)
              if (selFromPalette)
                g.drawRect(el.getX() + lastDragX - 16, el.getY() + lastDragY - 16, 32, 32);
              else
                g.drawRect(el.getX() + lastDragX - 16 + workAreaX,
                 el.getY() + lastDragY - 16,
                 32, 32);
          }
        }

        dragStarted = true;

        lastDragX = e.getX() - downX;
        lastDragY = e.getY() - downY;

        if (palette.hitTrash(e.getX(), e.getY()))
          palette.funktasticizeTrash(g);

        for (NetElement el: NetElement.selectedElements()) {
          if (el.moveable || el.trashable)
            if (selFromPalette)
              g.drawRect(el.getX() + lastDragX - 16, el.getY() + lastDragY - 16, 32, 32);
            else
              g.drawRect(el.getX() + lastDragX - 16 + workAreaX,
               el.getY() + lastDragY - 16,
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
    if (readOnly) return;
    if (e.getSource() == exportButton) {
      startAppropriatePropertiesArea(); // make sure strings are up'd
      upload(modify);
    }
  }

  public void mousePressed (MouseEvent e) {
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
			clickedOn = palette.clicked(x, y);
			if (!(clickedOn instanceof TopologyCreatorElement))
				NetElement.deselectAll();
      selFromPalette = true;
		}

    clickedOnSomething = (clickedOn != null);
    
    if (clickedOnSomething && clickedOn instanceof TopologyCreatorElement) {
    	ArrayList<Device> temp = new ArrayList<Device>();
      int minx=Integer.MAX_VALUE;
      int miny=Integer.MAX_VALUE;
      int maxx=Integer.MIN_VALUE;
      int maxy=Integer.MIN_VALUE;
    	for (NetElement nE:NetElement.selectedElements()) {
    		if (nE instanceof Device)	{
    			temp.add((Device)nE);
    			minx=Math.min(nE.getX(),minx);
    			miny=Math.min(nE.getX(),miny);
    			maxx=Math.max(nE.getX(),maxx);
    			maxy=Math.max(nE.getX(),maxy);
    		}
    	}    		
			if (temp.size() == 0) {
				tcClicked = true;
				mouseDown = false;
				Netbuild.setStatus("Please select the area where the topology should be created. Click anywhere to use entire area.");
				return;
			} else {
				mouseDown = false;
				TopologyCreatorElement.open(me,minx, miny, maxx-minx, maxy-miny,temp);
				return;
			}
    		
    }

    if (e.isControlDown()) {
      if (readOnly) return;
      allowMove = false;
      if (clickedOnSomething) {
        for (NetElement a: NetElement.selectedElements()) {
          NetElement b = clickedOn;
          connect ( a, b );
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

  private void connect ( NetElement a, NetElement b ) {
    if (a != b && a != null && b != null && a.linkable && b.linkable) {
      if (a instanceof Device && b instanceof Device) {
        SwitchConnector sw = new SwitchConnector () ;
        workArea.add(sw);
        connect(a, sw);
        connect(b, sw);
        paintElement(sw);
      } else if (a instanceof Device && b instanceof Connector) {
        Connection con = ((Connector)b).createConnection((Device)a);
        Interface iface = ((Device)a).createInterface(con);
        con.setIface(iface);
        workArea.add(iface);
        workArea.add(con);
        paintElement(con);
        paintElement(iface);
      } else if (b instanceof Device && a instanceof Connector) {
        connect(b, a);
      } else if (a instanceof Connector && b instanceof Connector)
        Netbuild.setStatus("!Connector to connector connection not allowed.");
    }
  }

  public static void repaintElement (NetElement t) {
    me.paintElement(t);
  }

  private void paintElement (NetElement t) {
    Rectangle r = t.getRectangle();

    // HACK!
    if (palette.has(t))
      repaint(r.x, r.y, r.width, r.height);
    else
      repaint(r.x + workAreaX, r.y, r.width, r.height);
  }
  private Set<NetElement> wasSelected;

  private void prePaintSelChange () {
    wasSelected = new HashSet<NetElement>();
    wasSelected.addAll(NetElement.selectedElements());
  }

  private void paintSelChange () {
    for (NetElement el: NetElement.selectedElements()) {
      if (!wasSelected.contains(el)) {
        paintElement(el);
        wasSelected.remove(el);
      }
    }
    for (NetElement el: wasSelected) paintElement(el);
  }

  public void mouseReleased (MouseEvent e) {
    if (!mouseDown) return;
    mouseDown = false;
    if (clickedOnSomething) {
    	tcClicked=false;
      Netbuild.setStatus(""); 
      if (dragStarted) {
        Graphics g = getGraphics();
        g.setXORMode(Color.white);

        if (palette.hitTrash(lastDragX + downX, lastDragY + downY)) palette.funktasticizeTrash(g);

        for (NetElement el: NetElement.selectedElements()) {
          if (el.moveable || el.trashable)
            if (selFromPalette)
              g.drawRect(el.getX() + lastDragX - 16, el.getY() + lastDragY - 16, 32, 32);
            else
              g.drawRect(el.getX() + lastDragX - 16 + workAreaX,
               el.getY() + lastDragY - 16,
               32, 32);
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
            NetElement t = NetElement.selectedElements().iterator().next();
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
            for (NetElement el: new HashSet<NetElement>(NetElement.selectedElements())) {
              if (el.trashable) {
                // into trash -- gone.
                el.deselect();
                workArea.remove(el);
                Netbuild.setStatus("Selection trashed.");
              } else if (el instanceof Interface)
                el.deselect();
            }
            repaint();
            startAppropriatePropertiesArea();

            if (workArea.getElementCount() < 1)
              exportButton.setEnabled(false);
          }
        } else {
          for (NetElement el: NetElement.selectedElements()) {
            if (el.moveable) {
                el.move(el.getX() + lastDragX, el.getY() + lastDragY);
                el.onPropertyChanged("pos", "", el.getX()+","+el.getY());
            }
            repaint();
          }
        }
        ensureNonOverlapping();
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

        if (tcClicked){
        	tcClicked=false;
        	Netbuild.setStatus("");
        	if (NetElement.selectedElements().size()==0) {
        		if (leastX>=workAreaX && sizeX<workAreaWidth)
        			TopologyCreatorElement.open(me,leastX-workAreaX, leastY, sizeX, sizeY,new ArrayList<Device>());
        		else Netbuild.setStatus("!Topology creator can only be started inside work area.");
        	} else Netbuild.setStatus("!Topology creator can only be started for empty area.");        	
          return;
        }        
        
        paintSelChange();
        startAppropriatePropertiesArea();
      } else {
				if (tcClicked && leastX > workAreaX) {
					TopologyCreatorElement.open(me, 50, 50, 500, 500,new ArrayList<Device>());
					tcClicked = false;
				}
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

  public static boolean isReadOnly() {
    return me.readOnly;
  }

    @Override
  public void init () {
    try {
      status = versionstring;

      me = this;

      Connection.init(me);
      EmulatedConnection.init(me);
      EmulatedRouterConnection.init(me);
      HubConnector.init(me);
      SwitchConnector.init(me);
      RouterConnector.init(me);
      Interface.init(me);
      ConfiguredInterface.init(me);
      Device.init(me);
      KvmDevice.init(me);
      OpenVzDevice.init(me);
      SpecialFeatureConnector.init(me);
      Modification.clear();

      mouseDown = false;

      setLayout(null);

      addMouseListener(this);
      addMouseMotionListener(this);
      addKeyListener(this);

      Dimension d = getSize();

      appWidth = 800;
      appHeight = 600;

      propAreaWidth = 160;
      paletteWidth = 80;
      workAreaWidth = appWidth - propAreaWidth - paletteWidth;

      workArea = new WorkArea();
      palette = new Palette();
      propertiesPanel = new Panel();

      modify = download();
      readOnly = getParameter("upload_url") == null;

      dragStarted = false;

      workAreaX = paletteWidth;

      propAreaX = paletteWidth + workAreaWidth;

      setBackground(Color.WHITE);
      propertiesPanel.setBackground(Color.WHITE);
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

      propertiesPanel.setLocation(propAreaX + 8, 0 + 8);
      propertiesPanel.setSize(propAreaWidth - 16, appHeight - 16 - 32);

      exportButton.setVisible(!readOnly);
      exportButton.setEnabled(workArea.getElementCount() > 0 && !readOnly);
      add(exportButton);

      exportButton.setLocation(propAreaX + 8, appHeight - 24 - 2 - 2);
      exportButton.setSize(propAreaWidth - 16, 20);

      copyButton.setVisible(false);
      copyButton.setSize(propAreaWidth - 16, 20);

    } catch ( Exception ex ) {
      exception (ex);
    }
  }

  public void paint (Graphics g) {
    if (status.compareTo("") != 0 && status.charAt(0) == '!') g.setColor(Color.red);

    g.drawString(status, workAreaX + 4, appHeight - 6);

    palette.paint(g);

    g.setColor(Color.black);
    g.fillRect(propAreaX + 8 - 3, appHeight - 24 - 2 - 8,
     propAreaWidth - 16 + 6, 1);

    g.setColor(Color.darkGray);
    g.fillRect(propAreaX + 8 - 3, appHeight - 24 - 2 - 7,
     propAreaWidth - 16 + 6, 1);

    g.setColor(glab_red);
    g.drawRect(0, 0, appWidth-1, appHeight-1);
    g.drawRect(0, 0, paletteWidth, appHeight);
    g.drawRect(workAreaX, 0, workAreaWidth, appHeight);
    g.drawRect(propAreaX, 0, propAreaWidth, appHeight);

    g.translate(workAreaX, 0);
    g.setClip(1, 1, workAreaWidth - 1, appHeight - 1);
    workArea.paint(g);
    g.translate(-workAreaX, 0);
    g.setClip(0, 0, appWidth, appHeight);

    super.paint(g);
  }

 // NEW CODE FROM HERE ON (owned by University of Kaiserslautern)

  public void upload (boolean modify) {
    try {
      readOnly = true;
      exportButton.setEnabled(false);
      exportButton.setText("sending...");
      exportButton.repaint();
      ByteArrayOutputStream baos = new ByteArrayOutputStream();
      Modification.encodeModifications(baos);
      String xml = baos.toString();
      
      URL base = getDocumentBase();
      URL url = new URL ( base, getParameter("upload_url") );
      HttpURLConnection con = (HttpURLConnection)url.openConnection();
      con.setRequestProperty("Authorization", getParameter("auth"));
      con.setDoOutput(true);
      con.setDoInput(true);

      OutputStream oStream = con.getOutputStream();
      oStream.write("xml=".getBytes());
      oStream.write(URLEncoder.encode(xml, "utf-8").getBytes());
      oStream.write("\n".getBytes());
      oStream.flush();
      oStream.close();
      
      String[] reply = parseReply(con.getInputStream());
      if ( reply != null ) {
        String kind = reply[2] ;
        if ( kind.equals("TOPOLOGY") ) {
          String id = reply[3] ;
          String task = reply[4] ;
          String backstr = getParameter("back_url");
          backstr = backstr.replace("12345", id);
          con.disconnect();
          URL backurl = new URL ( base, backstr );
          if (isActive()) {
            getAppletContext().showDocument(backurl);
            Thread.sleep(100);
          }
          return;
        } else if ( kind.equals("ERROR") ) {
          String code = reply[3] ;
          String message = reply[4] ;
          dialog("Error", code + ": " + message);
        }
      }
    } catch (Exception ex) {
      exception (ex) ;
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
      URL base = getDocumentBase();
      URL url = new URL ( base, getParameter("download_url") );
      HttpURLConnection con = (HttpURLConnection)url.openConnection();
      con.setRequestProperty("Authorization", getParameter("auth"));
      con.setDoOutput(false);
      con.setDoInput(true);
      InputStream iStream = con.getInputStream();

      workArea.decode(iStream);

      con.disconnect();
    } catch (Exception ex) {
      exception (ex) ;
      Logger.getLogger(Netbuild.class.getName()).log(Level.SEVERE, null, ex);
    }
    return true;
  }

  public String[] parseReply(InputStream in) {
    try {
      BufferedReader reader = new BufferedReader(new InputStreamReader(in));
      while (reader.ready()) {
        String s = reader.readLine();
        System.out.println(s);
        if ( s.contains("%%%GLABNETMAN%%%") ) return s.split("%%%");
      }
      return null;
    } catch (IOException ex) {
      exception(ex);
      Logger.getLogger(Netbuild.class.getName()).log(Level.SEVERE, null, ex);
      return null;
    }
  }
}

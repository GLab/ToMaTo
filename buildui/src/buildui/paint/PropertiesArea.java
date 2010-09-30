package buildui.paint;
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

import buildui.Netbuild;
import buildui.paint.NetElement;
import java.awt.*;
import java.awt.event.*;
import java.util.*;

public abstract class PropertiesArea extends Panel implements ActionListener {

  private Panel child;
  private GridBagLayout childLayout;
  private GridBagConstraints gbc;
  public EditElement nameEdit;
  private boolean started;
  private boolean childVisible;
  private Expando expando;
  private Vector currentThingees;

  public boolean isStarted () {
    return started;
  }

  private void setVisibleAll (boolean b) {
    childVisible = b;
    validate();
    invalidate();

    getParent().doLayout();
    //child.setVisible(b);
    //doLayout();
  }

  public void hideProperties () {
    setVisibleAll(false);
    expando.setState(false);
  }

  public void showProperties () {
    setVisibleAll(true);
    expando.setState(true);
  }

  public void actionPerformed (ActionEvent e) {
    if (e.getSource() == expando)
      if (e.getID() == ActionEvent.ACTION_PERFORMED)
        setVisibleAll(0 == e.getActionCommand().compareTo("down"));
  }

  public void addComponent (Component c) {
    childLayout.setConstraints(c, gbc);
    child.add(c);
  }

  private Vector<Property> propertyList;

  class Property {
    public String name;
    public String def;
    public EditElement editElement;
    public boolean alphic;
  }

  public void valueChanged (EditElement el, String value) {
    upload();
    if (nameEdit != null && el != null && el == nameEdit) { // hack.
      Component parent = getParent();
      if (parent != null) parent.repaint();
    }
  }

// NEW CODE FROM HERE ON (owned by University of Kaiserslautern)
  
  public void addTextProperty (String name, String desc, String pattern, String def) {
    Property p = new Property();
    p.name = name;
    p.def = def;
    p.editElement = new MagicTextField(this, desc, pattern, def);
    if (0 == name.compareTo("name")) nameEdit = (MagicTextField)p.editElement;
    propertyList.addElement(p);
  }

  public void addSelectProperty (String name, String desc, String[] options, String def) {
    addSelectProperty(name, desc, Arrays.asList(options), def);
  }

  public void addSelectProperty (String name, String desc, Collection<String> options, String def) {
    Property p = new Property();
    p.name = name;
    p.def = def;
    p.editElement = new DropDownField(this, desc, options, def);
    propertyList.addElement(p);
  }

  public void addBoolProperty (String name, String desc, boolean def) {
    Property p = new Property();
    p.name = name;
    p.def = def ? "true" : "false" ;
    p.editElement = new CheckboxField(this, desc, def);
    propertyList.addElement(p);
  }

// OLD CODE FROM HERE ON (owned by Emulab)

  public PropertiesArea () {
    super();
    child = new Panel();

    setVisible(true);
    started = false;
    expando = new Expando(getName());
    expando.addActionListener(this);
    propertyList = new Vector<Property>();
    nameEdit = null;

    setLayout(null);

    gbc = new GridBagConstraints();
    gbc.fill = GridBagConstraints.BOTH;
    gbc.weightx = 1.0;
    gbc.gridwidth = GridBagConstraints.REMAINDER;

    childLayout = new GridBagLayout();
    child.setLayout(childLayout);
    currentThingees = null;

    expando.setVisible(true);
    child.setVisible(true);
    add(expando);
    add(child);
    childVisible = true;
  }

  public void doLayout () //    public void myLayout()
  {
    Dimension d = expando.getPreferredSize();
    expando.setSize(640 - 480 - 16, d.height);
    expando.setLocation(0, 0);
    Dimension d2 = child.getPreferredSize();
    child.setLocation(2, d.height + 2);
    if (childVisible) child.setSize(640 - 480 - 16 - 2, d2.height);
    else child.setSize(640 - 480 - 16 - 2, 0);
    setSize(640 - 480 - 16, d.height + d2.height + 2);
  }

  public Dimension getPreferredSize () {
    Dimension d = expando.getPreferredSize();
    Dimension d2 = child.getPreferredSize();
    if (childVisible) return new Dimension(640 - 480 - 16, d.height + d2.height + 2);
    else return new Dimension(640 - 480 - 16, d.height);
  }

  public abstract boolean iCare (NetElement t);

  public abstract String getName ();

  private synchronized void download () {
    currentThingees = null;
    Vector<NetElement> elements = new Vector<NetElement>();

    int thingsICareAbout = 0;

    boolean first = true;
    for (NetElement el: NetElement.selectedElements()) {
      if (iCare(el)) {
        thingsICareAbout++;
        elements.addElement(el);

        for (Property p: propertyList) {
          String value = el.getProperty(p.name, p.def);
          if (value == null) value = "";
          if (first) p.editElement.setValue(value);
          else if (0 != p.editElement.getValue().compareTo(value)) p.editElement.setValue("<multiple>");
        }
        first = false;
      }
    }


    if (thingsICareAbout > 1) {
      if (nameEdit != null) nameEdit.setEnabled(false);
    } else if (nameEdit != null) {
      if (thingsICareAbout == 1 && (elements.elementAt(0)).nameFixed()) nameEdit.setEnabled(false);
      else nameEdit.setEnabled(true);
    }

    currentThingees = elements;
    //	System.out.println( "PropertiesArea.download(): Ending");
    if ( Netbuild.isReadOnly() ) for (Property p: propertyList) p.editElement.setEnabled(false);

  }

  public synchronized void upload () {
    //	System.out.println("Upload begins..");
    if (currentThingees == null || Netbuild.isReadOnly()) return;

    Enumeration et = currentThingees.elements();

    boolean needRedraw = false;
    while (et.hasMoreElements()) {
      //	    System.out.println( "PropertiesArea.upload(): Regarding a thingee.");
      NetElement t = (NetElement)et.nextElement();

      //if (iCare(t)) {
      Enumeration e = propertyList.elements();

      while (e.hasMoreElements()) {
        Property p = (Property)e.nextElement();
        if (p.editElement.isEnabled()) {
          String s = p.editElement.getValue();
          if (0 != s.compareTo("<multiple>")) {
            if (p.name.compareTo("name") == 0 && t.getName().compareTo(s) != 0)
              needRedraw = true;

            // System.out.println(
            //  "PA.upload(): Setting prop \"" +
            //  p.name +
            //  "\" to \"" + s + "\"." );
            t.setProperty(p.name, s);
          }
        }
      }
      //}
    }
    if (needRedraw)
      Netbuild.redrawAll();
    //	System.out.println("Upload ends..");
  }

  public void refresh () {
    upload();
    download();
  }

  public void start () {
    started = true;
    download();
    validate();

    invalidate();
    getParent().doLayout();
  }

  public void stop () {
    started = false;
    upload();

  }
};

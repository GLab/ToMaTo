package buildui.paint;
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

import buildui.Netbuild;
import java.awt.*;
import java.awt.event.*;
import java.util.*;

public abstract class PropertiesArea extends Panel implements TextListener, ActionListener {

  private Panel child;
  private GridBagLayout layout;
  private GridBagLayout childLayout;
  private GridBagConstraints gbc;
  private MagicTextField nameEdit;
  private boolean started;
  private boolean childVisible;
  private Expando expando;
  private Vector currentThingees;
  private static Color darkBlue;
  private static Color disabledBox;

  public boolean isStarted () {
    return started;
  }

  static {
    darkBlue = new Color(0.3f, 0.3f, 0.5f);
    //	disabledBox = new Color( 0.5f, 0.5f, 0.65f );
    disabledBox = new Color(0.7f, 0.7f, 0.85f);
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

  private MagicTextField addField (String name, boolean alphic, boolean special, final String def) {
    final MagicTextField tf = new MagicTextField(alphic, !alphic, special);
    Label l = new Label(name);

    l.setForeground(Color.white);
    tf.tf.setBackground(Color.white);

    childLayout.setConstraints(l, gbc);
    child.add(l);
    childLayout.setConstraints(tf.tf, gbc);
    child.add(tf.tf);
    tf.tf.addTextListener(this);

    if (name.compareTo("name:") != 0 && def != null ) {
      final PropertiesArea propertiesArea = this;
      FlatButton fb = new FlatButton("default") {

        public Dimension getPreferredSize () {
          return new Dimension(72, 18);
        }

        protected void clicked () {
          boolean wasDis = !tf.tf.isEditable();
          if (wasDis) tf.tf.setEditable(true);
          tf.tf.setText(def);
          propertiesArea.upload();
          if (wasDis) tf.tf.setEditable(false);
        }
      };

      Panel p = new Panel();
      p.setLayout(new FlowLayout(FlowLayout.RIGHT, 0, 0));
      p.add(fb);

      childLayout.setConstraints(p, gbc);
      child.add(p);

      fb.setVisible(true);
    }

    tf.tf.setVisible(true);
    l.setVisible(true);

    return tf;
  }
  private Vector propertyList;

  class Property {

    public String name;
    public String def;
    public MagicTextField textField;
    public boolean alphic;
  }

  public void textValueChanged (TextEvent e) {
    upload();
    if (nameEdit != null && e.getSource() != null
     && e.getSource() == nameEdit.tf) { // hack.
      Component parent = getParent();
      if (parent != null)
        parent.repaint();
    }
  }

  public void addProperty (String name, String desc, String def, boolean alphic, boolean special) {
    Property p = new Property();
    p.name = name;
    p.def = def;
    p.alphic = alphic;
    p.textField = addField(desc, alphic, special, def);
    if (0 == name.compareTo("name")) nameEdit = p.textField;
    propertyList.addElement(p);
  }

  public PropertiesArea () {
    super();
    child = new Panel();

    //setVisible( false );
    setVisible(true);
    started = false;
    setBackground(darkBlue);
    child.setBackground(darkBlue);
    //child.setBackground( Color.red );
    //setBackground( Color.green );
    expando = new Expando(getName());
    expando.addActionListener(this);
    propertyList = new Vector();
    nameEdit = null;

    //layout = new GridBagLayout();
    //setLayout( layout );

    setLayout(null);

    gbc = new GridBagConstraints();
    gbc.fill = GridBagConstraints.BOTH;
    gbc.weightx = 1.0;
    gbc.gridwidth = GridBagConstraints.REMAINDER;

    //layout.setConstraints( expando, gbc );


    childLayout = new GridBagLayout();
    child.setLayout(childLayout);
    //child.setVisible( true );
    //layout.setConstraints( child, gbc );
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
    if (childVisible)
      child.setSize(640 - 480 - 16 - 2, d2.height);
    else
      child.setSize(640 - 480 - 16 - 2, 0);
    setSize(640 - 480 - 16, d.height + d2.height + 2);
  }

  public Dimension getPreferredSize () {
    Dimension d = expando.getPreferredSize();
    Dimension d2 = child.getPreferredSize();
    if (childVisible)
      return new Dimension(640 - 480 - 16, d.height + d2.height + 2);
    else
      return new Dimension(640 - 480 - 16, d.height);
  }

  public abstract boolean iCare (NetElement t);

  public abstract String getName ();

  private synchronized void download () {
    //	System.out.println( "PropertiesArea.download(): Beginning");
    Enumeration et = NetElement.selectedElements();

    //currentThingees = new Vector();
    currentThingees = null;
    Vector cThingees = new Vector();

    int thingsICareAbout = 0;

    MagicTextField ipEdit = null;

    boolean first = true;
    while (et.hasMoreElements()) {
      NetElement t = (NetElement)et.nextElement();

      if (iCare(t)) {
        Enumeration e = propertyList.elements();

        thingsICareAbout++;
        cThingees.addElement(t);

        while (e.hasMoreElements()) {
          Property p = (Property)e.nextElement();

          if (p.name.compareTo("ip") == 0)
            ipEdit = p.textField;

          String value = t.getProperty(p.name, p.def);

          if (first)
            p.textField.setText(value);
          else if (0 != p.textField.tf.getText().compareTo(value))
            p.textField.setText("<multiple>");
        }
        first = false;
      }
    }


    if (thingsICareAbout > 1) {
      if (nameEdit != null) {
        nameEdit.tf.setEditable(false);
        nameEdit.tf.setBackground(disabledBox);
      }

      if (ipEdit != null) {
        ipEdit.tf.setEditable(false);
        ipEdit.tf.setBackground(disabledBox);
      }
    } else {
      if (nameEdit != null)
        if (thingsICareAbout == 1 && ((NetElement)cThingees.elementAt(0)).nameFixed()) {
          nameEdit.tf.setEditable(false);
          nameEdit.tf.setBackground(disabledBox);
        } else {
          nameEdit.tf.setEditable(true);
          nameEdit.tf.setBackground(Color.white);
        }

      if (ipEdit != null) {
        ipEdit.tf.setEditable(true);
        ipEdit.tf.setBackground(Color.white);
      }
    }

    currentThingees = cThingees;
    //	System.out.println( "PropertiesArea.download(): Ending");
  }

  private synchronized void upload () {
    //	System.out.println("Upload begins..");
    if (currentThingees == null) return;

    Enumeration et = currentThingees.elements();

    boolean needRedraw = false;
    while (et.hasMoreElements()) {
      //	    System.out.println( "PropertiesArea.upload(): Regarding a thingee.");
      NetElement t = (NetElement)et.nextElement();

      //if (iCare(t)) {
      Enumeration e = propertyList.elements();

      while (e.hasMoreElements()) {
        Property p = (Property)e.nextElement();
        if (p.textField.tf.isEditable()) {
          String s = p.textField.tf.getText();
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
    //setVisible( true );
    download();
    //child.setVisible( true );
    //myLayout();//doLayout();
    validate();

    invalidate();
    getParent().doLayout();
  }

  public void stop () {
    started = false;
    //setVisible( false );
    upload();

  }
};

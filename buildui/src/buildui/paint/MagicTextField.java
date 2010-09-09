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
import java.util.regex.Pattern;

public class MagicTextField implements EditElement, TextListener, FocusListener {

  public TextField textField;
  private boolean wasAuto;
  private String pattern;
  private static Color darkGreen = new Color(0.0f, 0.33f, 0.0f);
  private PropertiesArea parent ;
  private FlatButton fb;

  public static final String identifier_pattern = "(?:[0-9a-zA-Z_-]*)" ;
  public static final String numeric_pattern = "(?:[0-9]|[1-9][0-9]*)" ;
  public static final String fp_numeric_pattern = numeric_pattern+"\\."+numeric_pattern ;
  public static final String ip4_pattern = "(?:(?:(?:25[0-6]|2[0-4][0-9]|[01]?[0-9]?[0-9])\\.){3}(?:25[0-6]|2[0-4][0-9]|[01]?[0-9]?[0-9]))" ;
  public static final String ip4_prefix_pattern = ip4_pattern + "/(?:3[0-2]|[12]?[0-9])" ;

  public void focusGained (FocusEvent f) {
    textField.selectAll();
  }

  public void focusLost (FocusEvent f) {
  }

  public MagicTextField(final PropertiesArea parent, String name, String pattern, final String def) {
    this.parent = parent;

    textField = new TextField();
    textField.addTextListener(this);
    textField.addFocusListener(this);
    wasAuto = false;
    this.pattern = pattern;

    Label label = new Label(name);

    label.setForeground(Netbuild.glab_red);
    textField.setBackground(Color.white);

    parent.addComponent(label);
    parent.addComponent(textField);

    if (name.compareTo("name:") != 0 && def != null ) {
      fb = new FlatButton("default") {
        public Dimension getPreferredSize () {
          return new Dimension(72, 18);
        }
        protected void clicked () {
          boolean wasDis = !textField.isEditable();
          if (wasDis) textField.setEditable(true);
          textField.setText(def);
          parent.upload();
          if (wasDis) textField.setEditable(false);
        }
      };
      Panel p = new Panel();
      p.setLayout(new FlowLayout(FlowLayout.RIGHT, 0, 0));
      p.add(fb);
      parent.addComponent(p);
      fb.setVisible(true);
    }

    textField.setVisible(true);
    label.setVisible(true);
  }

  public void setValue (String t) {
    wasAuto =
     (0 == t.compareTo("<auto>")) || (0 == t.compareTo("<multiple>"));
    textField.setText(t);
  }

  public void textValueChanged (TextEvent e) {
    String newText = textField.getText();

    if (0 == newText.compareTo("<auto>"))
      //wasAuto = true;
      textField.setForeground(Color.blue);
    else if (0 == newText.compareTo("<multiple>"))
      textField.setForeground(darkGreen);
    else {
      textField.setForeground(Color.black);
      if (wasAuto) wasAuto = false;
      if (!Pattern.matches(pattern, newText)) textField.setForeground(Color.RED);
    }
    parent.valueChanged(this, newText);
  }

  public String getValue () {
    return textField.getText();
  }

  public void setEnabled (boolean enabled) {
    textField.setEditable(enabled);
    if (enabled) textField.setBackground(Color.white);
    else textField.setBackground(Color.LIGHT_GRAY);
    if ( fb != null ) fb.setEnabled(enabled);
  }

  public boolean isEnabled () {
    return textField.isEditable();
  }

}
    

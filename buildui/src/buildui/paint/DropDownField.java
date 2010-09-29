package buildui.paint;
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

import buildui.Netbuild;
import java.awt.*;
import java.awt.event.*;
import java.util.Collection;
import java.util.regex.Pattern;

public class DropDownField implements EditElement, ItemListener {

  public Choice dropDown;
  private boolean wasAuto;
  private static Color darkGreen = new Color(0.0f, 0.33f, 0.0f);
  private Collection<String> options ;

  public DropDownField(final PropertiesArea parent, String name, Collection<String> options, final String def) {
    dropDown = new Choice();
    this.options = options ;
    dropDown.addItemListener(this);
    wasAuto = false;
    setValue(def);

    Label label = new Label(name);

    label.setForeground(Netbuild.glab_red);
    dropDown.setBackground(Color.white);

    parent.addComponent(label);
    parent.addComponent(dropDown);

    dropDown.setVisible(true);
    label.setVisible(true);
  }

  public void setValue (String t) {
    wasAuto = (0 == t.compareTo("<auto>")) || (0 == t.compareTo("<multiple>"));
    dropDown.removeAll();
    if ( ! options.contains(t) ) dropDown.add(t);
    for ( String s : options ) dropDown.addItem(s);
    dropDown.select(t);
    itemStateChanged(null);
  }

  public String getValue () {
    return dropDown.getSelectedItem();
  }

  public void setEnabled (boolean enabled) {
    dropDown.setEnabled(enabled);
    if (enabled) dropDown.setBackground(Color.white);
    else dropDown.setBackground(Color.LIGHT_GRAY);
  }

  public boolean isEnabled () {
    return dropDown.isEnabled();
  }

  public void itemStateChanged (ItemEvent e) {
    String newText = dropDown.getSelectedItem();

    if (0 == newText.compareTo("<auto>"))
      //wasAuto = true;
      dropDown.setForeground(Color.blue);
    else if (0 == newText.compareTo("<multiple>"))
      dropDown.setForeground(darkGreen);
    else {
      dropDown.setForeground(Color.black);
      if (wasAuto) wasAuto = false;
    }
  }

}
    

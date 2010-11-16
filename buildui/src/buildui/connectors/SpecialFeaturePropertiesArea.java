package buildui.connectors;

import buildui.paint.DropDownField;
import buildui.paint.EditElement;
import buildui.paint.MagicTextField;
import buildui.paint.PropertiesArea;
import buildui.paint.NetElement;
import java.util.ArrayList;
import java.util.List;

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

public class SpecialFeaturePropertiesArea extends PropertiesArea {

  public boolean iCare (NetElement t) {
    return (t instanceof SpecialFeatureConnector);
  }

  public String getName () {
    return "Special feature properties";
  }

  protected DropDownField groupDD ;
  protected EditElement typeDD ;

  public SpecialFeaturePropertiesArea () {
    super();
    addTextProperty("name", "name:", MagicTextField.identifier_pattern, null);
    typeDD = addSelectProperty("feature_type", "type:", SpecialFeatureConnector.types, "");
    groupDD = addSelectProperty("feature_group", "group:", new String[0], "<auto>");
  }

  @Override
  public void valueChanged(EditElement el, String newValue) {
    System.out.println (el);
    if ( el.equals(typeDD) ) {
        List<String> options = SpecialFeatureConnector.groups.get(newValue);
        if (options == null) options = new ArrayList<String>();
        groupDD.changeOptions(options);
    }
  }
};

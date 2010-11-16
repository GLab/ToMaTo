package buildui.connectors;
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
import buildui.devices.Device;
import buildui.paint.NetElement;

import buildui.paint.PropertiesArea;
import java.applet.Applet;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import org.w3c.dom.Element;

public class SpecialFeatureConnector extends Connector {

  static int num;
  static PropertiesArea propertiesArea ;
  static HashSet<String> types = new HashSet<String>();
  static HashMap<String, List<String>> groups = new HashMap<String, List<String>>();

  public static void init ( Applet parent ) {
    types.clear();
    groups.clear();
    if (parent.getParameter("special_features").length() >= 2) {
        for (String f: parent.getParameter("special_features").split(",")) {
            String type = f.split(":")[0];
            types.add(type);
            ArrayList<String> list = new ArrayList<String> ();
            list.add("<auto>");
            list.addAll(Arrays.asList(f.split(":")[1].split("\\|")));
            groups.put(type, list);
        }
    }
    num = 0;
    propertiesArea = new SpecialFeaturePropertiesArea();
  }

  public SpecialFeatureConnector () {
    this("special"+num);
  }

  private String getImage() {
      if ( getFeatureType().equals("internet")) return "/icons/internet.png" ;
      if ( getFeatureType().equals("openflow")) return "/icons/openflow.png" ;
      return "/icons/special.png" ;
  }

  public SpecialFeatureConnector (String newName) {
    this(newName, "special");
  }

  public SpecialFeatureConnector (String newName, String type) {
    super(newName, "/icons/special.png");
    num++;
    setProperty("feature_type", type);
    icon = loadIcon(getImage());
  }

  public NetElement createAnother () {
    return new SpecialFeatureConnector("special"+num) ;
  }

  public PropertiesArea getPropertiesArea() {
    return propertiesArea ;
  }

  @Override
  public Connection createConnection (Device dev) {
    return new Connection("", this, dev);
  }

  public static Connector readFrom (Element x_con) {
    String name = x_con.getAttribute("name") ;
    SpecialFeatureConnector con = new SpecialFeatureConnector(name);
    con.readAttributes(x_con);
    return con ;
  }

  public void readAttributes (Element xml) {
    super.readAttributes(xml);
    setProperty("feature_type", xml.getAttribute("feature_type"));
    setProperty("feature_type", getProperty("feature_type", "special"));
    setProperty("feature_group", xml.getAttribute("feature_group"));
    setProperty("feature_group", getProperty("feature_group", "<auto>"));
    icon = loadIcon(getImage());
  }

  public void onPropertyChanged(String property, String oldValue, String newValue) {
      if (property.equals("feature_type")) {
          properties.put(property, newValue);
          String newName = getName().replace(oldValue, newValue);
          if ( ! getName().equals(newName) ) {
              super.onNameChanged(getName(), newName);
              setName(newName);
          }
          icon = loadIcon(getImage());
          Netbuild.redrawAll();
      }
      super.onPropertyChanged(property, oldValue, newValue);
  }

    public String getFeatureType() {
        return getProperty("feature_type", "special");
    }

    @Override
    public String getType() {
        return "special";
    }

}

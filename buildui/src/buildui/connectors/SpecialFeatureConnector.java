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
import java.util.Arrays;
import java.util.HashSet;
import org.w3c.dom.Element;

public class SpecialFeatureConnector extends Connector {

  static int num;
  static PropertiesArea propertiesArea ;
  static HashSet<String> types = new HashSet<String>();
  static HashSet<String> groups = new HashSet<String>();

  public static void init ( Applet parent ) {
    types.clear();
    groups.clear();
    groups.add("<auto>");
    for (String f: parent.getParameter("special_features").split(",")) {
        types.add(f.split(":")[0]);
        groups.addAll(Arrays.asList(f.split(":")[1].split("\\|")));
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
    super(newName, "/icons/special.png");
    num++;
    setProperty("feature_type", "special");
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
  }

  public void onPropertyChanged(String property, String oldValue, String newValue) {
      if (property.equals("feature_type")) {
          properties.put(property, newValue);
          System.out.println (oldValue + "->" + newValue);
          String newName = getName().replace(oldValue, newValue);
          if ( ! getName().equals(newName) ) setName(newName);
          System.out.println(getName());
          System.out.println(getImage());
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

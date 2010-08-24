package buildui.devices;

import buildui.paint.PropertiesArea;
import buildui.paint.NetElement;

public class OpenVzPropertiesArea extends PropertiesArea {

  public boolean iCare (NetElement t) {
    return (t instanceof OpenVzDevice);
  }

  public String getName () {
    return "OpenVZ properties";
  }

  public OpenVzPropertiesArea () {
    super();
    addProperty("name", "name:", "", true, false);
    addProperty("hostgroup", "hostgroup:", "<auto>", true, false);
    addProperty("template", "template:", "<auto>", true, true);
    addProperty("root_password", "root password:", "test123", true, true);
  }
};

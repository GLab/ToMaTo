package buildui.devices;

import buildui.paint.PropertiesArea;
import buildui.paint.Element;

public class OpenVzPropertiesArea extends PropertiesArea {

  public boolean iCare (Element t) {
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
    addProperty("rootpassword", "root password:", "", true, true);
  }
};

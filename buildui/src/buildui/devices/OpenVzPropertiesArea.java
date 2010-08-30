package buildui.devices;

import buildui.paint.MagicTextField;
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
    addTextProperty("name", "name:", MagicTextField.identifier_pattern, null);
    addSelectProperty("hostgroup", "hostgroup:", new String[]{"<auto>", "ukl", "uwue"}, "<auto>");
    addSelectProperty("template", "template:", new String[]{"<auto>", "debian"}, "<auto>");
    addTextProperty("root_password", "root password:", ".*", "test123");
  }
};

package buildui.devices;

import buildui.paint.PropertiesArea;
import buildui.paint.Element;

public class DhcpdPropertiesArea extends PropertiesArea {

  public boolean iCare (Element t) {
    return (t instanceof DhcpdDevice);
  }

  public String getName () {
    return "Dhcpd properties";
  }

  public DhcpdPropertiesArea () {
    super();
    addProperty("name", "name:", "", true, false);
    addProperty("hostgroup", "hostgroup:", "<auto>", true, false);
    addProperty("subnet", "subnet:", "10.1.1.0", false, false);
    addProperty("netmask", "netmask:", "255.255.255.0", false, false);
    addProperty("range", "range:", "10.1.1.1-10.1.1.250", false, true);
  }
};

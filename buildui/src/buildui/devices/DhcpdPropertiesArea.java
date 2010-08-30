package buildui.devices;

import buildui.paint.MagicTextField;
import buildui.paint.PropertiesArea;
import buildui.paint.NetElement;

public class DhcpdPropertiesArea extends PropertiesArea {

  public boolean iCare (NetElement t) {
    return (t instanceof DhcpdDevice);
  }

  public String getName () {
    return "Dhcpd properties";
  }

  public DhcpdPropertiesArea () {
    super();
    addTextProperty("name", "name:", MagicTextField.identifier_pattern, null);
    addSelectProperty("hostgroup", "hostgroup:", new String[]{"<auto>", "ukl", "uwue"}, "<auto>");
    addTextProperty("subnet", "subnet:", MagicTextField.ip4_pattern, "10.1.1.0");
    addTextProperty("netmask", "netmask:", MagicTextField.ip4_pattern, "255.255.255.0");
    addTextProperty("range", "range:", MagicTextField.ip4_pattern+"\\s?-\\s?"+MagicTextField.ip4_pattern, "10.1.1.1-10.1.1.250");
  }
};

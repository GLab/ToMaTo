package buildui.devices;

import buildui.paint.MagicTextField;
import buildui.paint.PropertiesArea;
import buildui.paint.NetElement;

public class KvmPropertiesArea extends PropertiesArea {

  public boolean iCare (NetElement t) {
    return (t instanceof KvmDevice);
  }

  public String getName () {
    return "KVM properties";
  }

  public KvmPropertiesArea () {
    super();
    addTextProperty("name", "name:", MagicTextField.identifier_pattern, null);
    addSelectProperty("hostgroup", "hostgroup:", Device.hostGroups, "<auto>");
    addSelectProperty("template", "template:", KvmDevice.templates, "<auto>");
  }
};

package buildui.devices;

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
    addProperty("name", "name:", "", true, false);
    addProperty("hostgroup", "hostgroup:", "<auto>", true, false);
    addProperty("template", "template:", "<auto>", true, true);
  }
};

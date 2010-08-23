package buildui.devices;

import buildui.PropertiesArea;
import buildui.paint.Element;

public class KvmPropertiesArea extends PropertiesArea {

  public boolean iCare (Element t) {
    return (t instanceof KvmDevice);
  }

  public String getName () {
    return "Node Properties";
  }

  public KvmPropertiesArea () {
    super();
    addProperty("name", "name:", "", true, false);
    addProperty("hardware", "hardware:", "<auto>", true, true);
    addProperty("osid", "os id:", "<auto>", true, true);
  }
};

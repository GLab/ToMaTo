package buildui;

import java.util.ArrayList;

import buildui.devices.Device;
import buildui.paint.IconElement;
import buildui.paint.PropertiesArea;

public class TopologyCreatorElement extends IconElement {

	public TopologyCreatorElement(String newName) {
		super(newName, true, "/icons/tc3.png");
	}

	public static void open(Netbuild parent,int leastX, int leastY, int sizeX, int sizeY,ArrayList<Device> dev) {
		TopologyCreatorWindow.setParams(leastX, leastY, sizeX, sizeY,dev);	
		TopologyCreatorWindow w = TopologyCreatorWindow.getInstance(parent);			
		w.appear();
	}

	@Override
	public PropertiesArea getPropertiesArea() {
		return null;
	}

}

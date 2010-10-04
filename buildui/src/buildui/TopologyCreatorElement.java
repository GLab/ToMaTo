/*
 * Copyright (C) 2010 David Hock, University of Würzburg
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

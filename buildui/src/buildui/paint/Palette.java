package buildui.paint;

/*
 * Copyright (c) 2002-2006 University of Utah and the Flux Group.
 * All rights reserved.
 * This file is part of the Emulab network testbed software.
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

import java.awt.Graphics;

import buildui.TopologyCreatorElement;
import buildui.TrashThingee;
import buildui.connectors.HubConnector;
import buildui.connectors.InternetConnector;
import buildui.connectors.RouterConnector;
import buildui.connectors.SwitchConnector;
import buildui.devices.KvmDevice;
import buildui.devices.OpenVzDevice;
import java.util.LinkedList;
import java.util.List;

public class Palette {

	private List<NetElement> elements = new LinkedList<NetElement>();
	private TrashThingee trash;
	private TopologyCreatorElement tc;
	private int x = 40;
	private int y = 40;
	private Boolean showTc = true;

	private void addElement(NetElement el) {
		elements.add(el);
		el.linkable = false;
		el.trashable = false;
		el.propertyEditable = false;
		el.move(x, y);
	}

	public Palette() {
		addElement(new OpenVzDevice("OpenVZ"));
		y += 60;
		addElement(new KvmDevice("KVM"));
		y += 60;
		y += 30;
		addElement(new InternetConnector("Internet"));
		y += 60;
		addElement(new HubConnector("Hub"));
		y += 50;
		addElement(new SwitchConnector("Switch"));
		y += 50;
		addElement(new RouterConnector("Router"));
		y += 90;
		trash = new TrashThingee("trash");
		trash.moveable = false;
		addElement(trash);
		y += 90;
		tc = new TopologyCreatorElement("TC");
		tc.moveable = false;
		addElement(tc);
	}

	public void showTc(Boolean b) {
		showTc = b;
	}

	public boolean has(NetElement el) {
		return elements.contains(el);
	}

	public void paint(Graphics g) {
		for (NetElement el : elements) {
			if (!el.equals(tc) || showTc)
				el.draw(g);
		}
	}

	public boolean hitTrash(int x, int y) {
		return trash.clicked(x, y);
	}

	public void funktasticizeTrash(Graphics g) {
		trash.drawRect(g);
	}

	public boolean hitCopier(int x, int y) {
		return false;
	}

	public NetElement clicked(int x, int y) {
		for (NetElement el : elements) {
			if (el.clicked(x, y) && el != trash)
				return el;
		}
		return null;
	}
};

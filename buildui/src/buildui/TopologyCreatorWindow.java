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

import java.awt.BorderLayout;
import java.awt.GridLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;

import buildui.connectors.Connection;
import buildui.connectors.InternetConnector;
import buildui.connectors.SwitchConnector;
import buildui.devices.Device;
import buildui.devices.Interface;
import buildui.devices.KvmDevice;
import buildui.devices.OpenVzDevice;

@SuppressWarnings("serial")
public class TopologyCreatorWindow extends JFrame implements ActionListener{
	
	//Functionality Attributes
	private static TopologyCreatorWindow singletonTC;
	
	private static Netbuild parent;
	private static WorkArea workArea;
	private static ArrayList<Device> devices=new ArrayList<Device>();

	private static OpenVzDevice myopenvz;
	private static KvmDevice mykvm;
	private static SwitchConnector myswitch;
	private static InternetConnector myinternet;

	private static int middlex=275;
	private static int middley=275;
	private static int rangex=225;
	private static int rangey=225;
	
	//GUI Attributes
	private JPanel myeditor;
	private JComboBox topologyType;
	private JComboBox numberOfNodes;
	private JComboBox deviceType;
	private JComboBox template;
	private JTextField ipPrefix;
	private JComboBox publicIP;
	private JTextField rootPassword;
	private JPanel myeditorLabels;
	private JPanel myeditorData;
	private JButton myCreateButton;
	private ArrayList<PropertiesEntry> properties = new ArrayList<PropertiesEntry>();		
	
	public static TopologyCreatorWindow getInstance(Netbuild p){
		if (singletonTC==null)
		{
			singletonTC=new TopologyCreatorWindow();
			singletonTC.init(p);
			}
		return singletonTC;
	}

	private TopologyCreatorWindow()
	{
		super();
	}
	
	public static void setParams(int leastX, int leastY, int sizeX,
			int sizeY,ArrayList<Device> d)
	{
		middlex = leastX + sizeX / 2;
		middley = leastY + sizeY / 2;
		rangex = sizeX / 2;
		rangey = sizeY / 2;
		devices=d;
	}

	public void init(Netbuild p) {
		parent = p;
		workArea = parent.getWorkArea();
		myopenvz = new OpenVzDevice("OpenVZ");
		mykvm = new KvmDevice("Kvm");
		myswitch = new SwitchConnector("Switch");

		this.setTitle("Automatic Topology Creator");

		topologyType = new JComboBox(
				new String[] { "Star", "Ring", "Fullmesh","Star around host","loose nodes" });
		topologyType.addActionListener(this);
		numberOfNodes = new JComboBox(new Integer[] { 2, 5, 10, 25 });
		numberOfNodes.setEditable(true);
		deviceType = new JComboBox(new String[] { "OpenVZ", "KVM" });
		deviceType.addActionListener(this);
		template = new JComboBox(OpenVzDevice.templates.toArray());
		//template.removeItem("<auto>");
		ipPrefix = new JTextField("10.1.1.");
		publicIP = new JComboBox(new String[] { "no", "yes" });
		rootPassword = new JTextField("glabroot");

		this.setLayout(new BorderLayout());

		myeditor = new JPanel();
		myeditor.setLayout(new GridLayout(1, 2));

		properties
				.add(new PropertiesEntry("Topology type (#S): ", topologyType));

		properties.add(new PropertiesEntry("Number of nodes (#N): ",
				numberOfNodes));
		properties.add(new PropertiesEntry("Device type (#D): ", deviceType));
		properties.add(new PropertiesEntry("Template (#T): ", template));
		properties.add(new PropertiesEntry("Root password: ", rootPassword));
		properties
				.add(new PropertiesEntry(
						"IP address prefix (e.g. Star: 10.X.Y., Ring/Fullmesh: 10.X.): ",
						ipPrefix));
		properties.add(new PropertiesEntry("Additional public IP addresses: ",
				publicIP));

		myeditorLabels = new JPanel();
		myeditorLabels.setLayout(new GridLayout(properties.size(), 1));

		myeditorData = new JPanel();
		myeditorData.setLayout(new GridLayout(properties.size(), 1));

		for (PropertiesEntry pr : properties) {
			myeditorLabels.add(new JLabel(pr.label));
			myeditorData.add(pr.value);
		}

		myeditor.add(myeditorLabels);
		myeditor.add(myeditorData);

		this.add(myeditor, BorderLayout.CENTER);

		myCreateButton = new JButton("Create");
		myCreateButton.addActionListener(this);

		this.add(myCreateButton, BorderLayout.SOUTH);

		int appWidth = 800;
		int appHeight = 200;

		this.setSize(appWidth, appHeight);
		this.setResizable(false);

	}

	@Override
	public void actionPerformed(ActionEvent arg0) {
		if (arg0.getSource().equals(topologyType)) {
			switch (topologyType.getSelectedIndex())
			{
			//STAR
			case 0:
				ipPrefix.setText("10.1.1.");
				break;
			//RING
			case 1:
				ipPrefix.setText("10.2.");
				break;
			//FULLMESH
			case 2:
				ipPrefix.setText("10.3.");
				break;
			//STAR AROUND HOST
			case 3:
				ipPrefix.setText("10.4.");
				break;
			//LOOSE NODES
			case 4:
				ipPrefix.setText("");
				break;
			default:
				break;
			}
		} else if (arg0.getSource().equals(deviceType)) {
			// System.out.println(deviceType.getSelectedItem().toString() + " "
			// + deviceType.getSelectedIndex());
			template.removeAllItems();
			if (deviceType.getSelectedIndex() == 0) {
				for (Object t : OpenVzDevice.templates.toArray()) {
					template.addItem(t);
				}
				rootPassword.setVisible(true);
				ipPrefix.setVisible(true);
				// publicIP.setVisible(true);
			} else {
				for (Object t : KvmDevice.templates.toArray()) {
					template.addItem(t);
				}
				rootPassword.setVisible(false);
				ipPrefix.setVisible(false);
				// publicIP.setVisible(false);
			}
			//template.removeItem("<auto>");
		} else if (arg0.getSource().equals(myCreateButton)) {
			Device el3;
			int number;
			if (devices==null || devices.isEmpty()) //no devices selected
			{
				try {
					number = (Integer) numberOfNodes.getSelectedItem();
				} catch (Exception e) {
					number = 5;// use 5 instead if no valid number entered
				}

				for (int i = 0; i < number; i++) {
					if (deviceType.getSelectedIndex() == 0) {
						el3 = (OpenVzDevice) myopenvz.createAnother();
					} else {
						el3 = (KvmDevice) mykvm.createAnother();
					}
					el3.setProperty("root_password", rootPassword.getText());
					el3.setProperty("template", (String) template
							.getSelectedItem());
					int x = (int) (Math.cos(((double) i / (double) number) * 2
							* Math.PI - Math.PI / 2) * rangex);
					int y = (int) (Math.sin(((double) i / (double) number) * 2
							* Math.PI - Math.PI / 2) * rangey);
					el3.move(middlex - x, middley + y);
					workArea.add(el3);
					devices.add(el3);
				}
			}
			else
			{
				number=devices.size();
			}
			
			//TOPOLOGY TYPE
			SwitchConnector el1;
			switch (topologyType.getSelectedIndex()) {
			//STAR
			case 0:
				el1 = (SwitchConnector) myswitch.createAnother();
				el1.move(middlex, middley);
				workArea.add(el1);
				for (int i = 0; i < devices.size(); i++) {
					Device d=devices.get(i);
					Connection con = (el1).createConnection(d);
					workArea.add(con);
					Interface iface = (d).createInterface(con);
					iface.setProperty("ip", ipPrefix.getText() + (i+1) + "/24");
					con.setIface(iface);
					workArea.add(iface);
				}
				break;
				
			//RING
			case 1:
				for (int i = 0; i < devices.size(); i++) {
					el1 = (SwitchConnector) myswitch.createAnother();
					int x = (int) (Math
							.cos(((double) (i + 0.5) / (double) number) * 2
									* Math.PI - Math.PI / 2) * rangex);
					int y = (int) (Math
							.sin(((double) (i + 0.5) / (double) number) * 2
									* Math.PI - Math.PI / 2) * rangey);
					el1.move(middlex - x, middley + y);
					workArea.add(el1);
					Device d1 = devices.get(i);
					Device d2 = devices.get((i + 1) % number);
					Connection con = (el1).createConnection(d1);
					workArea.add(con);
					Interface iface = (d1).createInterface(con);
					iface
							.setProperty("ip", ipPrefix.getText() + (i + 1)
									+ ".1" + "/24");
					con.setIface(iface);
					workArea.add(iface);
					Connection con2 = (el1).createConnection(d2);
					workArea.add(con2);
					Interface iface2 = (d2).createInterface(con2);
					iface2.setProperty("ip", ipPrefix.getText() + (i + 1)
							+ ".2" + "/24");
					con2.setIface(iface2);
					workArea.add(iface2);
				}
				break;

			// FULLMESH
			case 2:
				for (int i = 0; i < devices.size(); i++) {
					for (int j = i + 1; j < devices.size(); j++) {
						Device d1 = (Device) devices.toArray()[i];
						Device d2 = (Device) devices.toArray()[j];
						el1 = (SwitchConnector) myswitch.createAnother();
						int x = (d1.getX() + d2.getX()) / 2;
						int y = (d1.getY() + d2.getY()) / 2;
						el1.move(x, y);
						int d1i = i;
						int d2i = j;
						workArea.add(el1);
						Connection con = (el1).createConnection(d1);
						workArea.add(con);
						Interface iface = (d1).createInterface(con);
						iface.setProperty("ip", ipPrefix.getText()
								+ Math.min(d1i * 16 + d2i, 254) + ".1" + "/24");
						con.setIface(iface);
						workArea.add(iface);
						Connection con2 = (el1).createConnection(d2);
						workArea.add(con2);
						Interface iface2 = (d2).createInterface(con2);
						iface2.setProperty("ip", ipPrefix.getText()
								+ Math.min(d1i * 16 + d2i, 254) + ".2" + "/24");
						con2.setIface(iface2);
						workArea.add(iface2);
					}
				}
				break;
				
			//STAR AROUND HOST
			case 3:
				el3 = (OpenVzDevice) myopenvz.createAnother();
				el3.setProperty("root_password", rootPassword.getText());
				el3.setProperty("template", (String) template
								.getSelectedItem());
				el3.move(middlex, middley);
				workArea.add(el3);
				for (int i = 0; i < devices.size(); i++) {
					Device d1 = (Device) devices.toArray()[i];
					el1 = (SwitchConnector) myswitch.createAnother();
					int x = (d1.getX() + el3.getX()) / 2;
					int y = (d1.getY() + el3.getY()) / 2;
					el1.move(x, y);
					workArea.add(el1);
					Connection con = (el1).createConnection(d1);
					workArea.add(con);
					Interface iface = (d1).createInterface(con);
					iface.setProperty("ip", ipPrefix.getText()
							+ (i+1) + ".2" + "/24");
					con.setIface(iface);
					workArea.add(iface);
					Connection con2 = (el1).createConnection(el3);
					workArea.add(con2);
					Interface iface2 = (el3).createInterface(con2);
					iface2.setProperty("ip", ipPrefix.getText()
							+ (i+1) + ".1" + "/24");
					con2.setIface(iface2);
					workArea.add(iface2);
				}
				break;
				
			//LOOSE NODES --> NO CONNECTION
			case 4: break;

			default:
				break;
			}			

			// INTERNET
			if (((String) publicIP.getSelectedItem()).equals("yes")) {
				if (myinternet==null)
				{
					myinternet = new InternetConnector("Internet");
					myinternet.move(275,275);
					workArea.add(myinternet);
					}
				for (int i = 0; i < devices.size(); i++) {
					Device d = devices.get(i);
					Connection con2 = (myinternet).createConnection(d);
					workArea.add(con2);
					Interface iface2 = (d).createInterface(con2);
					iface2.setProperty("usedhcp", "true");
					con2.setIface(iface2);
					workArea.add(iface2);
				}
			}
						
			parent.setWorkArea(workArea);
			parent.repaint();		
	        devices.clear();
	        Netbuild.setStatus("Topology creation done");
			this.setVisible(false);
		}
	}

	public class PropertiesEntry {
		String label = "";
		JComponent value;

		public PropertiesEntry(String label, JComponent value) {
			super();
			this.label = label;
			this.value = value;
		}
	}

	public void appear() {
		if (!(devices==null || devices.isEmpty())) //no devices selected
		{
			this.numberOfNodes.setEnabled(false);
			this.rootPassword.setEnabled(false);
			this.template.setEnabled(false);
			this.deviceType.setEnabled(false);
		}
		else
		{
			this.numberOfNodes.setEnabled(true);
			this.rootPassword.setEnabled(true);
			this.template.setEnabled(true);
			this.deviceType.setEnabled(true);
		}
		this.repaint();
		setVisible(true);		
	}

}

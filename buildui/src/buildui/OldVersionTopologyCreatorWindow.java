package buildui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.GridLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowEvent;
import java.awt.event.WindowListener;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Arrays;

import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.JTree;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import buildui.connectors.Connection;
import buildui.connectors.InternetConnector;
import buildui.connectors.SwitchConnector;
import buildui.devices.Device;
import buildui.devices.Interface;
import buildui.devices.KvmDevice;
import buildui.devices.OpenVzDevice;

public class OldVersionTopologyCreatorWindow extends JFrame implements ActionListener,
		WindowListener {

	private JTextArea myxmlview;
	private JPanel myeditor;

	private JComboBox topologyType;
	// private JTextField topologyName;
	private JComboBox numberOfNodes;
	private JComboBox deviceType;
	private JComboBox template;
	private JTextField namePrefix;
	private JTextField ipPrefix;
	private JComboBox publicIP;
	private JTextField rootPassword;
	private JPanel myeditorLabels;
	private JPanel myeditorData;
	private JButton myCreateButton;

	private ArrayList<PropertiesEntry> properties = new ArrayList<PropertiesEntry>();

	private WorkArea workArea;

	static Netbuild parent;

	private OpenVzDevice myopenvz;
	private KvmDevice mykvm;
	private SwitchConnector myswitch;
	private InternetConnector myinternet;
	private JScrollPane scrollPane;

	private static int middlex;
	private static int middley;
	private static int rangex;
	private static int rangey;
	private boolean createdTopology;
	
	private static OldVersionTopologyCreatorWindow singletonTC;
	
	public static OldVersionTopologyCreatorWindow getInstance(){
		if (singletonTC==null)
		{
			singletonTC=new OldVersionTopologyCreatorWindow();
			singletonTC.init();
			}
		return singletonTC;
	}

	public OldVersionTopologyCreatorWindow()
	{
		super();
	}
	
	public static void setParams(Netbuild p, int leastX, int leastY, int sizeX,
			int sizeY)
	{
		parent = p;
//		System.out.println(leastX + ";" + leastY + ";" + sizeX + ";" + sizeY);
		middlex = leastX + sizeX / 2;
		middley = leastY + sizeY / 2;
		rangex = sizeX / 2;
		rangey = sizeY / 2;
	}

	public void init() {
		addWindowListener(this);
		workArea = parent.getWorkArea();

		this.setTitle("Automatic Topology Creator");

		topologyType = new JComboBox(
				new String[] { "Star", "Ring", "Fullmesh" });
		topologyType.addActionListener(this);
		// topologyName = new JTextField("#S_#N_#D_#T");
		numberOfNodes = new JComboBox(new Integer[] { 2, 5, 10, 25 });
		numberOfNodes.setEditable(true);
		deviceType = new JComboBox(new String[] { "OpenVZ", "KVM" });
		deviceType.addActionListener(this);
		template = new JComboBox(OpenVzDevice.templates.toArray());
		template.removeItem("<auto>");
		namePrefix = new JTextField("host");
		ipPrefix = new JTextField("10.1.1.");
		publicIP = new JComboBox(new String[] { "no", "yes" });
		rootPassword = new JTextField("");

		this.setLayout(new BorderLayout());

		myeditor = new JPanel();
		myeditor.setLayout(new GridLayout(1, 2));

		properties
				.add(new PropertiesEntry("Topology type (#S): ", topologyType));
		// properties.add(new PropertiesEntry(
		// "Name (Possible variables: #S,#N, #D, #T): ", topologyName));
		properties.add(new PropertiesEntry("Number of nodes (#N): ",
				numberOfNodes));
		properties.add(new PropertiesEntry("Device type (#D): ", deviceType));
		properties.add(new PropertiesEntry("Template (#T): ", template));
		properties.add(new PropertiesEntry("Hostname prefix: ", namePrefix));
		properties.add(new PropertiesEntry("Root password: ", rootPassword));
		properties
				.add(new PropertiesEntry(
						"IP address prefix (e.g. Star: 10.1.1., Ring: 10.1., Fullmesh: 10.): ",
						ipPrefix));
		properties.add(new PropertiesEntry("Additional public IP addresses: ",
				publicIP));

		myeditorLabels = new JPanel();
		myeditorLabels.setLayout(new GridLayout(properties.size(), 1));

		myeditorData = new JPanel();
		myeditorData.setLayout(new GridLayout(properties.size(), 1));

		for (PropertiesEntry p : properties) {
			myeditorLabels.add(new JLabel(p.label));
			myeditorData.add(p.value);
		}

		myeditor.add(myeditorLabels);
		myeditor.add(myeditorData);

		this.add(myeditor, BorderLayout.NORTH);

		myxmlview = new JTextArea("Output XML will appear here");
		myxmlview.setEditable(false);
		myxmlview.setEnabled(false);
		scrollPane = new JScrollPane(myxmlview);

		myCreateButton = new JButton("Create");
		myCreateButton.addActionListener(this);

		this.add(myCreateButton, BorderLayout.SOUTH);
		this.add(scrollPane, BorderLayout.CENTER);

		int appWidth = 800;
		int appHeight = 200 + properties.size() * 20;

		this.setSize(appWidth, appHeight);
		this.setResizable(false);

	}

	@Override
	public void actionPerformed(ActionEvent arg0) {
		if (arg0.getSource().equals(topologyType)) {
			if (((String) topologyType.getSelectedItem()).equals("Star")) {
				ipPrefix.setText("10.1.1.");
			} else if (((String) topologyType.getSelectedItem()).equals("Ring")) {
				ipPrefix.setText("10.1.");
			} else if (((String) topologyType.getSelectedItem())
					.equals("Fullmesh")) {
				ipPrefix.setText("10.");
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
			template.removeItem("<auto>");
		} else if (arg0.getSource().equals(myCreateButton)) {
			if (createdTopology)
			{
		        Netbuild.setStatus("Topology creation done"); 
				this.setVisible(false);
			}
			int number;
			try {
				number = (Integer) numberOfNodes.getSelectedItem();
			} catch (Exception e) {
				myxmlview.setText("Please enter a valid number of nodes!!");
				myxmlview.setForeground(Color.RED);
				myxmlview.setEnabled(true);
				return;
			}
			// workArea = new WorkArea();
			// workArea.topologyProperties.setNameValue(topologyName.getText()
			// .replaceAll(
			// "#S",
			// topologyType.getSelectedItem().toString()
			// .toLowerCase()).replaceAll("#N",
			// "" + number).replaceAll(
			// "#D",
			// deviceType.getSelectedItem().toString()
			// .toLowerCase()).replaceAll(
			// "#T",
			// ""
			// + template.getSelectedItem().toString()
			// .split("_")[0]));
			// OpenVzDevice.init(parent);
			// KvmDevice.init(parent);
			// SwitchConnector.init(parent);
			// InternetConnector.init(parent);
			myopenvz = new OpenVzDevice("OpenVZ");
			mykvm = new KvmDevice("Kvm");
			myswitch = new SwitchConnector("Switch");
			myinternet = new InternetConnector("Internet");

			SwitchConnector el1 = new SwitchConnector("");

			// STAR
			if (((String) topologyType.getSelectedItem()).equals("Star")) {
				// SWITCH
				el1 = (SwitchConnector) myswitch.createAnother();
				el1.move(middlex, middley);
				workArea.add(el1);
			}

			// INTERNET
			InternetConnector el2 = new InternetConnector("");
			if (((String) publicIP.getSelectedItem()).equals("yes")) {
				el2 = (InternetConnector) myinternet.createAnother();
				if (((String) topologyType.getSelectedItem()).equals("Star")) {
					el1.move(middlex - (rangex / 10), middley); // in this case
																// move switch
																// to get space
					// for internet icon
					el2.move(middlex + rangex / 10, middley);
				} else {
					el2.move(middlex, middley);
				}
				workArea.add(el2);
			}
			Device el3 = new OpenVzDevice("");
			Device el3prev = new OpenVzDevice("");
			Device el3first = new OpenVzDevice("");
			for (int i = 0; i < number; i++) {
				if (i > 0)
					el3prev = el3;
				if (deviceType.getSelectedIndex() == 0) {
					el3 = (OpenVzDevice) myopenvz.createAnother();
				} else {
					el3 = (KvmDevice) mykvm.createAnother();
				}

				el3.setName(namePrefix.getText() + (i + 1));
				el3.setProperty("root_password", rootPassword.getText());
				el3
						.setProperty("template", (String) template
								.getSelectedItem());
				int x = (int) (Math.cos(((double) i / (double) number) * 2
						* Math.PI - Math.PI / 2) * rangex);
				int y = (int) (Math.sin(((double) i / (double) number) * 2
						* Math.PI - Math.PI / 2) * rangey);
				// System.out.println(x+" , "+y);
				el3.move(middlex - x, middley + y);
				workArea.add(el3);

				if (((String) topologyType.getSelectedItem()).equals("Star")) {
					// SWITCH
					Connection con = (el1).createConnection(el3);
					workArea.add(con);
					Interface iface = (el3).createInterface(con);
					iface.setProperty("ip", ipPrefix.getText() + (i + 1));
					con.setIface(iface);
					workArea.add(iface);
				} else if (((String) topologyType.getSelectedItem())
						.equals("Ring")) {
					// SWITCH
					if (i > 0) {
						el1 = (SwitchConnector) myswitch.createAnother();
						x = (int) (Math
								.cos(((double) (i - 0.5) / (double) number) * 2
										* Math.PI - Math.PI / 2) * rangex);
						y = (int) (Math
								.sin(((double) (i - 0.5) / (double) number) * 2
										* Math.PI - Math.PI / 2) * rangey);
						el1.move(middlex - x, middley + y);
						el1.setName("switch" + (i + 1));
						workArea.add(el1);
						Connection con = (el1).createConnection(el3);
						workArea.add(con);
						Interface iface = (el3).createInterface(con);
						iface.setProperty("ip", ipPrefix.getText() + (i + 1)
								+ ".1");
						con.setIface(iface);
						workArea.add(iface);
						Connection con2 = (el1).createConnection(el3prev);
						workArea.add(con2);
						Interface iface2 = (el3prev).createInterface(con2);
						iface2.setProperty("ip", ipPrefix.getText() + (i + 1)
								+ ".2");
						con2.setIface(iface2);
						workArea.add(iface2);
					}
					if (i == (number - 1))// last one
					{
						el1 = (SwitchConnector) myswitch.createAnother();
						x = (int) (Math.cos(((double) -0.5 / (double) number)
								* 2 * Math.PI - Math.PI / 2) * rangex);
						y = (int) (Math.sin(((double) -0.5 / (double) number)
								* 2 * Math.PI - Math.PI / 2) * rangey);
						el1.move(middlex - x, middley + y);
						el1.setName("switch" + (1));
						workArea.add(el1);
						Connection con = (el1).createConnection(el3first);
						workArea.add(con);
						Interface iface = (el3first).createInterface(con);
						iface
								.setProperty("ip", ipPrefix.getText() + (1)
										+ ".1");
						con.setIface(iface);
						workArea.add(iface);
						Connection con2 = (el1).createConnection(el3);
						workArea.add(con2);
						Interface iface2 = (el3).createInterface(con2);
						iface2.setProperty("ip", ipPrefix.getText() + (1)
								+ ".2");
						con2.setIface(iface2);
						workArea.add(iface2);
					}
				}

				// INTERNET
				if (((String) publicIP.getSelectedItem()).equals("yes")) {
					Connection con2 = (el2).createConnection(el3);
					workArea.add(con2);
					Interface iface2 = (el3).createInterface(con2);
					iface2.setProperty("usedhcp", "true");
					con2.setIface(iface2);
					workArea.add(iface2);
				}

				if (i == 0)
					el3first = el3;
			}
			if (((String) topologyType.getSelectedItem()).equals("Fullmesh")) {
				for (int i = 0; i < workArea.getDevices().size(); i++) {
					for (int j = i + 1; j < workArea.getDevices().size(); j++) {
						Device d1 = (Device) workArea.getDevices().toArray()[i];
						Device d2 = (Device) workArea.getDevices().toArray()[j];
						el1 = (SwitchConnector) myswitch.createAnother();
						int x = (d1.getX() + d2.getX()) / 2;
						int y = (d1.getY() + d2.getY()) / 2;
						el1.move(x, y);
						int d1i = Integer.parseInt(d1.getName().replaceAll(
								namePrefix.getText(), ""));
						int d2i = Integer.parseInt(d2.getName().replaceAll(
								namePrefix.getText(), ""));
						if (d2i < d1i) // kleinere ID vorne
						{
							int ti = d1i;
							d1i = d2i;
							d2i = ti;
							Device t = d1;
							d1 = d2;
							d2 = t;
						}
						el1.setName("switch" + d1i + "_" + d2i);
						workArea.add(el1);
						Connection con = (el1).createConnection(d1);
						workArea.add(con);
						Interface iface = (d1).createInterface(con);
						iface.setProperty("ip", ipPrefix.getText() + d1i + "."
								+ d2i + ".1");
						con.setIface(iface);
						workArea.add(iface);
						Connection con2 = (el1).createConnection(d2);
						workArea.add(con2);
						Interface iface2 = (d2).createInterface(con2);
						iface2.setProperty("ip", ipPrefix.getText() + d1i + "."
								+ d2i + ".2");
						con2.setIface(iface2);
						workArea.add(iface2);
					}
				}
			}
			ByteArrayOutputStream baos = new ByteArrayOutputStream();
			workArea.encode(baos);
			parent.setWorkArea(workArea);
			parent.repaint();
			myxmlview.setText(baos.toString());
			// try {
			// JFrame temp = new JFrame();
			// temp.add(new JScrollPane(new JTree(initTreeRoot(new
			// ByteArrayInputStream(baos.toString().getBytes("UTF-8"))))),BorderLayout.CENTER);
			// temp.setVisible(true);
			// } catch (UnsupportedEncodingException e) {
			// // TODO Auto-generated catch block
			// e.printStackTrace();
			// }
			myxmlview.setForeground(Color.BLACK);
			myxmlview.setEnabled(true);
			myxmlview.setCaretPosition(0);

			// disable all controls and wait for close
			for (PropertiesEntry p : properties) {
				p.value.setEnabled(false);
			}
			myCreateButton.setText("Close");
			createdTopology = true;
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

	@Override
	public void windowActivated(WindowEvent arg0) {
		// TODO Auto-generated method stub

	}

	@Override
	public void windowClosed(WindowEvent arg0) {
	}

	@Override
	public void windowClosing(WindowEvent arg0) {
        Netbuild.setStatus("Topology creation done"); 
	}

	@Override
	public void windowDeactivated(WindowEvent arg0) {
		// TODO Auto-generated method stub

	}

	@Override
	public void windowDeiconified(WindowEvent arg0) {
		// TODO Auto-generated method stub

	}

	@Override
	public void windowIconified(WindowEvent arg0) {
		// TODO Auto-generated method stub

	}

	@Override
	public void windowOpened(WindowEvent arg0) {
		// TODO Auto-generated method stub

	}

	// private DefaultMutableTreeNode initTreeRoot(InputStream in) {
	// Document doc = null;
	// try {
	// DocumentBuilderFactory factory = DocumentBuilderFactory
	// .newInstance();
	// DocumentBuilder builder = factory.newDocumentBuilder();
	// doc = builder.parse(in);
	// } catch (ParserConfigurationException e) {
	// e.printStackTrace();
	// } catch (SAXException e) {
	// e.printStackTrace();
	// } catch (IOException e) {
	// e.printStackTrace();
	// }
	// if (doc == null)
	// return new DefaultMutableTreeNode("EMPTY");
	//
	// Node rootNode = doc.getFirstChild();
	// DefaultMutableTreeNode root = new DefaultMutableTreeNode(
	// rootNode.getNodeName());
	// treeWalk(rootNode, 0, root);
	//
	// return root;
	// }
	//
	// public static void treeWalk(Node node, int level,
	// DefaultMutableTreeNode parentNode) {
	//
	// String nodeName = node.getNodeName();
	// DefaultMutableTreeNode childNode = null;
	//
	// if (node.hasChildNodes()) {
	// level++;
	// System.out.println(repeat(level, ' ').append(nodeName));
	// NodeList list = node.getChildNodes();
	// int len = list.getLength();
	// for (int i = 0; i < len; i++) {
	// Node child = list.item(i);
	// childNode = new DefaultMutableTreeNode(child.getNodeName());
	// parentNode.add(childNode);
	// treeWalk(list.item(i), level, childNode);
	// }
	// } else {
	// childNode = new DefaultMutableTreeNode(node.getNodeValue());
	// System.out
	// .println(repeat(level, ' ').append(node.getTextContent()));
	// parentNode.add(childNode);
	// }
	// }
	//
	// public final static StringBuffer repeat(int n, char c) {
	// char[] cA = new char[n];
	// Arrays.fill(cA, c);
	// return (StringBuffer) new StringBuffer().insert(0, cA);
	// }

}

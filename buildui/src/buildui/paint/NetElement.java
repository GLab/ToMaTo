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
import java.awt.*;
import java.lang.Math;
import java.util.*;
import java.text.*;

public abstract class NetElement {
	private boolean nameFixed;
	private String name;
	private int x, y;

	private int stringWidth;
	private boolean stringWidthValid;

	static private Dictionary selections;
  private final boolean displayName;

	public void select() {
		if (!isSelected()) {
			selections.put(this, new Integer(1));
		}
	}

	public static Enumeration selectedElements() {
		return selections.keys();
	}

	public static void deselectAll() {
		selections = new Hashtable();
	}

	public void deselect() {
		selections.remove(this);
	}

	static public int selectedCount() {
		return selections.size();
	}

	public boolean isSelected() {
		return selections.get(this) != null;
	}

	static private Dictionary names;

	protected Dictionary properties;

	public void copyProps(NetElement t) {
		Enumeration e = t.properties.keys();

		while (e.hasMoreElements()) {
			String s = (String) e.nextElement();

			properties.put(new String(s), t.properties.get(s));
		}

	}

	static public String genName(String name) {
		/*
		 * if (names.get( name ) == null) { return name; }
		 */

		int num = 0;
		String n = new String();
		do {
			n = name + NumberFormat.getInstance().format(num);
			num++;
		} while (names.get(n) != null);
		return new String(n);
	}

	public synchronized String getProperty(String name, String def) {
		if (0 == name.compareTo("name")) {
			// note that the name _can_ be blank.
			return this.name;
		}
		Object foo = properties.get(name);
		if (foo == null || 0 == ((String) foo).compareTo("")) {
			return def;
		} else {
			return (String) foo;
		}
	}

	public synchronized void setProperty(String name, String value) {
		if (0 == name.compareTo("name")) {
			setName(new String(value));
		} else {
			properties.put(new String(name), new String(value));
		}
	}

	public int getX() {
		return x;
	}

	public int getY() {
		return y;
	}

	public boolean linkable;
	public boolean moveable;
	public boolean propertyEditable;
	public boolean trashable;

	// static NetElement currentlySelected;

	static {
		names = new Hashtable();
		// currentlySelected = null;
		selections = new Hashtable();
	}

	/*
	 * static public NetElement getSelected() { return currentlySelected; }
	 * 
	 * static public void setSelected( NetElement t ) { currentlySelected = t; }
	 */

	public void fixName(boolean fix) {
		nameFixed = fix;
	}

	public boolean nameFixed() {
		return nameFixed;
	}

	public String getName() {
		return name;
	}

	public void setName(String newName) {
		// System.out.println("NetElement.setName(): Renamed from \"" + name +
		// "\" to \"" + newName + "\"" );
		if (!nameFixed) {
			names.remove(name);
			name = new String(newName);
			names.put(name, new Integer(1));
			stringWidthValid = false;
		}
	}

	public NetElement(String newName, boolean displayName) {
		name = new String(newName);
		names.put(name, new Integer(1));
    this.displayName = displayName ;
		properties = new Hashtable();
		stringWidth = 128;
		stringWidthValid = false;
		linkable = true;
		moveable = true;
		propertyEditable = true;
		trashable = true;
		nameFixed = false;
	}

	public void move(int nx, int ny) {
		x = nx;
		y = ny;
	}

	public int size() {
		return 16;
	}

	public boolean clicked(int cx, int cy) {
		if (isSelected()) {
			Rectangle r = getRectangle();
			return (cx > r.x && cy > r.y && cx < (r.x + r.width) && cy < (r.y + r.height));
		} else {
			return (Math.abs(cx - x) < size() && Math.abs(cy - y) < size());
		}
	}

	public Rectangle getRectangle() {
		int wid = 26;
		if ((stringWidth / 2) > wid) {
			wid = (stringWidth / 2) + 4;
		}
		return new Rectangle(x + -wid - 2, y + -21 - 2, wid * 2 + 6, 57 + 6);
	}

	public void drawRect(Graphics g) {
		g.fillRect(x - 16, y - 16, 32, 32);
	}

	public void drawIcon(Graphics g) {
		g.setColor(Color.lightGray);
		g.fillRect(-12, -12, 32, 32);

		g.setColor(Color.white);
		g.fillRect(-16, -16, 32, 32);

		g.setColor(Color.black);
		g.drawRect(-16, -16, 32, 32);
	}

	public int textDown() {
		return 30;
	}

  public NetElement createAnother() {
    return null ;
  }

	public void draw(Graphics g) {
		if (!stringWidthValid) {
			FontMetrics fm = g.getFontMetrics();
			stringWidth = fm.stringWidth(name);
			stringWidthValid = true;
		}

		g.translate(x, y);

		if (isSelected()) {
			Rectangle r = getRectangle();
			g.setColor(Color.white);
			g.fillRect(r.x - x, r.y - y, r.width, r.height);

			g.setColor(Color.black);
			g.drawRect(r.x - x, r.y - y, r.width - 1, r.height - 1);
			g.drawRect(r.x - x + 1, r.y - y + 1, r.width - 3, r.height - 3);
			/*
			 * boolean anytext = (name != ""); int wid = 26; if ((stringWidth/2)
			 * > wid) { wid = (stringWidth/2) + 4; } g.setColor( Color.white );
			 * g.fillRect( -wid, -21, wid * 2, anytext ? 57 : 42 );
			 * 
			 * g.setColor( Color.black ); g.drawRect( -wid, -21, wid * 2,
			 * anytext ? 57 : 42 ); g.drawRect( -wid - 1, -21 - 1, wid * 2 + 2,
			 * (anytext ? 57 : 42) + 2 );
			 */
		}

		drawIcon(g);

		// g.setColor( Color.lightGray );
		// g.drawString( name, -(stringWidth/2) + 4, textDown() + 4 );
		g.setColor(Color.black);
		if ( displayName ) g.drawString(name, -(stringWidth / 2), textDown());
		g.translate(-x, -y);
	}

  public abstract PropertiesArea getPropertiesArea() ;

}

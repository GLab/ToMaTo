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
import java.awt.event.*;

class Expando extends Component
{
    private String text;
    private boolean expanded;
    private ActionListener actionListener;
    private static Color darkBlue;

    static {
	darkBlue = new Color( 0.3f, 0.3f, 0.5f );
    }

    public void setState( boolean state ) { expanded = state; }
    public boolean getState() { return expanded; }

    public Expando( String t)
    {
	super();
	text = t;
	expanded = true;

	setCursor( Cursor.getPredefinedCursor( Cursor.HAND_CURSOR ) );

	enableEvents( AWTEvent.MOUSE_EVENT_MASK );
	enableEvents( AWTEvent.MOUSE_MOTION_EVENT_MASK );
    }

    protected void processMouseEvent( MouseEvent e )
    {
	if (actionListener != null) {
	    if (e.getID() == MouseEvent.MOUSE_PRESSED) {
		expanded = !expanded;
		ActionEvent ae = new ActionEvent( this, ActionEvent.ACTION_PERFORMED,
						  expanded ? "down" : "up", 0 );
		actionListener.actionPerformed( ae );
		repaint();
	    }
	}
    }

    public void addActionListener( ActionListener l ) 
    {
	actionListener = l;
    }

    public void removeActionListener( ActionListener l )
    {
	actionListener = null;
    }

    public Dimension getPreferredSize()
    {
	Graphics g = getGraphics();
	if (g != null) {
	    FontMetrics fm = g.getFontMetrics();
	    if (fm != null) {
		int stringWidth = fm.stringWidth(text);
		return new Dimension(16 + 4 + stringWidth, 16);
	    }
	    g.dispose();
	} 
	
	return new Dimension(32, 32);
    }

    public Dimension getMinimumSize() { return getPreferredSize(); }
    public Dimension getMaximumSize() { return getPreferredSize(); }

    public void paint( Graphics g ) 
    {
	//super.paint();
	g.setColor( Color.white );
	FontMetrics fm = getGraphics().getFontMetrics();
	int stringHeight = fm.getHeight();
	g.drawString( text, 20, 8 + (stringHeight/2));
	g.fillRect( 2,2, 13, 13 );

	g.setColor( Color.black );
	g.drawRect( 2,2, 13, 13 );
	g.drawRect( 3,3, 11, 11 );

	g.setColor( darkBlue );
	g.fillRect( 6, 8, 6, 2 );
	
	if (!expanded) {
	    g.fillRect( 8, 6, 2, 6 );
	}
    }
};

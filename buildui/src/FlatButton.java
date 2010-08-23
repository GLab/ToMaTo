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

class FlatButton extends Canvas
{
    String text;
    boolean mouseIsOver;
    ActionListener myActionListener;

    private static Color lightBlue;
    private static Color darkerBlue;

    static {
	lightBlue  = new Color( 0.7f, 0.7f, 1.0f );
	darkerBlue = new Color( 0.4f, 0.4f, 0.6f );
    }

    public FlatButton( String t )
    {
	super();

	text = t;
	mouseIsOver = false;
	myActionListener = null;
	enableEvents( AWTEvent.MOUSE_EVENT_MASK );
    }

    public void addActionListener( ActionListener e ) {
	myActionListener = e;
    }

    protected void clicked() {
	ActionEvent ce = new ActionEvent( this, 
					  ActionEvent.ACTION_PERFORMED,
					  "clicked" );
	if (myActionListener != null) {
	    myActionListener.actionPerformed( ce );
	}
    }

    protected void processMouseEvent( MouseEvent e ) {
	if (e.getID() == MouseEvent.MOUSE_ENTERED) {
	    mouseIsOver = true;
	} else if (e.getID() == MouseEvent.MOUSE_EXITED) {
	    mouseIsOver = false;
	} else if (e.getID() == MouseEvent.MOUSE_PRESSED) {
	    if (isEnabled()) {
		clicked();
	    }
	}
	repaint();
    }

    public Dimension getPreferredSize()
    {
	Graphics g = getGraphics();

	if (g != null) {
	    FontMetrics fm = g.getFontMetrics();
	    if (fm != null) {
		int stringWidth = fm.stringWidth(text);
		//return new Dimension( stringWidth + 12, fm.getHeight() + 6 );
		return new Dimension( 640 - 480 - 16, fm.getHeight() + 8 );
	    }
	    g.dispose();
	} 
	return new Dimension(200, 40);
    }

    public Dimension getMinimumSize() { return getPreferredSize(); }
    public Dimension getMaximumSize() { return getPreferredSize(); }
    
    public void setEnabled( boolean en )
    {
	/*
	if (en) {
	    setCursor( Cursor.getPredefinedCursor( Cursor.HAND_CURSOR ) );
	} else {
	    setCursor( Cursor.getPredefinedCursor( Cursor.DEFAULT_CURSOR ) );
	}
	*/
	super.setEnabled( en );
	repaint();
    }
    
    public void paint( Graphics g )
    {
	FontMetrics fm = g.getFontMetrics();
	super.paint(g);

        int stringWidth = fm.stringWidth( text );
	int stringHeight = fm.getHeight();

	Dimension size = getSize();

	int begin = size.width / 2 - stringWidth / 2 - 2;
	//int end   = size.width / 2 + stringWidth / 2;

	if (isEnabled()) {
	    if (mouseIsOver) {
		g.setColor( lightBlue );
	    } else {
		g.setColor( darkerBlue );
	    }
	    g.fillRect( 0, 0, size.width, size.height );
	    g.setColor( Color.black );
	} else {
	    g.setColor( Color.darkGray );
	}

	g.drawRect( 0, 0, size.width - 1, size.height - 1);

	if (isEnabled()) {
	    g.setColor( Color.white );
	} else {
	    g.setColor( Color.lightGray );
	}


	//    g.drawLine( begin, stringHeight + 2, end, stringHeight + 2 );
	g.drawString( text, begin, size.height / 2 + fm.getHeight() / 3 );
    }   
};

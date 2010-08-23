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
import java.awt.Color;
import java.awt.Rectangle;
import java.util.Vector;
import java.util.Enumeration;

public class Palette {
    private Thingee newNode;
    private Thingee newLAN;
    private Thingee copier;
    private Thingee trash;

    public Palette() {
	newNode = new NodeThingee( "New Node" );
	newNode.move( 40, 100 );
	newNode.linkable = false;
	newNode.trashable = false;

	newNode.propertyEditable = false;

	newLAN  = new LanThingee( "New LAN" );
	newLAN.move( 40, 180 );
	newLAN.linkable = false;
	newLAN.trashable = false;
	newLAN.propertyEditable = false;

	trash = new TrashThingee( "trash" );
	trash.move( 40, 420 );
	trash.linkable = false;
	trash.trashable = false; // very zen.
	trash.moveable = false;
	trash.propertyEditable = false;

	copier = new Thingee( "copier" );
	copier.move( 40, 340 );
	copier.linkable = false;
	copier.trashable = false;
	copier.moveable = false;
	copier.propertyEditable = false;
    }

    public boolean has( Thingee t ) {
	return (newNode == t || newLAN == t || trash == t);
    }

    public void paint( Graphics g ) {
	newNode.draw( g );
	newLAN.draw( g );
	//copier.draw( g );
	trash.draw( g );
    }

    public boolean hitTrash( int x, int y ) {
	return trash.clicked(x, y);
    }

    public void funktasticizeTrash( Graphics g ) {
	trash.drawRect( g );
    }

    public boolean hitCopier( int x, int y ) {
	return false;
	//return copier.clicked(x, y);
    }

    public Thingee clicked( int x, int y ) {
	if (newNode.clicked(x, y)) {
	    return newNode;
	} else if (newLAN.clicked( x, y )) {
	    return newLAN;
	} else {
	    return null;
	}
    }
};

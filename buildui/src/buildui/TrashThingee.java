package buildui;
/*
 * Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
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
import buildui.paint.PropertiesArea;
import java.awt.*;

import buildui.paint.IconElement;

public class TrashThingee extends IconElement {

  public TrashThingee (String newName) {
    super(newName, true, "/icons/trash.png");
  }

  @Override
  public PropertiesArea getPropertiesArea () {
    throw new UnsupportedOperationException("Not supported yet.");
  }

    @Override
    public void onNameChanged(String oldName, String newName) {
        throw new UnsupportedOperationException("Not supported yet.");
    }

    @Override
    public void onPropertyChanged(String property, String oldValue, String newValue) {
        //ignore
    }

};

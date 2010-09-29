package buildui.connectors;

import buildui.paint.MagicTextField;
import buildui.paint.PropertiesArea;
import buildui.paint.NetElement;

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

public class EmulatedConnectionPropertiesArea extends ConnectionPropertiesArea {

  public boolean iCare (NetElement t) {
    return (t instanceof EmulatedConnection) & ! (t instanceof EmulatedRouterConnection);
  }

  public String getName () {
    return "Link properties";
  }

  public EmulatedConnectionPropertiesArea () {
    super();
    addTextProperty("bandwidth", "bandwidth(Kb/s):", MagicTextField.numeric_pattern, "10000");
    addTextProperty("delay", "latency(ms):", MagicTextField.numeric_pattern, "0");
    addTextProperty("lossratio", "loss rate(0.0-1.0):", MagicTextField.fp_numeric_pattern, "0.0");
    addSelectProperty("capture", "capture packets:", new String[]{"true", "false"}, "false");
  }
};

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
import java.awt.event.*;

public class MagicTextField implements TextListener, FocusListener {

  public TextField tf;
  private boolean zapped;
  private boolean wasAuto;
  private boolean alphaAllowed;
  private boolean specialAllowed; // '+' and '_'
  private boolean numAllowed;
  private static Color darkGreen;

  static {
    //	darkGreen = new Color( 0.20f, 0.55f, 0.20f );
    darkGreen = new Color(0.0f, 0.33f, 0.0f);
  }

  public void focusGained (FocusEvent f) {
    tf.selectAll();
  }

  public void focusLost (FocusEvent f) {
  }

  public MagicTextField (boolean nAlphaAllowed, boolean nNumAllowed, boolean nSpecialAllowed) {
    tf = new TextField();
    tf.addTextListener(this);
    tf.addFocusListener(this);
    wasAuto = false;

    alphaAllowed = nAlphaAllowed;
    numAllowed = nNumAllowed;
    specialAllowed = nSpecialAllowed;
  }

  public void setText (String t) {
    wasAuto =
     (0 == t.compareTo("<auto>")) || (0 == t.compareTo("<multiple>"));
    tf.setText(t);
  }

  private boolean isAlphic (char c) {
    return "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ".indexOf(c, 0) != -1;
  }

  private boolean isNumeric (char c) {
    return "0123456789".indexOf(c, 0) != -1;
  }

  public void textValueChanged (TextEvent e) {
    String newText = tf.getText();

    if (0 == newText.compareTo("<auto>"))
      //wasAuto = true;
      tf.setForeground(Color.blue);
    else if (0 == newText.compareTo("<multiple>"))
      tf.setForeground(darkGreen);
    else {
      tf.setForeground(Color.black);
      if (wasAuto)
        wasAuto = false;

      int caret = tf.getCaretPosition();


      int i = 0;
      // in perl, this would be one line.
      String rep = newText;
      while (i != rep.length()) {
        char c = rep.charAt(i);
        // valid if:
        // alphaAllowed and its alphanumeric (or '-')
        // (but not numeric or '-' if it is the first char)
        // numAllowed and its numeric or "."
		/*		if (alphaAllowed && c == ' ') {
        rep = rep.replace(' ', '-');
        i++;
        } else */
        if ((alphaAllowed && (isAlphic(c) || (i != 0 && (isNumeric(c)/* || c == '-'*/)))) || (specialAllowed && i != 0 && (c
         == '_' || c == '-' || c == '+' || c == '.')) || (numAllowed && (isNumeric(c) || c == '.')))
          // legit.
          i++;
        else {
          // utter crap.
          caret--;
          if (i == rep.length() - 1)
            rep = rep.substring(0, i);
          else
            rep = rep.substring(0, i) + rep.substring(i + 1, rep.length());
        }
      }

      if (rep.compareTo(newText) != 0)
        tf.setText(rep);

      try {
        tf.setCaretPosition(caret);
      } catch (Exception ex) {
      }
    }
  }
};
    

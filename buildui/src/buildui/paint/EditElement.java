/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package buildui.paint;

/**
 *
 * @author lemming
 */
interface EditElement {

  public void setValue (String value);

  public String getValue ();

  public void setEnabled (boolean b);

  public boolean isEnabled ();

}

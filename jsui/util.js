/* Simple JavaScript Inheritance
 * By John Resig http://ejohn.org/
 * MIT Licensed.
 */
// Inspired by base2 and Prototype
(function(){
  var initializing = false, fnTest = /xyz/.test(function(){xyz;}) ? /\b_super\b/ : /.*/;
  // The base Class implementation (does nothing)
  this.Class = function(){};
  
  // Create a new Class that inherits from this class
  Class.extend = function(prop) {
    var _super = this.prototype;
    
    // Instantiate a base class (but only create the instance,
    // don't run the init constructor)
    initializing = true;
    var prototype = new this();
    initializing = false;
    
    // Copy the properties over onto the new prototype
    for (var name in prop) {
      // Check if we're overwriting an existing function
      prototype[name] = typeof prop[name] == "function" && 
        typeof _super[name] == "function" && fnTest.test(prop[name]) ?
        (function(name, fn){
          return function() {
            var tmp = this._super;
            
            // Add a new ._super() method that is the same method
            // but on the super-class
            this._super = _super[name];
            
            // The method only need to be bound temporarily, so we
            // remove it when we're done executing
            var ret = fn.apply(this, arguments);        
            this._super = tmp;
            
            return ret;
          };
        })(name, prop[name]) :
        prop[name];
    }
    
    // The dummy class constructor
    function Class() {
      // All construction is actually done in the init method
      if ( !initializing && this.init )
        this.init.apply(this, arguments);
    }
    
    // Populate our constructed prototype object
    Class.prototype = prototype;
    
    // Enforce the constructor to be what we expect
    Class.constructor = Class;

    // And make this class extendable
    Class.extend = arguments.callee;
    
    return Class;
  };
})(); 

compoundBBox = function (list) {
  minX = -1;
  maxX = -1;
  minY = -1;
  maxY = -1;
  for (i in list) {
    box = list[i].getBBox();
    if (minX<0) minX = box.x;
    minX = Math.min(minX, box.x);
    if (maxX<0) maxX = box.x+box.width;
    maxX = Math.max(maxX, box.x+box.width);
    if (minY<0) minY = box.y;
    minY = Math.min(minY, box.y);
    if (maxY<0) maxY = box.y+box.height;
    maxY = Math.max(maxY, box.y+box.height);
  }
  return {x: minX, y: minY, width: maxX-minX, height: maxY-minY};
};

arrayRemove = function(array, item){
  var pos = -1;
  for (i in array) if (array[i] == item) pos = i;
  array[i] = array[length-1];
  return array.pop();
};
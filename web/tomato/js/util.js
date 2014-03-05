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

(function($){$.toJSON=function(o)
{if(typeof(JSON)=='object'&&JSON.stringify)
return JSON.stringify(o);var type=typeof(o);if(o===null)
return"null";if(type=="undefined")
return undefined;if(type=="number"||type=="boolean")
return o+"";if(type=="string")
return $.quoteString(o);if(type=='object')
{if(typeof o.toJSON=="function")
return $.toJSON(o.toJSON());if(o.constructor===Date)
{var month=o.getUTCMonth()+1;if(month<10)month='0'+month;var day=o.getUTCDate();if(day<10)day='0'+day;var year=o.getUTCFullYear();var hours=o.getUTCHours();if(hours<10)hours='0'+hours;var minutes=o.getUTCMinutes();if(minutes<10)minutes='0'+minutes;var seconds=o.getUTCSeconds();if(seconds<10)seconds='0'+seconds;var milli=o.getUTCMilliseconds();if(milli<100)milli='0'+milli;if(milli<10)milli='0'+milli;return'"'+year+'-'+month+'-'+day+'T'+
hours+':'+minutes+':'+seconds+'.'+milli+'Z"';}
if(o.constructor===Array)
{var ret=[];for(var i=0;i<o.length;i++)
ret.push($.toJSON(o[i])||"null");return"["+ret.join(",")+"]";}
var pairs=[];for(var k in o){var name;var type=typeof k;if(type=="number")
name='"'+k+'"';else if(type=="string")
name=$.quoteString(k);else
continue;if(typeof o[k]=="function")
continue;var val=$.toJSON(o[k]);pairs.push(name+":"+val);}
return"{"+pairs.join(", ")+"}";}};$.evalJSON=function(src)
{if(typeof(JSON)=='object'&&JSON.parse)
return JSON.parse(src);return eval("("+src+")");};$.secureEvalJSON=function(src)
{if(typeof(JSON)=='object'&&JSON.parse)
return JSON.parse(src);var filtered=src;filtered=filtered.replace(/\\["\\\/bfnrtu]/g,'@');filtered=filtered.replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,']');filtered=filtered.replace(/(?:^|:|,)(?:\s*\[)+/g,'');if(/^[\],:{}\s]*$/.test(filtered))
return eval("("+src+")");else
throw new SyntaxError("Error parsing JSON, source is not valid.");};$.quoteString=function(string)
{if(string.match(_escapeable))
{return'"'+string.replace(_escapeable,function(a)
{var c=_meta[a];if(typeof c==='string')return c;c=a.charCodeAt();return'\\u00'+Math.floor(c/16).toString(16)+(c%16).toString(16);})+'"';}
return'"'+string+'"';};var _escapeable=/["\\\x00-\x1f\x7f-\x9f]/g;var _meta={'\b':'\\b','\t':'\\t','\n':'\\n','\f':'\\f','\r':'\\r','"':'\\"','\\':'\\\\'};})(jQuery);

(function ($) {
	var $prev_focused = null;
	var focus_orig = $.fn.focus;
	$.fn.focus = function () {
		if (!arguments.length) {
			if ($prev_focused) $prev_focused.blur();
			$prev_focused = this;
		}
		else {
			focus_orig.apply(this, function () { $prev_focused = $(this); });
		}
		return focus_orig.apply(this, arguments);
	};
	$(document).click(function () {
		if ($prev_focused) $prev_focused.blur();
		$prev_focused = null;
		
		$(document).find('.ui-state-focus').blur();
	});
})(jQuery);

compoundBBox = function (list) {
  var minX = -1;
  var maxX = -1;
  var minY = -1;
  var maxY = -1;
  for (var i = 0; i < list.length; i++) {
	if (list[i].getBBox) var box = list[i].getBBox();
	if (list[i].getRect) var box = list[i].getRect();
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

if (!Array.prototype.remove) {
	Array.prototype.remove = function(item) {
		var pos = -1;
		for (var i in this) if (this[i] == item) pos = i;
		this.splice(pos, 1);
	};
}

computedStyle = function(el){
    if (el.currentStyle) return el.currentStyle;
    else return document.defaultView.getComputedStyle(el);
};

getKeys = function(assAr) {
	var keys = [];
	for (var key in assAr) keys.push(key);
	return keys;
};

formatSize = function(value) {
	suffix = 0;
	while (value > 1024) {
		value /= 1024.0;
		suffix++;
	}
	return Math.round(value*100)/100 + " " + ["Bytes", "KB", "MB", "GB", "TB"][suffix];
};

formatDuration = function(value, recursed) {
	var units = [[1, "seconds"], [60, "minutes"], [3600, "hours"], [3600*24, "days"]];
	for (var i = units.length-1; i >= 0; i--) {
		var val = units[i][0];
		var unit = units[i][1];
		if (value >= val) {
			var str = Math.floor(value/val) + " " + unit;
			var rest = value - Math.floor(value/val)*val;
			if (rest && !recursed) str += ", " + formatDuration(rest, true);
			return str;
		}
	}
};

if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function(elt /*, from*/) {
    var len = this.length;
    var from = Number(arguments[1]) || 0;
    from = (from < 0) ? Math.ceil(from) : Math.floor(from);
    if (from < 0) from += len;
    for (; from < len; from++) {
      if (from in this && this[from] === elt) return from;
    }
    return -1;
  };
}

if (!Array.prototype.forEach) {
  Array.prototype.forEach = function(func) {
    for (var i = 0; i < this.length; i++) func(this[i]);
  };
}

if (Raphael && !Raphael.el.conditionalClass) {
  Raphael.el.conditionalClass = function(cls, value) {
	var classes = (this.node.getAttribute("class") || "").split(" ");
	if ((classes.indexOf(cls) > -1) == value) return;
	if (value) classes.push(cls);
	else classes.remove(cls);
	this.node.setAttribute("class", classes.join(" "));
  };
}

Boolean.parse = function (str) {
  if (str == true || str == false) return str;
  switch (str.toLowerCase ()) {
    case "true":
      return true;
    case "false":
      return false;
    default:
      throw new Error ("Boolean.parse: Cannot convert string to boolean.");
  }
};

var Vector = Class.extend({
	init: function(coord) {
		this.c = coord;
	},
	length: function() {
		return Math.sqrt(this.c.x*this.c.x+this.c.y*this.c.y);
	},
	sub: function(v) {
		this.c.x -= v.c.x;
		this.c.y -= v.c.y;
		return this;
	},
	add: function(v) {
		this.c.x += v.c.x;
		this.c.y += v.c.y;
		return this;
	},
	mult: function(d) {
		this.c.x *= d;
		this.c.y *= d;
		return this;
	},
	div: function(d) {
		this.c.x /= d;
		this.c.y /= d;
		return this;
	},
	clone: function() {
		return new Vector({x: this.c.x, y: this.c.y});
	},
	str: function() {
		return this.c.x + "," + this.c.y;
	}
});

log = function(msg) {
	if (typeof(console)!="undefined") console.log(msg);
};

table_row = function(elements) {
	var tr = $('<tr/>');
	for (var i=0; i<elements.length; i++) tr.append($('<td/>').append(elements[i]));
	return tr;
};

pattern = {
	int: /^\d+$/,
	float: /^\d+(\.\d+)?$/,
	ip4: /^\d+\.\d+\.\d+\.\d+$/,		
	ip6: /^([0-9A-Fa-f]{1,4}:){0,7}([0-9A-Fa-f]{1,4})?(:[0-9A-Fa-f]{1,4}){0,7}$/,		
	ip4net: /^\d+\.\d+\.\d+\.\d+\/\d+$/,
	ip6net: /^([0-9A-Fa-f]{1,4}:){0,7}([0-9A-Fa-f]{1,4})?(:[0-9A-Fa-f]{1,4}){0,7}\/\d+$/
};

copy = function(orig, deep) {
	switch (typeof(orig)) {
		case "object":
			if (orig.slice != null) return orig.map(function(el) {
				return deep ? copy(el, deep) : el;
			});
			var c = {};
			for (var name in orig) c[name] = deep ? copy(orig[name], deep) : orig[name];
			return c;
		default:
			return orig;
	}
}

isIE = /MSIE (\d+\.\d+);/.test(navigator.userAgent);
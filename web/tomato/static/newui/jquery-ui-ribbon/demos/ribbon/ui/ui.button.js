/*
 * jQuery UI Button
 *
 * Copyright (c) 2009 sompylasar (maninblack.msk@hotmail.com ; http://maninblack.info/)
 * Licensed under the MIT (MIT-LICENSE.txt)
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 * 
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
/**
 * Depends on:
 *	ui.core.js
 *  ui.core.css
 *  ui.theme.css
 *  ui.button.css
 */
(function($) {

	var uiButtonClasses = {
		widgetBase: 'ui-button',
		widgetSpec: 'ui-widget ui-helper-clearfix ui-corner-all',
		idle: 'ui-state-default',
		hover: 'ui-state-hover',
		down: 'ui-state-down ui-state-active',
		focus: 'ui-state-focus',
		disabled: 'ui-state-disabled',
		checked: 'ui-button-checked ui-state-highlight',
		label: 'ui-button-label',
		icon: 'ui-button-icon',
		iconNone: 'ui-button-icon-none', // to be able to handle the icon's parents differently if no icon (Safari padding bug)
		slidingDoorsLeft: 'ui-button-door-left',
		visualProxy: 'ui-button-proxy',
		inputProxy: 'ui-button-inputproxy'
	};
	
	var uiButtonModes = {
		normal: '',
		toggle: 'ui-button-toggle'
	};
	
	var uiIconClasses = {
		widgetBase: 'ui-icon',
		widgetSpec: '',
		none: 'ui-icon-none'
	};
	var uiButtonIconPlacementClasses = {
		left: 'ui-button-icon-left',
		right: 'ui-button-icon-right',
		solo: 'ui-button-icon-solo'
	};
	
	var uiButtonEvents = {
		widgetEventPrefix: 'button',
		click: 'click',
		mouseenter: 'mouseenter',
		mouseleave: 'mouseleave',
		dragstart: 'dragstart',
		dragend: 'dragend',
		focus: 'focus',
		blur: 'blur',
		pressed: 'pressed', // not HTML5 but useful (occurs whenever the button gets into 'down' state)
		released: 'released', // not HTML5 but useful (occurs whenever the button gets back from 'down' to other state)
		action: 'action' // not HTML5 but useful (occurs when clicked or pressed with ENTER or SPACE)
	};
	
	var createEventArgs = function (widget) {
		return {
			options: $.extend(widget.options, {}), // clone the options
			eventArgs: true
		};
	};
	
	var mouse_captured_by = null, keyboard_captured_by = null;
	var button_under_cursor = null;
	
	var handleReleaseOutside = function (event) {
		if (mouse_captured_by) {
			// release outside
			//$('#log').prepend('release outside<br />');
			
			mouse_captured_by.element.removeClass(uiButtonClasses.down).removeClass(uiButtonClasses.hover); 
			mouse_captured_by._trigger(uiButtonEvents.dragend, event, createEventArgs(mouse_captured_by)); 
			mouse_captured_by.userinput_sink.blur();
			
			mouse_captured_by._updateCheckedClasses();
			
			mouse_captured_by = null;
			
			if (button_under_cursor) {
				button_under_cursor.element.addClass(uiButtonClasses.hover);
				button_under_cursor._trigger(uiButtonEvents.mouseenter, event, createEventArgs(button_under_cursor)); 
			}
		}
	};
	
	$(function () {
		var mouse_tester = $('body')
			.bind('mouseup.ui-button', function(event) { 
				handleReleaseOutside(event);
			});
		$(window).bind('unload', function () {
			mouse_tester.unbind('.ui-button');
			mouse_tester = null;
		});
	});
	
	$.widget("ui.button", {
		_init: function() {
			var self = this,
				options = this.options;
			
			if (this.element.is(':not(input[type=button], input[type=submit], input[type=reset], a, button, span, div)'))
				throw 'Element ' + this.element[0].tagName + ' is not supported as a button';
				
			var isChecked = false;
			
			this.element_supports_children  = this.element.is(':not(input)');
			this.element_text_in_value_attr = this.element.is('input');
			this.element_needs_href_fix     = this.element.is('a') && !this.element.attr('href');
			
			// store initial values to restore them on destroy
			this.oldChildren = (this.element_supports_children ? this.element.children() : undefined);
			this.oldAttrs = {};
			this.oldAttrs.title = this.element.attr('title'); // will be set later explicitly
			this.oldAttrs.href  = (this.element_needs_href_fix ? this.element.attr('href') : undefined);
			this.oldAttrs.tabindex = this.element[0].getAttribute('tabindex'); // .attr('tabindex') normalizes, we need raw value
			if (this.oldAttrs.tabindex == null) this.oldAttrs.tabindex = undefined;
			
			$.each(['id', 'name', 'value', 'class', 'style', 'disabled'], function (i, attrName) { // these attrs are just copied
				self.oldAttrs[attrName] = self.element.attr(attrName);
			});
			
			if (options.buttonMode == null) {
				$.each(uiButtonModes, function (mode, className) {
					if (self.element.hasClass(className)) { options.buttonMode = mode; return false; }
				});
			}
			
			if (this.element_supports_children) {
				if (this.element_needs_href_fix) 
					this.element.attr('href', '#'); // to be able to get focus
				
				this.button = this.element;
			}
			else {
				this.button = $('<button type="button"></button>')
					.addClass(uiButtonClasses.visualProxy)
					.attr('for', this.oldAttrs.id) // BUG: jQuery adds 'htmlfor' attribute, not 'for'
					.insertAfter(this.element);
				
				$.data(this.button[0], this.widgetName, this);
				
				if (options.icon == null) {
					options.icon = this._getIconClassname(this.element) || null;
				}

				$.each(['id', 'name', 'class', 'style', 'disabled'], function (i, attrName) { // these attrs are moved to new control
					self.button.attr(attrName, self.element.attr(attrName));
					self.element.removeAttr(attrName);
				});
				
				this.element.hide()
					.removeAttr('tabindex').removeAttr('accesskey'); // these attrs will be set on userinput_sink
			}
			
			this.button.attr('title', (options.tooltip || this.oldAttrs.title || '')); // set title attr in all cases
			options.tooltip = this.button.attr('title');
			
			this.button_supports_userinput = this.button.is('input, button' + ($.browser.safari || $.browser.opera ? '' : ', a'));
			
			// set up the icon
			this.icon = this.element.find('.'+uiButtonClasses.icon.replace(/\s+/,'.')).remove().eq(0);
			if (!this.icon.length) {
				this.icon = $('<span></span>')
					.addClass(uiButtonClasses.icon);
			}
			this.iconImage = this.icon.find('img, .'+uiIconClasses.widgetBase).add(this.element.find('.'+uiIconClasses.widgetBase)).remove().eq(0);
			if (!this.iconImage.length) {
				this.iconImage = $('<span></span>')
					.addClass(uiIconClasses.widgetBase + ' ' + uiIconClasses.widgetSpec);
			}
			this.icon.append(this.iconImage);
			if (options.icon == null) {
				options.icon = this._getIconImageOption(this.iconImage);
			}
			
			// set up the button text
			this.label = this.element.find('.'+uiButtonClasses.label.replace(/\s+/,'.')).remove().eq(0);
			if (!this.label.length) {
				this.label = $('<span></span>')
					.addClass(uiButtonClasses.label)
					.html( this.element_text_in_value_attr ? this.oldAttrs.value : this.element.html() );
			}
			if (options.text != null) this.label.empty().append(options.text);
			options.text = this.label.html();
			
			this.label.disableSelection();
			
			// set up an element to handle user input
			if (this.button_supports_userinput) {
				this.userinput_sink = this.button;
			}
			else {
				this.userinput_sink = $('<button type="button" style="width:0px"></button>')
					.addClass(uiButtonClasses.inputProxy)
					.addClass('ui-helper-hidden-accessible')
					.attr('for', this.oldAttrs.id) // BUG: jQuery adds 'htmlfor' attribute, not 'for'
					.insertAfter(this.button);
			}
			
			// set up tabindex
			if (options.tabindex != null) {
				this.userinput_sink.attr('tabindex', options.tabindex);
			}
			else if (typeof this.oldAttrs.tabindex != 'undefined') {
				this.userinput_sink.attr('tabindex', this.oldAttrs.tabindex);
			}
			
			// set up accesskey
			if (options.accesskey != null) {
				this.userinput_sink.attr('accesskey', options.accesskey);
			}
			else if (typeof this.oldAttrs.accesskey != 'undefined') {
				this.userinput_sink.attr('accesskey', this.oldAttrs.accesskey);
			}
			
			// set up button handlers
			var keydown_code = -1;
			this.button
				.bind('mousedown.ui-button', function(event) { 
					if (self._isActionAvailable()) {
						mouse_captured_by = self;
						
						self.button.addClass(uiButtonClasses.down);
						self._trigger(uiButtonEvents.pressed, event, createEventArgs(self))
						
						self.userinput_sink.focus();
					}
				})
				.bind('mouseup.ui-button', function(event) {
					if (mouse_captured_by == self) {
						mouse_captured_by = null;
						
						self.button.removeClass(uiButtonClasses.down);
						self._trigger(uiButtonEvents.released, event, createEventArgs(self));
						
						if (options.buttonMode == 'toggle') self._toggleChecked();
						
						self._trigger(uiButtonEvents.click, event, createEventArgs(self));
						self._trigger(uiButtonEvents.action, event, createEventArgs(self)); 
						
						//self.userinput_sink.blur(); // browsers don't remove focus on release
					}
					else {
						handleReleaseOutside(event);
					}
				})
				.bind('mouseenter.ui-button', function(event) { 
					button_under_cursor = self;
					if (!mouse_captured_by || mouse_captured_by == self) {
						self.button.addClass(uiButtonClasses.hover);
						self._trigger(uiButtonEvents.mouseenter, event, createEventArgs(self));
					}
					if (mouse_captured_by == self) { // mouse was pressed, than moved out, and now is back and still is pressed
						self.button.addClass(uiButtonClasses.down); // restore down state
					}
				})
				.bind('mouseleave.ui-button', function (event) { 
					button_under_cursor = null;
					if (!mouse_captured_by || mouse_captured_by == self) {
						self.button.removeClass(uiButtonClasses.down);
					}
					if (!mouse_captured_by) { // mouse was released inside
						self.button.removeClass(uiButtonClasses.hover);
					}
					if (!mouse_captured_by || mouse_captured_by == self) {
						self._trigger(!mouse_captured_by ? uiButtonEvents.mouseleave : uiButtonEvents.dragstart, event, createEventArgs(self)); 
					}
					
					self._updateCheckedClasses();
				})
				.bind('click.ui-button', function (event) {
					if (typeof event.clientX != 'undefined') {
						event.stopImmediatePropagation();
						//event.stopPropagation();
						return false;
					}
				})
				.bind('contextmenu.ui-button', function (event) { 
					if (options.preventContextMenu) event.preventDefault(); 
				});
			
			// set up user input handlers
			this.userinput_sink
				.bind('focus.ui-button', function (event) { 
					if (!self._isFocused() && self._isActionAvailable()) {
						self.button.add(self.userinput_sink).addClass(uiButtonClasses.focus);
						self._trigger(uiButtonEvents.focus, event, createEventArgs(self))
					}
					return false;
				})
				.bind('blur.ui-button', function (event) { 
					if (self._isFocused()) {
						self._trigger(uiButtonEvents.blur, event, createEventArgs(self))
					}
					self.button.add(self.userinput_sink).removeClass(uiButtonClasses.focus);
					return false;
				})
				.bind('keydown.ui-button', function (event) {
					if (self._isFocused() && !keyboard_captured_by && self._isActionAvailable()) {
						if (event.keyCode == $.ui.keyCode.ENTER || event.keyCode == $.ui.keyCode.SPACE) {
							keydown_code = event.keyCode;
							keyboard_captured_by = self;
							
							self.button.addClass(uiButtonClasses.down);
							self._trigger(uiButtonEvents.pressed, event, createEventArgs(self)); 
							
							return false; // prevent further dispatching of a keypress
						}
					}
					
					if (self._isFocused()) {
						if (event.keyCode == $.ui.keyCode.ESCAPE) {
							keydown_code = -1; // cancel action
							
							if (keyboard_captured_by == self || mouse_captured_by == self) {
								keyboard_captured_by = null;
								mouse_captured_by = null;
								
								self.button.removeClass(uiButtonClasses.down);
								self._updateCheckedClasses();
								self._trigger(uiButtonEvents.released, event, createEventArgs(self)); 
							}
							
							return false; // prevent further dispatching of a keypress
						}
					}
				})
				.bind('keyup.ui-button', function (event) {
					if (self._isFocused() && self._isActionAvailable()) {
						if (event.keyCode == keydown_code) {
							keydown_code = -1;
							keyboard_captured_by = null;
							
							self.button.removeClass(uiButtonClasses.down);
							self._trigger(uiButtonEvents.released, event, createEventArgs(self)); 
							
							if (options.buttonMode == 'toggle') self._toggleChecked();
							
							self._trigger(uiButtonEvents.keypress, event, createEventArgs(self)); 
							self._trigger(uiButtonEvents.action, event, createEventArgs(self)); 
							
							return false; // prevent further dispatching of a keypress
						}
					}
				});
			
			if (this.userinput_sink != this.button) {
				this.button
					.bind('focus.ui-button', function (event) { return self.userinput_sink.trigger(event); })
					.bind('blur.ui-button', function (event) { return self.userinput_sink.trigger(event); })
			}
				
			this.button.empty().append(this.label).prepend(this.icon);
			
			options.icon = this._setupIcon(options.icon);
			options.useSlidingDoors = this._setupSlidingDoors(options.useSlidingDoors);
			
			options.priority = this._setupPriority(options.priority);
			
			options.buttonMode = this._setupButtonMode(options.buttonMode);
			
			this.button.addClass(uiButtonClasses.widgetBase + ' ' + uiButtonClasses.widgetSpec 
				+ ' ' + uiButtonClasses.idle);
			
			// set up disabled state
			if (this.element.is(':disabled')) {
				this.disable();
			}
		},

		destroy: function() {
			var self = this;
			
			if (this.button == this.element) {
				this.button
					.unbind('.ui-button')
					.removeClass(uiButtonClasses.widgetBase + ' ' + uiButtonClasses.widgetSpec
						+ ' ' + uiButtonClasses.idle
						+ ' ' + uiButtonClasses.hover
						+ ' ' + uiButtonClasses.down
						+ ' ' + uiButtonClasses.focus
						+ ' ' + uiButtonClasses.checked);
				this.button[0].className = this.button[0].className.replace(/\bui-button-([a-z-]+)\b/ig, '');
				
				if (this.element_supports_children && this.oldChildren) {
					this.element
						.children().remove().end()
						.append(this.oldChildren);
				}
			}
			else {
				this.button.remove();
			}
			
			if (this.userinput_sink != this.button)
				this.userinput_sink.remove();
			
			$.each(this.oldAttrs, function (attrName, value) {
				if (typeof value != 'undefined')
					self.element.attr(attrName, self.button.attr(attrName) || value); // the values may have been changed on new control, so copy them back
			});
			
			$.widget.prototype.destroy.apply(this, arguments);
		},
		
		disable: function () { 
			this.button.add(this.element).addClass('ui-state-disabled').attr('disabled', 'disabled');
			
			$.widget.prototype.disable.apply(this, arguments);
		},
		enable: function () { 
			this.button.add(this.element).removeClass('ui-state-disabled').removeAttr('disabled', 'disabled');
			
			$.widget.prototype.enable.apply(this, arguments);
		},
		
		originalElement: function () {
			return this.element;
		},
		
		_setChecked: function (checked) {
			this.options.checked = checked;
			this._updateCheckedClasses();
		},
		_toggleChecked: function () {
			if (this.options.buttonMode == 'toggle') this._setChecked(!this.options.checked);
		},
		_updateCheckedClasses: function () { // from checked state
			if (this.options.buttonMode == 'toggle' && this.options.checked) this.button.addClass(uiButtonClasses.checked);
			else this.button.removeClass(uiButtonClasses.checked);
		},
		
		_trigger: function (type, event, data) {
			var ret;
			
			$.widget.prototype._trigger.apply(this, arguments); // goes to original element
			
			if (this.button != this.element 
				&& event 
				&& event.isImmediatePropagationStopped 
				&& !event.isImmediatePropagationStopped()) 
			{
				var element = this.element;
				this.element = this.button;
				$.widget.prototype._trigger.apply(this, arguments); // goes to button
			}
		},
		
		_isEnabled: function () {
			return !(this.button.hasClass(uiButtonClasses.disabled) || this.button.is('.ui-state-disabled, [disabled]')
				|| (this.element != this.button && this.element.hasClass(uiButtonClasses.disabled) || this.element.is('.ui-state-disabled, [disabled]')));
		},
		_isFocused: function () {
			return this.button.hasClass(uiButtonClasses.focus);
		},
		_isDown: function () {
			return this.button.hasClass(uiButtonClasses.down);
		},
		_isVisible: function () {
			return this.button.is(':visible');
		},
		_isActionAvailable: function () {
			return (this._isEnabled() && this._isVisible());
		},

		_setupIcon: function(icon) {
			if (icon) {
				this.iconImage.removeClass(this.options.icon).css('backgroundImage', '');
				
				if (/^url\(.*\)$/.test(icon)) {
					this.iconImage.css('backgroundImage', icon);
				}
				else {
					this.iconImage.addClass(icon);
				}
				if (icon != uiIconClasses.none) this.button.removeClass(uiButtonClasses.iconNone);
			}
			else if (icon == null) {
				this.iconImage.removeClass(this.options.icon).css('backgroundImage', '').addClass(uiIconClasses.none);
				this.button.addClass(uiButtonClasses.iconNone);
			}
			
			return icon;
		},
		_setupIconMode: function(iconMode) {
			if (this.options.iconMode) this.button.removeClass(uiButtonIconPlacementClasses[this.options.iconMode]);
			if (iconMode) this.button.addClass(uiButtonIconPlacementClasses[iconMode]);
			
			return iconMode;
		},
		_setupButtonMode: function(buttonMode) {
			if (this.options.buttonMode) this.button.removeClass(uiButtonModes[this.options.buttonMode]);
			if (buttonMode) this.button.addClass(uiButtonModes[buttonMode]);
			
			this._updateCheckedClasses();
			
			return buttonMode;
		},
		_setupPriority: function(priority) {
			this.button.removeClass('ui-priority-' + this.options.priority)
			if (priority) this.button.addClass('ui-priority-' + priority);
		},
		_setupSlidingDoors: function (use) {
			this.door = this.button.find('.'+uiButtonClasses.slidingDoorsLeft);
			if (use && !this.door.length) {
				this.door = $('<span class="'+uiButtonClasses.slidingDoorsLeft+'"></span>');
				this.button.append(this.door.append(this.button.children()));
			}
			else if (!use && this.door.length) {
				this.button.append(this.door.children());
				this.door.remove();
			}
			
			return use;
		},
		
		_getIconImageOption: function ($iconImage) {
			var icon = null;
			$iconImage = $iconImage || this.iconImage;
			if ($iconImage.is('img')) {
				icon = this.iconImage.attr('src') || null;
			}
			else {
				icon = this._getIconClassname($iconImage) || null;
			}
			return icon;
		},
		_getIconClassname: function ($elem) {
			if ($elem && $elem.length) {
				var className = /\b(ui-icon-[a-z-]+)\b/.exec($elem[0].className);
				if (className != null)
					return className[0];
			}
			return '';
		},

		_setData: function(key, value) {
			switch(key) {
				case 'icon':
					arguments[1] = value = this._setupIcon(value);
					break;
				case 'text':
					if (this.element_text_in_value_attr) this.element.val(value);
					this.label.html(value);
					break;
				case 'tooltip':
					this.button.attr('title', value || '');
					break;
				case 'tabindex':
					if (value != null) this.userinput_sink.attr('tabindex', value);
					else this.userinput_sink.removeAttr('tabindex', value);
					break;
				case 'priority':
					arguments[1] = value = this._setupPriority(value);
					break;
				case 'iconMode':
					arguments[1] = value = this._setupIconMode(value);
					break;
				case 'buttonMode':
					arguments[1] = value = this._setupButtonMode(value);
					break;
				case 'checked':
					this._setChecked(value);
					break;
				case 'useSlidingDoors':
					arguments[1] = value = this._setupSlidingDoors(value);
					break;					
			}
			$.widget.prototype._setData.apply(this, arguments);
		},
		
		_getMouseButtonCode: function (event) {
			var button = null;

			var s = ''; 
			
			if (event.button != null)
		       button = (event.button < 2) ? 0/*"LEFT"*/ :
		                 ((event.button == 4) ? 2/*"MIDDLE"*/ : 1/*"RIGHT"*/);
		    else if (event.which != null)
		       button = (event.which < 2) ? 0/*"LEFT"*/ :
		                 ((event.which == 2) ? 2/*"MIDDLE"*/ : 1/*"RIGHT"*/);
						 
			return button;
		}
	});

	$.extend($.ui.button, {
		version: '1.7.1',
		eventPrefix: uiButtonEvents.widgetEventPrefix,
		defaults: {
			text: null, // if .text == null, the element's html is used (or value attr for input[type=button], input[type=submit], input[type=reset]
			tooltip: null, // if .tooltip == null, the element's title attr is used
			tabindex: null, // if .tabindex == null, the element's tabindex attr is used
			priority: null, // null | 'primary' | 'secondary' - sets .ui-priority-* class on the button
			icon: null, // if .icon == '', .ui-icon-none class is added to the icon
			iconMode: 'left', // null | 'left' | 'right' | 'solo' - sets the corresponding class from uiButtonIconPlacementClasses on the button
			buttonMode: null, // null | 'normal' | 'toggle'
			useSlidingDoors: false,  // generates a span.ui-button-left-door wrapper for the button content
			preventContextMenu: true // prevents default behavior for contextmenu event
		},
		getter: 'originalElement'
	});

})(jQuery);

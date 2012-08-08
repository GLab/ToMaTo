/*
 * jQuery UI Ribbon
 *
 * Copyright (c) 2008, 2009 Babak (babak@fintech.ru)
 *
 * Depends:
 *	ui.core.js
 *	jquery.blockUI.js 
 */
;(function($) {

$.widget("ui.orbButton", {
	_init: function() {
		this.options.event += '.ui-orbButton'; // namespace event
		
		this.extend(true);
	},
	setData: function(key, value) {
		
	},
	extend: function(init) {
	
		var self = this, o = this.options;
		
		/*var fakeEvent = function(type) {
		    return $.event.fix({
			    type: type,
			    target: this.element[0]
		    });
	    };*/
		var triggerWithResult = function (type, eventArgs) {
			return $.event.trigger(type + '.ui-orbButton', [ eventArgs ], self.element[0]);
		};
		
		
		var createMenuItemEventArgs = function(item) {
		    return {
			    options: self.options,
			    item: item,
			    index: self.$lis.index( item ),
			    eventArgs: true
		    };
	    };
	    var createMenuFooterButtonEventArgs = function (button) {
	        return {
			    options: self.options,
			    button: button,
			    eventArgs: true
		    };
	    };
		
		
		this.animating = false;
		
		this.$menu = $('.' + o.menuPlaceholderClass, this.element);
		this.$button = $('.' + o.buttonClass, this.element);
		this.$lis = $('.' + o.menuPlaceholderClass + ' li', this.element);
		
		var $menuExtended = $('.'+o.menuExtendedClass, this.element);
		
		
		if (init) {

			// attach necessary classes for styling if not present
			this.element.addClass('ui-widget').addClass(o.containerClass);
			
			this.$menu.addClass(o.menuPlaceholderHideClass);
			$(':first', this.$lis).addClass('first');
			$(':last', this.$lis).addClass('last');
			
			this.$menuContainer = this.$menu.find('div:eq(0)').addClass(o.menuContainerClass);
			this.$menuFooter    = this.$menu.find('div:eq(1)').addClass(o.menuFooterClass);
		
			// clean up to avoid memory leaks in certain versions of IE 6
			$(window).bind('unload', function() {
				self.$menu = null;
				self.$button = null;
			});

		}
		
		
		// set up animations
		var hideFx = { 'opacity': 0.0, duration: 400 }, showFx = { 'opacity': 1.0, duration: 400 }, baseDuration = 'slow';
		if (o.fx) {
			if (o.fx.constructor == Array)
				hideFx = o.fx[0] || hideFx, showFx = o.fx[1] || showFx;
			else
				hideFx = showFx = o.fx;
		}
		
		var blockSettings = { message: null, overlayCSS: { opacity: 0.0 }, fadeIn: 0, fadeOut: 0 };
		
		
		// menu item that was expanded
		var $expanded_a = null;
		
		
		
		this.isVisiblePlaceholder = function () {
			return (!self.$menu.hasClass(o.menuPlaceholderHideClass) && self.$menu.is(':visible'));
		};
		this.showMenuPlaceholder = function() {
			var res = triggerWithResult('menu-before-show', {}); // TODO: eventArgs
			if (res === false)
				return false;
				
			var $menu = self.$menu;
			var $button = self.$button;
			
			var changed = !self.isVisiblePlaceholder();
			
			if (changed) {
				//alert('orbButton showMenu');
				
				self.animating = true;
				if ($menu.block && $menu.unblock) $menu.block(blockSettings);
				
				// stop possibly running animations
				$menu.stop();
				
				$button.addClass('selected');
				$menu.css({	opacity: 0.0 });
				$menu.removeClass(o.menuPlaceholderHideClass);
				
				$menu.animate(showFx, {
					duration: showFx.duration || baseDuration, 
					complete: function() {
						$menu.removeClass(o.menuPlaceholderHideClass);

						if ($.browser.msie && showFx.opacity)
							$menu[0].style.filter = '';
							
						self.animating = false;
						if ($menu.block && $menu.unblock) $menu.unblock();
						
						// callback
						triggerWithResult('menu-shown', {}); // TODO: eventArgs
					}
				});
			}
			
			return changed;
		}
		this.hideMenuPlaceholder = function() {
			var res = triggerWithResult('menu-before-hide', {}); // TODO: eventArgs
			if (res === false)
				return false;
				
			var $menu = self.$menu;
			var $button = self.$button;
			
			var changed = self.isVisiblePlaceholder();
			
			if (changed) {
				self.animating = true;
				if ($menu.block && $menu.unblock) $menu.block(blockSettings);
				
				if ($expanded_a) $expanded_a.trigger('split-collapse');
				
				// stop possibly running animations
				$menu.stop();
				
				$menu.animate(hideFx, { 
					duration: hideFx.duration || baseDuration, 
					complete: function() {
						$button.removeClass('selected');
						
						$menu.addClass(o.menuPlaceholderHideClass);

						if ($.browser.msie && hideFx.opacity)
							$menu[0].style.filter = '';
							
						self.animating = false;
						if ($menu.block && $menu.unblock) $menu.unblock();
						
						// callback
						triggerWithResult('menu-hidden', {}); // TODO: eventArgs
					}
				});
			}
			
			return changed;
		}
		this.toggleMenuPlaceholder = function() {
			var changed = true;
			
			if (self.isVisiblePlaceholder()) {
				self.hideMenuPlaceholder();
			}
			else {
				self.showMenuPlaceholder();
			}
			
			return changed;
		}
		
		// attach events
		this.$button.unbind('.ui-orbButton').bind(o.event, function(event) {
			if (event.which === 1) {
				if (self.toggleMenuPlaceholder()) {
					event.stopPropagation();
				}
			}
		});
		
		
		$menuExtended.unbind('.ui-orbButton').bind('mouseenter.ui-orbButton', function(event) {
			if ($expanded_a) $expanded_a.addClass('split-hover');
		}).bind('mouseleave.ui-orbButton', function(event) {
			//if ($expanded_a) $expanded_a.removeClass('split-hover');
		});
		
		$('.'+o.menuClass+' a[rel]', this.element).each(function () {
			var $a = $(this);
			
			var extended_id = $a.attr('rel');
			if ( $('#'+extended_id, $menuExtended).length > 0 ) {
				$a.addClass('split').addClass('split-right');
			}
		});
		
		this.$menuFooter.find('a').unbind('.ui-orbButton').bind('click.ui-orbButton', function(event) {
			$(this).blur();
			
			if (self.animating) {
				return false;
			}
			
			if (event.which === 1) {
				var button = $(this)[0];

				// callback
				var res = triggerWithResult('menu-footer-button-click', createMenuFooterButtonEventArgs(button));
				
				if (res !== false)
					self.hideMenuPlaceholder();
				
				return false;
			}
		});
		
		this.$menuContainer.find('.'+o.menuClass+' a').unbind('.ui-orbButton').bind('click.ui-orbButton', function(event) {
			$(this).blur();
			
			if (self.animating) {
				return false;
			}
				
			if (event.which === 1) {
				var item = $(this).parent('li')[0];

				// callback
				var res = triggerWithResult('menu-item-click', createMenuItemEventArgs(item));
				
				if (res !== false)
					self.hideMenuPlaceholder();
				
				return false;
			}
		}).bind('split-expand.ui-orbButton', function () {
			var $item = $(this).parent('li'), 
				$a = $item.find('a'),
				item = $item[0];
				
			var extended_id = $a.attr('rel');
			if (extended_id) {
				$expanded_a = $a;
				$menuExtended.children().hide();
				$menuExtended.find('#'+extended_id).show();
				
				triggerWithResult('menu-item-expanded', createMenuItemEventArgs(item));
			}
		}).bind('split-collapse.ui-orbButton', function () {
			var $item = $(this).parent('li'), 
				$a = $item.find('a'),
				item = $item[0];
			
			if ($expanded_a) $expanded_a.removeClass('split-hover');
			$expanded_a = null;
			
			var extended_id = $a.attr('rel');
			if (extended_id) {
				$menuExtended.find('#'+extended_id).hide();
				
				triggerWithResult('menu-item-collapsed', createMenuItemEventArgs(item));
			}
		}).bind('focus.ui-orbButton', function () {
			$(this).triggerHandler('mouseenter.ui-orbButton');
		}).bind('mouseenter.ui-orbButton', function () {
			var $item = $(this).parent('li'), 
				$a = $item.find('a'),
				item = $item[0];
			
			$('.'+o.menuClass+' a', self.element).trigger('split-collapse');
			$a.trigger('split-expand');
			
			triggerWithResult('menu-item-enter', createMenuItemEventArgs(item));
		}).bind('mouseleave.ui-orbButton', function () {
			var item = $(this).parent('li')[0];
			
			triggerWithResult('menu-item-leave', createMenuItemEventArgs(item));
		});
		$('.'+o.menuPlaceholderClass+'', this.element).unbind('.ui-orbButton').bind('click.ui-orbButton', function(event) {
			if (self.animating) {
				return false;
			}
		});
		
		$(document).unbind('.ui-orbButton').bind('click.ui-orbButton', function(event) {
			if (event.which === 1) {
				if ( $(event.target).parents('.'+o.containerClass).length ) {
					return;
				}
				
				if (self.isVisiblePlaceholder()) {
					self.hideMenuPlaceholder();
					
					return false;
				}
			}
		});
		
		// disable click if event is configured to something else
		if (!(/^click/).test(o.event))
			this.$button.bind('click.ui-orbButton', function() { return false; });
	},
	showMenu: function () {
		return this.showMenuPlaceholder();
	},
	hideMenu: function () {
		return this.hideMenuPlaceholder();
	},
	toggleMenu: function () {
		return this.toggleMenuPlaceholder();
	},
	isVisible: function () {
		return this.isVisiblePlaceholder();
	},
	disableMenu: function () {
		$('a', this.$lis).addClass(o.disabledClass);
	},
	enableMenu: function () {
		$('a', this.$lis).removeClass(o.disabledClass);
	},
	hasMenuItem: function (li) {
		var found = false;
		this.$lis.each(function () { found = (this === li); if (found) return false; });
		return found;
	},
	disableMenuItem: function (li) {
		if (!this.hasMenuItem(li)) return;
		
		$('a', li).addClass(o.disabledClass);
	},
	enableMenuItem: function (li) {
		if (!this.hasMenuItem(li)) return;
		
		$('a', li).removeClass(o.disabledClass);
	},
	destroy: function() {
		var o = this.options;
		this.element.unbind('.ui-orbButton')
			.removeClass(o.containerClass);
	}
});

$.ui.orbButton.defaults = {
	// basic setup
	event: 'click',
	cookie: null, // e.g. { expires: 7, path: '/', domain: 'jquery.com', secure: true }
	// TODO history: false,
	
	fx: null, // e.g. { height: 'toggle', opacity: 'toggle', duration: 200 }

	// CSS classes
	containerClass: 'ui-orbButton',
	menuPlaceholderClass: 'menu-placeholder',
	menuPlaceholderHideClass: 'ui-orbButton-menu-placeholder-hidden',
	menuClass: 'ui-orbButton-menu-main',
	menuContainerClass: 'ui-orbButton-menu',
	menuFooterClass: 'ui-orbButton-menu-footer',
	menuExtendedClass: 'ui-orbButton-menu-extended',
	buttonClass: 'orbButton',
	disabledClass: 'disabled'
};

$.ui.orbButton.getter = "isVisible hasMenuItem";

})(jQuery);

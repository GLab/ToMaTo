/*
 * jQuery UI Ribbon
 *
 * Copyright (c) 2008, 2009 sompylasar (maninblack.msk@hotmail.com ; http://maninblack.info/)
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
 * jQuery UI Ribbon
 *
 * Depends on:
 *  jquery-1.3.2.js
 *	ui.core.js
 *	ui.tabs.js
 *  ui.core.css
 *  ui.theme.css
 *  ui.tabs.css
 *  ui.ribbon.css
 */
;(function($) {

	var uiRibbonClasses = {
        base: 'ui-ribbon',
        ribbonMinimized: 'ui-ribbon-minimized',
		ribbonMinimizedBorder: 'ui-ribbon-minimized-border',
		
		tabsetContextual: 'ui-ribbon-tabset-contextual',
		tabsetsCollapsed: 'ui-ribbon-tabsets-collapsed',
		
		tabsList: 'ui-ribbon-tabs',
		tab: 'ui-ribbon-tab',
        tabContextual: 'ui-ribbon-tab-contextual',
        
        panel: 'ui-ribbon-panel',
        panelContextual: 'ui-ribbon-panel-contextual',
		
        group: 'ui-ribbon-group',
        groupContent: 'ui-ribbon-group-content',
        groupLabel: 'ui-ribbon-group-label',
        groupDialogButton: 'ui-ribbon-group-dialog-button',
		groupHighlight: 'ui-state-hover ui-state-highlight',
		
		element: 'ui-ribbon-element',
		control: 'ui-ribbon-control',
		controlsList: 'ui-ribbon-list'
	};
	
	var createEventArgs = function(widget) {
		return {
			options: $.extend(widget.options, {}), // clone the options
			eventArgs: true
		};
	};
	var createTabEventArgs = function(widget, tab, panel, index) {
		return $.extend({
			tab: tab,
			panel: panel,
			index: index,
			eventArgs: true
		}, createEventArgs(widget));
	};
	var createGroupEventArgs = function(widget, tab, panel, index, group) {
		return $.extend({
			group: group,
			eventArgs: true
		}, createTabEventArgs(widget, tab, panel, index));
	};
	

    $.widget("ui.ribbon", {
        _init: function() {
			this.widgetEventPrefix = 'ui-ribbon-';
			this.widgetBaseClass = uiRibbonClasses.base;
			
            this._extend();
        },
		_setData: function (key, value) {
			if (key == 'showTabsets') {
				if (arguments.length == 1) return this.options[key];
				else this.options[key] = value;
				
				this._updateAllTabsets();
			}
			else {
				this.$tabsWidget.tabs('option', key, value);
			}
		},
		
        enable: function(index) {
            if (!arguments.length) {
                var disabledIndexes = this.$tabsWidget.tabs('getData', 'disabled');
                $.log(disabledIndexes);

				var $tabsWidget = this.$tabsWidget;
                $.each(disabledIndexes, function(i, index) {
                    $tabsWidget.tabs('enable', index);
                });
            }
            else {
                this.$tabsWidget.tabs('enable', index);
            }
        },
        disable: function(index) {
            if (!arguments.length) {
                var enabledIndexes = [];
                var i = 0, len = this.$tabsWidget.tabs('length');
                while (i < len) { enabledIndexes.push(i); ++i; }
                $.log(enabledIndexes);

				var $tabsWidget = this.$tabsWidget;
                $.each(enabledIndexes, function(i, index) {
                    $tabsWidget.tabs('disable', index);
                });
            }
            else {
                this.$tabsWidget.tabs('disable', index);
            }
        },
        show: function(index) {
            this.$tabsWidget.tabs('show', index);
            this._updateAllTabsets('show');
        },
        hide: function(index) {
            this.$tabsWidget.tabs('hide', index);
            this._updateAllTabsets('hide');
        },
        showGroup: function(tabset_id, showAllTabs) {
            this._setTabsetVisibility(tabset_id, true, showAllTabs);
        },
        hideGroup: function(tabset_id) {
            this._setTabsetVisibility(tabset_id, false);
        },
        select: function(index) {
            this.$tabsWidget.tabs('select', index);
        },
		update: function() {
			this._updateAllTabsets();
		},
        load: function(index) {
            this.$tabsWidget.tabs('load', index);
        },
        url: function(index, url) {
            this.$tabsWidget.tabs('url', index, url);
        },
        destroy: function() {
            this.$tabsWidget.tabs('destroy');
			this.element.removeClass(uiRibbonClasses.base);
			
			$.widget.prototype.destroy.apply(this, arguments);
        },
		
        _extend: function() {
            var self = this, o = this.options;

            this.$panels = $([]);
			
			this.$tabsList = $('ul:eq(0)', this.element).addClass(uiRibbonClasses.tabsList);
			this.$minimizedBorder = this.$tabsList
				.after('<span></span>')
				.next('span:eq(0)')
				.addClass(uiRibbonClasses.ribbonMinimizedBorder)
				.addClass('ui-widget-content');
				
			this.$lis = this.$tabsList.children('li')
				.addClass(uiRibbonClasses.tab)
				.addClass('ui-priority-primary');
			
            this.$tabsWidget = $('<div></div>').append(this.element.children()).prependTo(this.element);

			this.element
				.addClass(uiRibbonClasses.base)
				.addClass('ui-widget ui-widget-content ui-helper-reset');
			
			this.$tabsWidget
				.tabs({
					event: 'click',
					disabled: o.disabled,
					cookie: o.cookie,
					history: o.history || false,
					collapsible: o.collapsible,

					spinner: o.spinner,
					cache: true,
					idPrefix: o.idPrefix,
					ajaxOptions: null,

					fx: o.fx
				})
				.removeClass('ui-widget-content ui-corner-all')
				.find('.ui-tabs-nav').removeClass('ui-corner-all ui-widget-header').addClass('ui-corner-top').end()
				.bind('tabsshow', function(event, info) {
					o.disabled = self.$tabsWidget.tabs('option', 'disabled');
					
					self._recalcAllTabsetsInfo();
					self._updateAllTabsets();

					self._trigger('tab-shown', null, createTabEventArgs(self, info.tab, info.panel, info.index));
				})
				.bind('tabshide', function(event, info) {
					o.disabled = info.options.disabled;
					
					self._recalcAllTabsetsInfo();
					self._updateAllTabsets();
					
					self._trigger('tab-hidden', null, createTabEventArgs(self, info.tab, info.panel, info.index));
				})
				.bind('tabsselect', function(event, info) {
					o.disabled = self.$tabsWidget.tabs('option', 'disabled');
					var opening = info.index,
						closing = self.$tabsWidget.tabs('option', 'selected');
					if (opening == closing) {
						// collapsing the currently open tab
						
						self.element.addClass(uiRibbonClasses.ribbonMinimized);
						self._trigger('minimized', null, createEventArgs(self));
					} 
					else if (closing == -1) {
						// opening after all panels have been collapsed
						
						self._recalcAllTabsetsInfo();
						self._updateAllTabsets();
						
						self.element.removeClass(uiRibbonClasses.ribbonMinimized);
						self._trigger('restored', null, createEventArgs(self));
					} 
					else {
						// changing tabs
						
						self._recalcAllTabsetsInfo();
						self._updateAllTabsets();
						
						self.$panels.eq(opening).addClass('ui-state-active');
						self._trigger('tab-selected', null, createTabEventArgs(self, self.$lis[opening], self.$panels[opening], opening));
						
						self.$panels.eq(closing).removeClass('ui-state-active');
						self._trigger('tab-deselected', null, createTabEventArgs(self, self.$lis[closing], self.$panels[closing], closing));
					}
				})
				.bind('tabsenable', function(event, info) {
					o.disabled = self.$tabsWidget.tabs('option', 'disabled');

					self._trigger('tab-enabled', null, createTabEventArgs(self, info.tab, info.panel, info.index));
				})
				.bind('tabsdisable', function(event, info) {
					o.disabled = self.$tabsWidget.tabs('option', 'disabled');

					self._trigger('tab-disabled', null, createTabEventArgs(self, info.tab, info.panel, info.index));
				});
            
            this.$panels = this.element.find('.ui-tabs-panel')
				.addClass(uiRibbonClasses.panel)
				.addClass('ui-widget-content ui-state-default ui-corner-all ui-helper-clearfix');
				
			this.$panels.eq( self.$tabsWidget.tabs('option', 'selected') ).addClass('ui-state-active');
			
			var addGroupHighlight = function ($panel, $group) {
				$panel.find('.'+uiRibbonClasses.group + ', .'+uiRibbonClasses.groupLabel).removeClass(uiRibbonClasses.groupHighlight);
				$group.add($group.find('.'+uiRibbonClasses.groupLabel)).addClass(uiRibbonClasses.groupHighlight);
			};
			var removeGroupHighlight = function ($panel, $group) {
				$panel.find('.'+uiRibbonClasses.group + ', .'+uiRibbonClasses.groupLabel).removeClass(uiRibbonClasses.groupHighlight);
				//$group.add($group.find('.'+uiRibbonClasses.groupLabel)).removeClass(uiRibbonClasses.groupHighlight);
			};
			
            // find and set up groups
            this.$panels.each(function(index) {
                var $panel = $(this);
				var is_contextual = $panel.hasClass(uiRibbonClasses.panelContextual);
                $panel.find('> ul > li')
					.each(function() {
	                    var $group = $(this);
						
						$group
							.addClass(uiRibbonClasses.group)
							.addClass('ui-widget-content ui-corner-all')
							.bind('mouseover.ui-ribbon, mouseenter.ui-ribbon',
								function () { addGroupHighlight($panel, $group); })
							.bind('mouseout.ui-ribbon, mouseleave.ui-ribbon', 
								function () { removeGroupHighlight($panel, $group); });
							
						if (is_contextual)
							$group.addClass('ui-priority-secondary');
							
						$group.children('div:first').addClass(uiRibbonClasses.groupContent).addClass('ui-corner-top ui-helper-clearfix')
							.find('.'+uiRibbonClasses.control)
								.bind('focus.ui-ribbon', function () {
									addGroupHighlight($panel, $group);
								})
								.bind('blur.ui-ribbon', function () {
									//removeGroupHighlight($panel, $group);
								});
						$group.children('h3:first').addClass(uiRibbonClasses.groupLabel).addClass('ui-widget-header ui-corner-bottom ui-state-default');
						
	                    var $dialogbutton = $group.find('.' + uiRibbonClasses.groupDialogButton);

	                    $dialogbutton.bind('click', function() {
	                        self._trigger('group-dialog', self._ui(createGroupEventArgs(self, self.$lis.eq(index).find('a')[0], $panel[0], index, $group[0])));
	                    });
	                });
            });
			
			if ($.quirks && $.isFunction($.quirks.process))
				$.quirks.process(this.element);
				
			
			this.$tabsets = $([]);
            this._tabsetsInfo = {};
            
            // find and set up tabsets
            this.$lis.each(function(index) {
                var $li = $(this);
                var tabset_id = $li.find('a:eq(0)').attr('rel');
                var $tabset;
                if (tabset_id && ($tabset = $('#' + tabset_id)).length > 0) {
                    self.$tabsets = self.$tabsets.add($tabset);
                    
					$tabset
						.addClass(uiRibbonClasses.tabsetContextual);
					
					var $label = $tabset.find('label');
						
					$tabset
						.attr('title', $label.text())
						.html('<i class="left"></i><span></span><i class="right"></i>')
						.find('span').append($label).addClass('ui-widget-header');

                    $li
						.addClass(uiRibbonClasses.tabContextual)
						.removeClass('ui-priority-primary').addClass('ui-priority-secondary');
						
                    self.$panels.eq(index)
						.addClass(uiRibbonClasses.panelContextual)
						.removeClass('ui-priority-primary').addClass('ui-priority-secondary');
                    
                    $tabset.css({ 'visibility': 'hidden', 'display': 'none' });
                }
            });
			
			self._updateAllTabsets();
			$(window)
				.bind('unload', function() { // cleanup to avoid memory leaks in certain versions of IE 6
					self.$tabsWidget = null;
					self.$lis = null;
				})
				.bind('load', function () { // to properly calculate the sizes
					self._updateAllTabsets();
				});
        },
		
		_setTabsetVisibility: function(tabset_id, show, showAllTabs, _fromMethod) {
			var self = this;
			
			var $tabset;
			if (tabset_id && ($tabset = $('#' + tabset_id)).length > 0) {
				if (show) {
					$tabset.css({ 'display': 'block', 'visibility': 'visible' });
				}
				else {
					$tabset.css({ 'visibility': 'hidden', 'display': 'none' });
				}
				
				self._tabsetsInfo[tabset_id].$lis.each(function () {
					var $li = $(this);
					var index = self.$lis.index(this);
					
					if (show) {
						if (showAllTabs !== false)
							if (_fromMethod != 'show') // to avoid recursion
								self.show(index);
					}
					else {
						if (_fromMethod != 'hide') // to avoid recursion
							self.hide(index);
					}
				});
			}
		},
		_recalcAllTabsetsInfo: function() {
			var self = this;
			
			var constOffsetLeft = parseInt(self.element.css('paddingLeft'), 10)
				+ parseInt(self.$tabsList.css('marginLeft'), 10)
				+ parseInt(self.$tabsList.css('borderLeftWidth'), 10)
				+ parseInt(self.$tabsList.css('paddingLeft'), 10);
			
			self._tabsetsInfo = {};
			self.$lis.each(function(index) { // assume tabsets are continuous
				var $li = $(this);
				var tabset_id = $li.find('a:eq(0)').attr('rel');
				if (tabset_id && $('#' + tabset_id).length > 0) {
					var tabset_info = self._tabsetsInfo[tabset_id];
					var li_visible = $li.is(':visible');
					
					if (typeof tabset_info == 'undefined') {
						tabset_info = {};
						tabset_info.width = 0;
						tabset_info.left = Number.MAX_VALUE;
						tabset_info.$lis = $([]);
					}
					tabset_info.width += (li_visible ? $li.outerWidth(true) : 0);
					tabset_info.$lis = tabset_info.$lis.add($li);
					var left = parseInt($li.position().left, 10)
						+ constOffsetLeft;
					if (li_visible && !isNaN(left) && left <= tabset_info.left) {
						tabset_info.left = left;
					}
					
					self._tabsetsInfo[tabset_id] = tabset_info;
				}
			});
		},
		_updateTabset: function(tabset_id) {
			var self = this;
			var $tabset;
			if (tabset_id && ($tabset = $('#' + tabset_id)).length > 0) {
				var tabset_info = self._tabsetsInfo[tabset_id];
				
				var $span = $tabset.find('span');
				var $ileft = $tabset.find('i.left');
				var $iright = $tabset.find('i.right');

				var ileft_width = 1;
				var iright_width = 1;
				var span_width = tabset_info.width
						   - parseInt($span.css('paddingLeft'))
						   - parseInt($span.css('paddingRight'))
						   - ileft_width
						   - iright_width;

				if (span_width > 0) {
					$tabset.css({ width: tabset_info.width+1, left: tabset_info.left-1 });
					$span.css({ width: span_width+1 });
				}   
			}
		},
		_updateAllTabsets: function(_fromMethod) {
			var self = this, o = self.options;
			
			if (o.showTabsets) self.element.removeClass(uiRibbonClasses.tabsetsCollapsed);
			else self.element.addClass(uiRibbonClasses.tabsetsCollapsed);
			
			self._recalcAllTabsetsInfo();
			$.each(self._tabsetsInfo, function(tabset_id, tabset_info) {
				self._updateTabset(tabset_id);
				
				var has_visible = false;
				tabset_info.$lis.each(function () {
					if ($(this).is(':visible')) {
						has_visible = true;
						return false;
					}
				});
				self._setTabsetVisibility(tabset_id, has_visible, false, _fromMethod);
			});
		}
    });

	$.extend($.ui.ribbon, {
		version: '1.7.1',
		//getter: 'length getData',
		defaults: {
			collapsible: false,
			disabled: [],
			showTabsets: true,
			event: 'click',
			cookie: false,
			fx: null, // e.g. { height: 'toggle', opacity: 'toggle', duration: 200 }
			idPrefix: 'ui-ribbon-',
			spinner: 'Loading&#8230;'
		}
	});

})(jQuery);

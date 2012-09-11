(function ($) {
	uiButtonsetClasses = {
		widgetBase: 'ui-buttonset',
		widgetSpec: 'ui-widget ui-widget-content',
		hover: 'ui-buttonset-hover' // not to apply hover style to all child buttons
	};
	
	$.widget('ui.buttonset', {
		_init: function () {
			var self = this,
				options = this.options;
			
			this.element.addClass(uiButtonsetClasses.widgetBase + ' ' + uiButtonsetClasses.widgetSpec);
			
			this.element.find('.ui-button').removeClass('ui-corner-all')
				.filter(':first').addClass('ui-corner-left').end()
				.filter(':last').addClass('ui-corner-right').end()
				.bind('buttonmouseenter.ui-buttonset', function () {
					self.element.addClass(uiButtonsetClasses.hover);
				})
				.bind('buttonmouseleave.ui-buttonset', function () {
					self.element.removeClass(uiButtonsetClasses.hover);
				});
		}
	});
})(jQuery);
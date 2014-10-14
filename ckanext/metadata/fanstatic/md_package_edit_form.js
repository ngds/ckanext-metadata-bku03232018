'use strict';

ckan.module('md-package-edit', function (jQuery, _) {
  return {
    initialize: function () {
      var message
        , form
        , button
        , obj
        , data
        , injection
        ;

      obj = this;

      message = _('There are unsaved modifications to this form').fetch();
      this.el.incompleteFormWarning(message);
      // Internet Explorer 7 fix for forms with <button type="submit">
      if ($('html').hasClass('ie7')) {
        this.el.on('submit', function () {
          form = $(this);
          $('button', form).each(function () {
            button = $(this);
            $('<input type="hidden">')
              .prop('name', button.prop('name'))
              .prop('value', button.val())
              .appendTo(form);
          })
        })
      }
    }
  }
});
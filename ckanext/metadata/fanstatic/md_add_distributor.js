'use strict';

ckan.module('md_add_distributor', function ($, _) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
    },
    _onClick: function () {
      this.sandbox.client.getTemplate('contrib_md_related_agent_form.html',
        this.options, this._onReceiveSnippet);
    },
    _onReceiveSnippet: function (html) {
      var target = $('#collapse-md-distributor-fields .form-fields .md-distributors');
      target.append('<hr>');
      target.append(html);
    }
  }
});
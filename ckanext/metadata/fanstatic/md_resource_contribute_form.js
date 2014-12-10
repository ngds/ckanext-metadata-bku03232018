'use strict';

ckan.module('md-resource-contribute', function (jQuery, _) {
  return {
    initialize: function () {
      var message
        , form
        , button
        , obj
        , data
        , injection
        , res_id
        , res_action
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

      res_id = $('#md-resource-edit [name=id]').val();
      res_action = $('#md-resource-edit').attr('action');

      $('#md-resource-edit').submit(function () {
        data = obj.buildSchema();
        form = $(this);
        injection = $('<input>')
          .attr('type', 'hidden')
          .attr('name', 'md_resource')
          .val(JSON.stringify(data));
        $('#md-resource-edit').append($(injection));

	//geoserver field format validation
        //check if geoserver extension is enabled
        if($('.geo-select-required').length > 0)
        {
            if($('.geo-select-required .select2-chosen').html() == '' || $('.geo-select-required .select2-chosen').length == 0)
            {
                $('#md-resource-edit ol').after("<div class='error-explanation alert alert-error '>"
                + "<p>The form contains invalid entries:</p><ul><li>Format: Missing value</li></ul></div>")
                return false;
            }
        }
      })
    },
    getResource: function (callback) {
      $.ajax({
        url: '/api/3/action/resource_show',
        type: 'POST',
        data: JSON.stringify({'id': id}),
        success: function (res) {
          if (res.success === false) callback('error');
          if (res.success === true) callback(null, res.result);
        },
        error: function (err) {
          callback(err);
        }
      })
    },
    buildSchema: function () {
      var obj
        , doc
        , resource
        , distributors
        , distributor
        , distribs
        , linkObj
        , i
        ;

      function buildRelatedAgent (section) {
        var agent
          , role
          ;

        agent = {};
        agent.relatedAgent = {};
        role = agent.relatedAgent.agentRole = {};
        role.individual = {};

        $(section).find('input').each(function () {
          var name = $(this).attr('name');
          if (name === 'md-person-name') {
            role.individual.personName = $(this).val();
          }
          if (name === 'md-person-position') {
            role.individual.personPosition = $(this).val();
          }
          if (name === 'md-organization-name') {
            role.organizationName = $(this).val();
          }
          if (name === 'md-phone-number') {
            role.phoneNumber = $(this).val();
          }
          if (name === 'md-contact-email') {
            role.contactEmail = $(this).val();
          }
          if (name === 'md-contact-address') {
            role.contactAddress = $(this).val();
          }
        });

        return agent;
      }

      obj = this;

      resource = $('#collapse-md-resource-fields .md-input-form');
      distributors = $('#collapse-md-distributor-fields .md-input-form');

      doc = {};

      distribs = [];
      for (i = 0; i < distributors.length; i++) {
        distributor = distributors[i];
        distribs.push(buildRelatedAgent(distributor));
      }
      doc.distributors = distribs;

      doc.accessLink = {};
      linkObj = doc.accessLink.LinkObject = {};

      resource.find('textarea').each(function () {
        var name = $(this).attr('name');
        if (name === 'description') {
          linkObj.linkDescription = $(this).val();
        }
      });

      resource.find('input').each(function () {
        var name = $(this).attr('name');
        if (name === 'name') {
          linkObj.linkTitle = $(this).val();
        }
      });

      resource.find('select').each(function () {
        var name = $(this).attr('name');
        if (name === 'md-usgin-content-model-layer') {
          doc.usginContentModelLayer = $(this).val();
        }
      });

      return doc;
    }
  }
});

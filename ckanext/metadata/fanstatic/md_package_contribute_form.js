'use strict';

ckan.module('md-package-contribute', function (jQuery, _) {
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

      $('#md-dataset-edit').submit(function () {
        data = obj.buildSchema();
        form = $(this);
        injection = $('<input>')
          .attr('type', 'hidden')
          .attr('name', 'md_package')
          .val(JSON.stringify(data));
        $('#md-dataset-edit').append($(injection));
      })
    },
    getPackage: function (id, callback) {
      $.ajax({
        url: '/api/3/action/package_show',
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
        , basic
        , doc
        , res_desc
        , dateTime
        , citedSourceAgents
        , sourceAgents
        , sourceAgent
        , resourceContact
        , geo
        , geoExt
        , pkgId
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

      basic = $('#collapse-basic-fields .md-input-form');
      citedSourceAgents = $('#collapse-md-author-fields .md-input-form');
      resourceContact = $('#collapse-md-metadata-contact-fields .md-input-form');
      geo = $('#collapse-md-geographic-extent-fields .md-input-form');

      res_desc = {};
      res_desc.citationDates = {};
      res_desc.citationDates.EventDateObject = {};
      dateTime = res_desc.citationDates.EventDateObject = {};

      basic.find('textarea').each(function () {
        var name = $(this).attr('name');
        if (name === 'notes') {
          res_desc.resourceDescription = $(this).val();
        }
      });

      basic.find('input').each(function () {
        var name = $(this).attr('name');
        if (name === 'title') {
          res_desc.resourceTitle = $(this).val();
        }
        if (name === 'publication_date') {
          dateTime.dateTime = $(this).val();
        }
      });

      basic.find('select').each(function () {
        var name = $(this).attr('name');
        if (name === 'md-usgin-content-model') {
          res_desc.usginContentModel = $(this).val();
        }
        if (name === 'md-usgin-content-model-version') {
          res_desc.usginContentModelVersion = $(this).val();
        }
      });

      sourceAgents = [];
      for (i = 0; i < citedSourceAgents.length; i++) {
        sourceAgent = citedSourceAgents[i];
        sourceAgents.push(buildRelatedAgent(sourceAgent));
      }
      res_desc.citedSourceAgents = sourceAgents;

      res_desc.resourceContact = buildRelatedAgent(resourceContact);

      geoExt = {};
      res_desc.geographicExtent = [];
      geo.find('input').each(function () {
        var name
          , north
          , south
          , east
          , west
          ;

        name = $(this).attr('name');
        if (name === 'md-geo-north') {
          geoExt.northBoundLatitude = parseFloat($(this).val());
        }
        if (name === 'md-geo-south') {
          geoExt.southBoundLatitude = parseFloat($(this).val());
        }
        if (name === 'md-geo-east') {
          geoExt.eastBoundLongitude = parseFloat($(this).val());
        }
        if (name === 'md-geo-west') {
          geoExt.westBoundLongitude = parseFloat($(this).val());
        }
      });
      res_desc.geographicExtent.push(geoExt);

      pkgId = $("[name=pkg_name]").val();

      doc = {};

      if (pkgId) {
        obj.getPackage(pkgId, function (err, res) {
          if (err) console.log(err);
          doc.harvestInformation = res.harvestInformation;
          doc.metadataProperties = res.metadataProperties;
          doc.resourceDescription = res_desc;
          return doc;
        })
      } else {
        doc.harvestInformation = {
          "crawlDate": "",
          "harvestURL": "",
          "indexDate": "",
          "originalFileIdentifier": "",
          "originalFormat": "",
          "version": "",
          "sourceInfo": {
            "harvestSourceID": "",
            "harvestSourceName": "",
            "viewID": ""
          }
        };

        doc.metadataProperties = {
          "metadataContact": {
            "relatedAgent": {
              "agentRole": {
                "agentRoleLabel": "",
                "agentRoleURI": "",
                "contactAddress": "",
                "contactEmail": "",
                "organizationName": "",
                "organizationURI": "",
                "phoneNumber": "",
                "individual": {
                  "personName": "",
                  "personPosition": "",
                  "personURI": ""
                }
              }
            }
          }
        };

        doc.resourceDescription = res_desc;
        return doc;
      }
    }
  }
});
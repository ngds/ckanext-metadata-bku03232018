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
        , pkgId
        ;

      obj = this;

      //set custom validation issue #7 metadata
      obj.validateFirstStepBeforeSubmit('#md-dataset-edit');

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

      pkgId = $("[name=pkg_name]").val();
      if (pkgId) {
        obj.getPackage(pkgId, function (err, res) {
          var mdPkg
            , doc
            , i
            ;

          if (err) console.log(err);
          for (i = 0; i < res.extras.length; i++) {
            if (res.extras[i].key === 'md_package') {
              mdPkg = JSON.parse(res.extras[i].value);
            }
          }
          doc = {};
          doc.harvestInformation = mdPkg.harvestInformation;
          doc.metadataProperties = mdPkg.metadataProperties;

          obj.originalDoc = doc;
        });
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
    buildSchema: function (callback) {
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
        , doc
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

      res_desc.resourceContact = [buildRelatedAgent(resourceContact)];

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

      doc = {};
      if (obj.originalDoc) {
          doc.harvestInformation = obj.originalDoc.harvestInformation;
          doc.metadataProperties = obj.originalDoc.metadataProperties;
          doc.resourceDescription = res_desc;
          return doc;
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
    },
    validateFirstStepBeforeSubmit: function(formID) {
        if($(formID).length > 0)
        {
            $(formID).on('submit', function(e) {
                if($('#usgin-field-publication-date').val() != '')
                {
		    if($('.md-cited-source-agent #md-person-name').val() == '' || $('.md-resource-contacts #md-person-name').val() == '')
                    {
                        $('.md-cited-source-agent #md-person-name, .md-resource-contacts #md-person-name').css({'border-color': 'red'});

                        if($('.md-cited-source-agent #md-person-name').val() == '')
                            $('a[href="#collapse-md-author-fields"]').trigger('click');

                        if($('.md-resource-contacts #md-person-name').val() == '')
                            $('a[href="#collapse-md-metadata-contact-fields"]').trigger('click');

                        e.preventDefault();
                        return false;
                    }
                    else
                    {
                        $('.md-cited-source-agent #md-person-name, .md-resource-contacts #md-person-name').css({'border-color': 'none'});
                    }
                }

                return true;
            });
        }
    }
  }
});

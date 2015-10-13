'use strict';

(function ($) {
  var pkg_id;

  pkg_id = $("[name=pkg_name]").val();

  function getPackage (id, callback) {
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
  }

  function makeRelatedAgent (data) {
    var html
      , name
      , position
      , orgName
      , orgURI
      , phone
      , email
      , address
      ;

    name = data.relatedAgent.agentRole.individual.personName;
    position = data.relatedAgent.agentRole.individual.personPosition;
    orgName = data.relatedAgent.agentRole.organizationName;
    orgURI = '';
    phone = data.relatedAgent.agentRole.phoneNumber;
    email = data.relatedAgent.agentRole.contactEmail;
    address = data.relatedAgent.agentRole.contactAddress;

    html = '<div class="md-input-form md-related-agent">';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-person-name">Name</label>';
    html += '<div class="controls">';
    html += '<input id="md-person-name" type="text" name="md-person-name" value="' + name + '">';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-person-position">Position</label>';
    html += '<div class="controls">';
    html += '<input id="md-person-position" type="text" name="md-person-position" value="' + position + '">';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-organization-name">Organization Name</label>';
    html += '<div class="controls">';
    html += '<input id="md-organization-name" type="text" name="md-organization-name" value="' + orgName + '">';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-organization-uri">Organization URI</label>';
    html += '<div class="controls">';
    html += '<input id="md-organization-uri" type="text" name="md-organization-uri" value="' + orgURI + '">';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-phone-number">Phone Number</label>';
    html += '<div class="controls">';
    html += '<input id="md-phone-number" type="text" name="md-phone-number" value="' + phone + '">';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-contact-email">Email</label>';
    html += '<div class="controls">';
    html += '<input id="md-contact-email" type="text" name="md-contact-email" value="' + email + '">';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-contact-address">Address</label>';
    html += '<div class="controls">';
    html += '<input id="md-contact-address" type="text" name="md-contact-address" value="' + address + '">';
    html += '</div></div>';

    html += '</div>';

    return html;
  }

  function makeBoundingBox (data) {
    var html
      , north
      , south
      , east
      , west
      ;

    north = data.northBoundLatitude;
    south = data.southBoundLatitude;
    east = data.eastBoundLongitude;
    west = data.westBoundLongitude;

    html = '<div class="md-input-form md-geographic-extent">';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-geo-north">North Bound</label>';
    html += '<div class="controls">';
    html += '<input id="md-geo-north" type="text" name="md-geo-north" value=' + north + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-geo-south">South Bound</label>';
    html += '<div class="controls">';
    html += '<input id="md-geo-south" type="text" name="md-geo-south" value=' + south + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-geo-east">East Bound</label>';
    html += '<div class="controls">';
    html += '<input id="md-geo-east" type="text" name="md-geo-east" value=' + east + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-geo-west">West Bound</label>';
    html += '<div class="controls">';
    html += '<input id="md-geo-west" type="text" name="md-geo-west" value=' + west + '>';
    html += '</div></div>';

    html += '</div>';

    return html;
  }

  getPackage(pkg_id, function (err, res) {
    var md_pkg
      , md_geo
      , bbox
      , extent
      , md_authors
      , authors
      , author
      , md_contacts
      , contacts
      , contact
      , i
      , j
      , k
      ;

    if (err) console.log(err);

    for (i = 0; i < res.extras.length; i++) {
      if (res.extras[i].key === 'md_package') {
        md_pkg = JSON.parse(res.extras[i].value);
      }
    }

    md_authors = $('#collapse-md-author-fields .md-cited-source-agent');
    md_authors.empty();
    authors = md_pkg.resourceDescription.citedSourceAgents;
    for (j = 0; j < authors.length; j++) {
      author = makeRelatedAgent(authors[j]);
      md_authors.append(author);
    }

    $('#select-usgin .contrib-tab-pane').addClass('active');

    //Check if usgin structure is used
    if(md_pkg.resourceDescription.usginContentModel != "" && md_pkg.resourceDescription.usginContentModelLayer && md_pkg.resourceDescription.usginContentModelVersion != "")
    {
	//load usgin structure html then select dataset usgin values (content model, version and layer)
        setTimeout(function(){
		$('#select-usgin #toggle-structured-tab').trigger('click');

		setTimeout(function(){
		    $('#usgin-content-model option[value="' + md_pkg.resourceDescription.usginContentModel +'"]').prop("selected", true).change();

		    $('#usgin-content-model-version option[value="' + md_pkg.resourceDescription.usginContentModelVersion +'"]').prop("selected", true).change();

		    $('#usgin-content-model-layer option[value="' + md_pkg.resourceDescription.usginContentModelLayer +'"]').prop("selected", true).change();

			$('#usgin-field-resource_id').val(md_pkg.harvestInformation.originalFileIdentifier);

		}, 100);
	    }, 500);
    }
    else
    {
    	$('#select-usgin h3').remove();
    	$('#select-usgin .btn-group').remove();
    }

    md_geo = $('#collapse-md-geographic-extent-fields .md-geographic-extent');
    md_geo.empty();
    bbox = md_pkg.resourceDescription.geographicExtent[0];
    extent = makeBoundingBox(bbox);
    md_geo.append(extent);

    md_contacts = $('#collapse-md-metadata-contact-fields .md-resource-contacts');
    md_contacts.empty();
    contacts = md_pkg.resourceDescription.resourceContact;
    for (k = 0; k < contacts.length; k++) {
      contact = makeRelatedAgent(contacts[k]);
      md_contacts.append(contact);
    }
  });

}(jQuery));

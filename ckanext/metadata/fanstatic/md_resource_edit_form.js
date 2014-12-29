'use strict';

(function ($) {
  var res_id
    , res_action
    , regex
    , pkg_id
    ;

  res_id = $('#md-resource-edit [name=id]').val();
  res_action = $('#md-resource-edit').attr('action');

  function getResource (id, callback) {
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

  getResource(res_id, function (err, res) {
    var md_res
      , md_distributors
      , distributors
      , distributor
      , i
      ;

    if (err) console.log(err);
    md_res = JSON.parse(res.md_resource);

    md_distributors = $('#collapse-md-distributor-fields .md-distributors');
    md_distributors.empty();
    distributors = md_res.distributors;
    for (i = 0; i < distributors.length; i++) {
      distributor = makeRelatedAgent(distributors[i]);
      md_distributors.append(distributor);
    }

  });

})(jQuery);

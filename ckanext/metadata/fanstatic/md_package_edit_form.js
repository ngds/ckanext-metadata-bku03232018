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

  function makeBasicForm (data) {
    var html;

    html = '<div class="md-input-form">';
    html += 
    html += '</div>';
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
    html += '<input id="md-person-name" type="text" name="md-person-name" value=' + name + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-person-position">Position</label>';
    html += '<div class="controls">';
    html += '<input id="md-person-position" type="text" name="md-person-position" value=' + position + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-organization-name">Organization Name</label>';
    html += '<div class="controls">';
    html += '<input id="md-organization-name" type="text" name="md-organization-name" value=' + orgName + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-organization-uri">Organization URI</label>';
    html += '<div class="controls">';
    html += '<input id="md-organization-uri" type="text" name="md-organization-uri" value=' + orgURI + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-phone-number">Phone Number</label>';
    html += '<div class="controls">';
    html += '<input id="md-phone-number" type="text" name="md-phone-number" value=' + phone + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-contact-email">Email</label>';
    html += '<div class="controls">';
    html += '<input id="md-contact-email" type="text" name="md-contact-email" value=' + email + '>';
    html += '</div></div>';

    html += '<div class="control-group control-medium">';
    html += '<label class="control-label" for="md-contact-address">Address</label>';
    html += '<div class="controls">';
    html += '<input id="md-contact-address" type="text" name="md-contact-address" value=' + address + '>';
    html += '</div></div>';

    html += '</div>';

    return html;
  }

  getPackage(pkg_id, function (err, res) {
    var md_pkg
      , md_authors
      , authors
      , author
      , i
      , j
      ;

    if (err) console.log(err);

    for (i = 0; i < res.extras.length; i++) {
      if (res.extras[i].key === 'md_package') {
        md_pkg = JSON.parse(res.extras[i].value);
      }
    }

    md_authors = $("#collapse-md-author-fields .md-cited-source-agent");
    md_authors.empty();
    authors = md_pkg.resourceDescription.citedSourceAgents;
    for (j = 0; j < authors.length; j++) {
      author = makeRelatedAgent(authors[j]);
      md_authors.append(author);
    }

  });

}(jQuery));
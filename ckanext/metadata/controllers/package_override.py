import cgi
import paste.fileapp
import mimetypes
import json
import os
from ckanext.metadata.common import helpers as h
from ckanext.metadata.common import plugins as p
from ckanext.metadata.common import request, c, g, _, response
from ckanext.metadata.common import dictization_functions
from ckanext.metadata.common import base, logic, model

from ckan.controllers.package import PackageController

import ckan.lib.navl.dictization_functions as dict_fns

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

class PackageContributeOverride(p.SingletonPlugin, PackageController):

    def new_resource(self, id, data=None, errors=None, error_summary=None):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        if request.method == 'POST' and not data:
            save_action = request.params.get('save')
            data = data or clean_dict(dictization_functions.unflatten(
                tuplize_dict(parse_params(request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']
            resource_id = data['id']
            del data['id']

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            # see if we have any data that we are trying to save
            data_provided = False
            for key, value in data.iteritems():
                if ((value or isinstance(value, cgi.FieldStorage))
                    and key != 'resource_type'):
                    data_provided = True
                    break

            if not data_provided and save_action != "go-dataset-complete":
                if save_action == 'go-dataset':
                    # go to final stage of adddataset
                    redirect(h.url_for(controller='package',
                                       action='edit', id=id))
                # see if we have added any resources
                try:
                    data_dict = get_action('package_show')(context, {'id': id})
                except NotAuthorized:
                    abort(401, _('Unauthorized to update dataset'))
                except NotFound:
                    abort(404,
                      _('The dataset {id} could not be found.').format(id=id))
                if not len(data_dict['resources']):
                    # no data so keep on page
                    msg = _('You must add at least one data resource')
                    # On new templates do not use flash message
                    if g.legacy_templates:
                        h.flash_error(msg)
                        redirect(h.url_for(controller='package',
                                           action='new_resource', id=id))
                    else:
                        errors = {}
                        error_summary = {_('Error'): msg}
                        return self.new_resource(id, data, errors, error_summary)
                # we have a resource so let them add metadata
                redirect(h.url_for(controller='package',
                                   action='new_metadata', id=id))

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new_resource(id, data, errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to create a resource'))
            except NotFound:
                abort(404,
                    _('The dataset {id} could not be found.').format(id=id))

            if save_action == 'go-metadata' or save_action == 'go-dataset-complete':
                ## here's where we're doing the route override
                data_dict = get_action('package_show')(context, {'id': id})

		######## 	USGINModels File Validation 	#######
		## Before activate dataset, validate files of all resources for dataset has usgin structure ##

		isUsginUsed = p.toolkit.get_action('is_usgin_structure_used')(context, data_dict)

		#if dataset doesn't use usgin structure then no need for usginModel file validation
		if isUsginUsed is True:

                    resources = data_dict.get('resources', [])
		    messages = []
		    validationProcess = True

                    for resource in resources:
                        result = p.toolkit.get_action('usginmodels_validate_file') (context, {'resource_id': resource.get('id', None),
                                                                                'package_id': id,
                                                                                'resource_name': resource.get('name', None)})

		        valid = result.get('valid', None)
			message = result.get('message', None)
		        if valid is False or ( valid is True and message ):
			    #validation process has failed
			    validationProcess = False
			    try:
			        get_action('resource_delete')(context, {'id': resource.get('id', None)})
			    except:
			        #deleting non existing resource
			        continue

			    msg = message

			    # in case we have an array of messages
			    if isinstance(message, (list, tuple)):
				msg = "<br />".join(message)

			        if valid is True:
				    msg = "<p>The file could be valid with the changes below:</p>"+msg

				    link = p.toolkit.url_for('custom_resource_download', id=id, resource_id=result.get('resourceId', None))
				    msg = msg+"<h6>Download</h6><p>Click the button below to download a copy of your data which has applied to it the changes indicated in the Warning and Notice messages.<br/>"
				    msg = msg+"<a href='"+link+"' style='color: white !important' class='btn btn-primary btn-small'>Download</a></p>"

			    if not msg:
			        msg = _("An error occurred while saving the data, please try again.")

			    messages.append("Resource [%s]: %s" % (result.get('resourceName', ''), _(msg)))

		    #if at least one resource file validation is failed, redirect user to new_resource page with error message
		    if not validationProcess:
		        h.flash_error("<br />".join(messages), True)
		        redirect(h.url_for(controller='package',
                                           action='new_resource', id=id))

		### END USGINModels File Validation ###

	    if save_action == 'go-metadata':
		data_dict = get_action('package_show')(context, {'id': id})
                get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
                """
                # this is the original route
                # go to final stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='new_metadata', id=id))
                """
            elif save_action == 'go-dataset':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            else:
                # add more resources
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        vars['pkg_name'] = id
        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('The dataset {id} could not be found.').format(id=id))
        try:
            check_access('resource_create', context, pkg_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a resource for this package'))

        # required for nav menu
        vars['pkg_dict'] = pkg_dict
        template = 'package/new_resource_not_draft.html'
        if pkg_dict['state'] == 'draft':
            vars['stage'] = ['complete', 'active']
            template = 'package/new_resource.html'
        elif pkg_dict['state'] == 'draft-complete':
            vars['stage'] = ['complete', 'active', 'complete']
            template = 'package/new_resource.html'
        return render(template, extra_vars=vars)

    def resource_edit(self, id, resource_id, data=None, errors=None,
                      error_summary=None):
        if request.method == 'POST' and not data:
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']

            context = {'model': model, 'session': model.Session,
                       'api_version': 3, 'for_edit': True,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.resource_edit(id, resource_id, data,
                                          errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to edit this resource'))
            
	    ########        USGINModels File Validation     #######
            pkg_dict = get_action('package_show')(context, {'id': id})

            isUsginUsed = p.toolkit.get_action('is_usgin_structure_used')(context, pkg_dict)

            #if dataset doesn't use usgin structure then no need for usginModel file validation
            if isUsginUsed is True:

                messages = []
                validationProcess = True

                result = p.toolkit.get_action('usginmodels_validate_file') (context, {'resource_id': resource_id,
                                                                        'package_id': id,
                                                                        'resource_name': data.get('name', None)})

                valid = result.get('valid', None)
		message = result.get('message', None)
                if valid is False or ( valid is True and message ):
                    #validation process has failed
                    validationProcess = False
                    try:
                        get_action('resource_delete')(context, {'id': resource_id})
                    except:
                        #deleting non existing resource
                        pass

		    msg = message

		    # in case we have an array of messages
		    if isinstance(message, (list, tuple)):
			msg = "<br />".join(message)

			if valid is True:
			    msg = "<p>The file could be valid with the changes below:</p>"+msg

			    link = p.toolkit.url_for('custom_resource_download', id=id, resource_id=result.get('resourceId', None))
                            msg = msg+"<h6>Download</h6><p>Click the button below to download a copy of your data which has applied to it the changes indicated in the Warning and Notice messages.<br />"
                            msg = msg+"<a href='"+link+"' style='color: white !important' class='btn btn-primary btn-small'>Download</a></p>"

                    if not msg:
                        msg = _("An error occurred while saving the data, please try again.")

                    h.flash_error(msg, True)

                #if the resource file updated not valid then we delete this resource and redirect user to add new resource
                if not validationProcess:
                    redirect(h.url_for(controller='package',
                                       action='new_resource', id=id))

            ### END USGINModels File Validation ###

	    redirect(h.url_for(controller='package', action='resource_read',
                               id=id, resource_id=resource_id))

        context = {'model': model, 'session': model.Session,
                   'api_version': 3, 'for_edit': True,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        pkg_dict = get_action('package_show')(context, {'id': id})
        if pkg_dict['state'].startswith('draft'):
            # dataset has not yet been fully created
            resource_dict = get_action('resource_show')(context, {'id': resource_id})
            fields = ['url', 'resource_type', 'format', 'name', 'description', 'id']
            data = {}
            for field in fields:
                data[field] = resource_dict[field]
            return self.new_resource(id, data=data)
        # resource is fully created
        try:
            resource_dict = get_action('resource_show')(context, {'id': resource_id})
        except NotFound:
            abort(404, _('Resource not found'))
        c.pkg_dict = pkg_dict
        c.resource = resource_dict
        # set the form action
        c.form_action = h.url_for(controller='package',
                                  action='resource_edit',
                                  resource_id=resource_id,
                                  id=id)
        if not data:
            data = resource_dict

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        return render('package/resource_edit.html', extra_vars=vars)

    #Custom resource download corrected data, resource_id only for generating the path to the file
    def resource_download_corrected_data(self, id, resource_id):
        """
        Provides a direct download by either redirecting the user to the url stored
         or downloading an uploaded file directly.
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

	result = p.toolkit.get_action('get_file_path')(context, {'resourceId': resource_id, 'suffix': '_CorrectedData'})
	filePath = result.get('path', None)

        if os.path.isfile(filePath):
            #upload = uploader.ResourceUpload(rsc)
            #filepath = upload.get_path(rsc['id'])
            fileapp = paste.fileapp.FileApp(filePath)

            try:
               status, headers, app_iter = request.call_application(fileapp)
            except OSError:
               abort(404, _('Resource data not found'))
            response.headers.update(dict(headers))
            #content_type, content_enc = mimetypes.guess_type(rsc.get('url',''))
            #if content_type:
	    #It's CSV, because this method can be only access when a usgin model doesn't validate a CSV File
            response.headers['Content-Type'] = 'text/csv'
            response.status = status
            return app_iter

        abort(404, _('No download is available'))

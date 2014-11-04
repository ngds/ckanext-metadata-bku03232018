import json
import cgi
import logic.action as action
import logic.converters as converters
import logic.validators as validators
import helpers as h
from ckanext.metadata.common import base, logic, model
from ckanext.metadata.common import plugins as p
from ckanext.metadata.common import app_globals
from ckanext.metadata.common import request, c, g, _
from ckanext.metadata.common import dictization_functions

from ckan.controllers.package import PackageController

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

try:
    from collections import OrderedDict
except ImportError:
    from sqlalchemy.util import OrderedDict

class MetadataPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):

    p.implements(p.IConfigurer)
    p.implements(p.IActions)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IDatasetForm)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    # IConfigurer
    def update_config(self, config):
        templates = 'templates'
        public = 'public'

        p.toolkit.add_template_directory(config, templates)
        p.toolkit.add_public_directory(config, public)
        p.toolkit.add_resource('fanstatic', 'metadata')

        content_models = action.http_get_content_models()
        app_globals.mappings['usgin.content_models'] = 'usgin.content_models'
        data = {
            'usgin.content_models': config.get('usgin.content_models', content_models)
        }
        config.update(data)

    # IRoutes
    def before_map(self, map):
        controller = 'ckanext.metadata.controllers.view:ViewController'
        map.connect('metadata_iso_19139', '/metadata/iso-19139/{id}.xml',
                    controller=controller, action='show_iso_19139')
        return map

    # IActions
    def get_actions(self):
        return {
            'iso_19139': action.iso_19139,
            'get_content_models': action.get_content_models,
            'get_content_models_short': action.get_content_models_short,
        }

    # IDatasetForm
    def _modify_package_schema(self, schema):
        schema.update({
            'md_package': [p.toolkit.get_validator('ignore_missing'),
                             converters.convert_to_md_package_extras]
        })
        schema['resources'].update({
            'md_resource': [p.toolkit.get_validator('ignore_missing'),
                              converters.convert_to_md_resource_extras],
            'url': [validators.is_usgin_valid_data]
        })
        return schema

    def create_package_schema(self):
        schema = super(MetadataPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(MetadataPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(MetadataPlugin, self).show_package_schema()
        schema['tags']['__extras'].append(p.toolkit.get_converter('free_tags_only'))
        schema.update({
            'md_package': [p.toolkit.get_validator('ignore_missing'),
                             p.toolkit.get_converter('convert_from_extras')]
        })

        schema['resources'].update({
            'md_resource': [p.toolkit.get_validator('ignore_missing'),
                              p.toolkit.get_converter('convert_from_extras')],
        })

        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # packages not handled by any other IDatasetForm plugin
        return True

    def package_types(self):
        return []

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'md_get_vanilla_ckan_version': h.md_get_vanilla_ckan_version,
            'md_package_extras_processor': h.md_package_extras_processor,
            'md_resource_extras_processer': h.md_resource_extras_processer,
            'usgin_check_package_for_content_model': h.usgin_check_package_for_content_model,
        }

    # IPackageController
    def before_index(self, pkg_dict):
        if pkg_dict.get('md_package'):
            md_pkg = json.loads(pkg_dict.get('md_package'))

            # Authors
            md_agents = md_pkg.get('resourceDescription').get('citedSourceAgents')
            author_names = []
            organization_names = []
            for agent in md_agents:
                name = agent.get('relatedAgent').get('agentRole') \
                    .get('individual').get('personName', None)
                organization = agent.get('relatedAgent').get('agentRole') \
                    .get('organizationName', None)

                if name:
                    author_names.append(name)
                if organization:
                    organization_names.append(organization)

            pkg_dict['md_author_names'] = author_names
            pkg_dict['md_organization_names'] = organization_names

        if pkg_dict.get('tags'):
            content_models = []
            for tag in pkg_dict.get('tags'):
                tag = str(tag)
                if tag.startswith('usgincm:'):
                    content_models.append(tag.rsplit(":", 1)[1].title())
            pkg_dict['md_content_models'] = content_models

        return pkg_dict

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
            if save_action == 'go-metadata':
                ## here's where we're doing the route override
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

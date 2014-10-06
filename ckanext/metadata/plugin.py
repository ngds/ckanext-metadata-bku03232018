import logic.action as action
import logic.converters as converters
import helpers as h
from common import plugins as p


class MetadataPlugin(p.SingletonPlugin, p.toolkit.DefaultDatasetForm):

    p.implements(p.IConfigurer)
    p.implements(p.IActions)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IDatasetForm)
    p.implements(p.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config):
        templates = 'templates'
        public = 'public'

        p.toolkit.add_template_directory(config, templates)
        p.toolkit.add_public_directory(config, public)
        p.toolkit.add_resource('fanstatic', 'metadata')

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
        }

    # IDatasetForm
    def _modify_package_schema(self, schema):
        schema.update({
            'md_package': [p.toolkit.get_validator('ignore_missing'),
                             converters.convert_to_md_package_extras]
        })

        schema['resources'].update({
            'md_resource': [p.toolkit.get_validator('ignore_missing'),
                              converters.convert_to_md_package_extras],
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
            'protocol_codes': h.protocol_codes,
            'md_package_extras_processor': h.md_package_extras_processor,
            'md_resource_extras_processer': h.md_resource_extras_processer,
        }
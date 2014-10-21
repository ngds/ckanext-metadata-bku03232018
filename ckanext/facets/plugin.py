import helpers as h
from ckanext.facets.common import plugins as p
from ckanext.facets.common import app_globals
from ckanext.facets.common import config

try:
    from collections import OrderedDict
except ImportError:
    from sqlalchemy.util import OrderedDict

class FacetsPlugin(p.SingletonPlugin):

    p.implements(p.IConfigurer)
    p.implements(p.IFacets, inherit=True)

    # IConfigurer
    def update_config(self, config):
        h.load_md_facets(app_globals, config)


    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        if package_type == 'harvest':
            return OrderedDict([('frequency', 'Frequency'), ('source_type', 'Type')])
        md_facets = h.load_md_facets(app_globals, config)
        if md_facets:
            facets_dict = md_facets
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        if package_type == 'harvest':
            return OrderedDict([('frequency', 'Frequency'), ('source_type', 'Type')])
        md_facets = h.load_md_facets(app_globals, config)
        if md_facets:
            facets_dict = md_facets
        return facets_dict
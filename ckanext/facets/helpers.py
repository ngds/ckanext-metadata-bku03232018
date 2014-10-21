import json
import logging

try:
    from collections import OrderedDict
except ImportError:
    from sqlalchemy.util import OrderedDict

log = logging.getLogger(__name__)

def load_md_facets(app_globals, config):
    try:
        md_facets = app_globals.mappings.get('md_facets', None)
        md_facet_config = config.get('md.facets_config', None)
        if md_facets:
            log.info('Metadata plugin custom facets already loaded')
        else:
            md_facets = read_facets_config(md_facet_config)
            app_globals.mappings['md.facets'] = md_facets
            log.info('Metadata plugin custom facets loaded')
        return md_facets
    except:
        log.info('Metadata plugin custom facets could not be loaded')

def read_facets_config(config_path):

    with open(config_path, 'r') as json_file:
        json_data = json.load(json_file)
        facets = []
        for facet in json_data:
            md_field = facet.get('metadatafield', None)
            md_facet = facet.get('facet', None)
            if md_field and md_facet:
                facet_tuple = (md_field, md_facet)
                facets.append(facet_tuple)

    if facets:
        return OrderedDict(facets)
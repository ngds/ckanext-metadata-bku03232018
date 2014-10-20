import json
from ckan import model
from common import plugins as p
from common import logic
from common import app_globals
from logic import action

def create_protocol_codes():
    user = p.toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'protocol_codes'}
        p.toolkit.get_action('vocabulary_show')(context, data)
    except p.toolkit.ObjectNotFound:
        data = {'name': 'protocol_codes'}
        vocab = p.toolkit.get_action('vocabulary_create')(context, data)
        for tag in ('OGC:WMS', 'OGC:WFS', 'OGC:WCS', 'OGC:CSW', 'OGC:SOS',
                    'OPeNDAP', 'ESRI', 'other'):
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            p.toolkit.get_action('tag_create')(context, data)

def protocol_codes():
    create_protocol_codes()
    try:
        tag_list = p.toolkit.get_action('tag_list')
        protocol_codes = tag_list(data_dict={'vocabulary_id': 'protocol_codes'})
        return protocol_codes
    except p.toolkit.ObjectNotFound:
        return None

def make_author(data):
    individual = data.get('individual', None)
    name = None
    position = None

    if individual:
        name = individual.get('personName', None)
        position = individual.get('personPosition', None)

    return {
        'Name': name,
        'Position': position,
        'Organization': data.get('organizationName', None),
        'Address': data.get('contactAddress', None),
        'Phone': data.get('phoneNumber', None),
        'Email': data.get('contactEmail', None),
    }

def md_package_extras_processor(extras):

    def check_harvest_info(data):
        original_id = data.get('originalFileIdentifier', None)
        if original_id:
            return True
        else:
            return False

    def check_author(data):
        name = data.get('Name', None)
        phone = data.get('Phone', None)
        org = data.get('Organization', None)
        address = data.get('Address', None)
        position = data.get('Position', None)
        email = data.get('Email', None)

        items = [name, phone, org, address, position, email]
        if all(value is None for value in items):
            return False
        else:
            return True

    def check_geo_ext(data):
        north = data.get('northBoundLatitude', None)
        south = data.get('southBoundLatitude', None)
        east = data.get('eastBoundLongitude', None)
        west = data.get('westBoundLongitude', None)

        items = [north, south, east, west]
        if all(value is None for value in items):
            return False
        else:
            return True

    try:
        pkg = [extra for extra in extras if extra.get('key') == 'md_package'][0]
    except:
        pkg = None

    if pkg:
        md = json.loads(pkg.get('value'))

        details_obj = {}

        # harvest information
        harvest_info = md.get('harvestInformation', None)
        has_harvest = check_harvest_info(harvest_info)
        if has_harvest:
            details_obj['harvest'] = harvest_info
        else:
            details_obj['harvest'] = None

        # metadata properties
        md_props_author = md.get('metadataProperties').get('metadataContact') \
            .get('relatedAgent').get('agentRole', None)
        has_md_props = check_author(md_props_author)
        if has_md_props:
            details_obj['props'] = {'author': md_props_author}
        else:
            details_obj['props'] = None

        # citation date
        cite_date = md.get('resourceDescription').get('citationDates') \
            .get('EventDateObject').get('dateTime', None)
        if cite_date:
            details_obj['date'] = cite_date
        else:
            details_obj['date'] = None

        # related agents
        authors = []
        for agent in md['resourceDescription']['citedSourceAgents']:
            agent = agent['relatedAgent']['agentRole']
            author = make_author(agent)
            has_author = check_author(author)
            if has_author:
                authors.append(author)
        if len(authors) > 0:
            details_obj['authors'] = authors
        else:
            details_obj['authors'] = None

        # resource contacts
        contacts = []
        for agent in md['resourceDescription']['resourceContact']:
            agent = agent['relatedAgent']['agentRole']
            contact = make_author(agent)
            has_contact = check_author(contact)
            if has_contact:
                contacts.append(contact)
        if len(contacts):
            details_obj['contacts'] = contacts
        else:
            details_obj['contacts'] = None

        # geographic extent
        geo_ext = md.get('resourceDescription').get('geographicExtent', None)
        if geo_ext[0]:
            has_geo_ext = check_geo_ext(geo_ext[0])
            if has_geo_ext:
                details_obj['geography'] = geo_ext[0]
            else:
                details_obj['geography'] = None
        else:
            details_obj['geography'] = None

        if all(value is None for value in details_obj.itervalues()):
            return None
        else:
            return details_obj

def md_resource_extras_processer(res):
    md_res = res.get('md_resource', None)
    if md_res:
        md = json.loads(md_res)

        res_obj = md.get('accessLink').get('LinkObject', None)
        res_dist = md.get('distributors', None)

        distributors = []
        for agent in res_dist:
            agent = agent['relatedAgent'].get('agentRole', None)
            distributor = make_author(agent)
            distributors.append(distributor)

        return {
            'distributors': distributors,
            'resource': res_obj,
        }

def usgin_check_package_for_content_model(pkg_id):
    context= {'model': model, 'user': ''}
    search = logic.action.get.package_show(context, {'id': pkg_id})
    try:
        extras = search.get('extras')
        usgin = [i for i in extras if i['key'] == 'md_package']
        usgin = json.loads(usgin[0]['value'])
        cm = {'content_model_uri': usgin['usginContentModel'],
              'content_model_version': usgin['usginContentModelVersion']}
        try:
            models = app_globals.config.get('ngds.content_models')
        except:
            models = action.http_get_content_models()
        c_model = [m['versions'] for m in models if m['uri'] == \
                   cm['content_model_uri']][0]
        version = [m for m in c_model if m['uri'] == \
                   cm['content_model_version']]
        return {'success': True, 'data': version}
    except:
        return {'success': False, 'data': ''}

################################################################################

from ckan.lib.base import g
from ckan.plugins import toolkit
from pylons import config
import logging

try:
    from collections import OrderedDict
except ImportError:
    from sqlalchemy.util import OrderedDict

log = logging.getLogger(__name__)

def load_ngds_facets():

    loaded_facets = None
    facets_dict = None

    try:
        if g.loaded_facets:
            return g.loaded_facets
    except AttributeError:
        log.info("facets are yet to be loaded from the config.")


    # Read the facet config file path from application config file (developement.ini)
    facets_config_path = config.get('ngds.facets_config')

    if facets_config_path:
        loaded_facets = read_facets_json(facets_config_path=facets_config_path)

    # If facets are loaded and available then set them in global context and return.
    if loaded_facets:
        g.loaded_facets = loaded_facets
        facets_dict = loaded_facets

    return facets_dict


def read_facets_json(facets_config_path=None):

    with open(facets_config_path, 'r') as json_file:
        import json
        from pprint import pprint

        json_data = json.load(json_file)

        #Dict structure of json config file is placed on global context for future use.
        g.facet_json_data = json_data

        facets_list = []
        #Pass each facet to read_facet method to find the list of fields.
        for facet in json_data:
            facets_list = read_facet(facet, facets_list)

    if facets_list:
        return OrderedDict(facets_list)
    else:
        return None


def read_facet(facet_struc, facet_list):

    if facet_struc.get("metadatafield"):
        facet_list.append(
            (facet_struc['metadatafield'], toolkit._(facet_struc.get("facet") or facet_struc.get("display_name"))))

    #If subfacet exists then iterate through entire structure to find the remaining facets.
    if facet_struc.get("subfacet"):
        for subfacet in facet_struc.get("subfacet"):
            facet_list = read_facet(subfacet, facet_list)

    return facet_list

def get_ngdsfacets():

    facet_config = g.facet_json_data

    facets = []
    for facet_group in facet_config:
        facet_dict = {}
        facets.append(construct_facet(facet_group, facet_dict=facet_dict, facet_level=1))

    return facets

def construct_facet(facet_group, facet_dict={}, metadatafield=None, facet_level=1, facet_values=None):
    """
    This method constructs the facet results for each Facet structure (from json file)

        **Parameters:**
        facet_group - Facet Structure to be filled based on results.
        facet_dict - newly constrcuted facets dict which needs to be appended with new values.
        metadatafield - Metadata field of the facet.
        facet_level - 1 - Top level facet 2 - Other sub level facets.
        facet_values - Values of the facets returned from search.


        **Results:**
        :returns: Constructed faceted dict from the input facet structure and the results.
        :rtype: Dict
    """

    #If metadatafield exists, then get the faceted values from the search results.
    if facet_group.get("metadatafield"):
        metadatafield = facet_group['metadatafield']
        facet_dict['facet_field'] = metadatafield
        facet_values = h.get_facet_items_dict(metadatafield)

    facet_type = facet_group.get("type")

    facet_dict['type'] = facet_type


    # Display type of the field is determined here. If the facet level is 1 (i.e. called from get_ngdsfacets()) then it shld be top level title.
    #Otherwise it will be sub-title. In some cases, top level facet itself will be of type dynamic_keywords. Those types shld be displayed as titles.
    if facet_type == "title" or (facet_type == "dynamic_keywords" and not facet_group.get("subfacet")):
        if facet_level == 1:
            display_type = "title"
        else:
            display_type = "subtitle"
    else:
        display_type = "facet"

    #If the displaye_name exits then display that otherwise display facet itself.
    facet_dict['display_name'] = facet_group.get('display_name') or facet_group.get('facet')
    facet_dict['display_type'] = display_type

    #if the facet_type is dynamic_keywords then there won't be any sub-facets. Display those dynamic facet values .
    if facet_group.get("type") == 'dynamic_keywords':
        facet_dict['fvalues'] = facet_values

    #If the facet_type is "keyword" then it has to be compared with the results for the count. If matches then remove that from the results so that it won't be in the others list.
    #If the facet is not matching with any results, then create a dummy facet with count 0.
    if facet_group.get("type") == 'keyword':
        found = False
        for ret_facet in facet_values:
            #print "ret_facet['name']: ",ret_facet['name']
            fc_group = (facet_group.get('facet').encode('ascii', 'ignore')).strip().lower()
            fc_name = (ret_facet['name'].encode('ascii', 'ignore')).strip().lower()
            ret_facet['name'] = fc_name
            ret_facet['group'] = fc_group
            if fc_name == fc_group:
                ret_facet['display_name'] = facet_group.get('display_name') or facet_group.get('facet')
                facet_dict['fvalues'] = [ret_facet]
                found = True
                facet_values.remove(ret_facet)
                break

        if not found:
            active = False
            if display_type == "facet":
                if (facet_dict['facet_field'], facet_group.get('facet')) in request.params.items():
                    active = True
            facet_dict['fvalues'] = [{'count': 0, 'active': active, 'display_name': facet_dict.get('display_name'),
                                      'name': facet_group.get('facet')}]

    #If subfacet exists in the facet then iterate through the entire sub-facet structure to construct the results.
    if facet_group.get("subfacet"):
        subfacet_dict = []
        for subfacet in facet_group.get("subfacet"):
            subfacet_dict.append(
                construct_facet(subfacet, facet_dict={"facet_field": metadatafield}, metadatafield=metadatafield,
                                facet_level=2, facet_values=facet_values))
        facet_dict['subfacet'] = subfacet_dict

    return facet_dict
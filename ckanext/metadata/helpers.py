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

        if not None in [name, phone, org, address, position, email]:
            return True
        else:
            return False

    def check_geo_ext(data):
        north = data.get('northBoundLatitude', None)
        south = data.get('southBoundLatitude', None)
        east = data.get('eastBoundLongitude', None)
        west = data.get('westBoundLongitude', None)

        if not None in [north, south, east, west]:
            return True
        else:
            return False

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

        if not None in [details_obj['harvest'], details_obj['props']
                        , details_obj['date'], details_obj['authors']
                        , details_obj['contacts'], details_obj['geography']]:
            return details_obj
        else:
            return None

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
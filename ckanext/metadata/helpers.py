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
    try:
        pkg = [extra for extra in extras if extra.get('key') == 'md_package'][0]
    except:
        pkg = None

    if pkg:
        md = json.loads(pkg.get('value'))

        authors = []
        for agent in md['resourceDescription']['citedSourceAgents']:
            agent = agent['relatedAgent']['agentRole']
            author = make_author(agent)
            authors.append(author)

        res_contacts = []
        for agent in md['resourceDescription']['resourceContact']:
            agent = agent['relatedAgent']['agentRole']
            contact = make_author(agent)
            res_contacts.append(contact)

        md_props_author = md['metadataProperties']['metadataContact']['relatedAgent'].get('agentRole', None)
        md_props_author = make_author(md_props_author)

        return {
            'harvest_info': md.get('harvestInformation', None),
            'metadata_props': {'author': md_props_author},
            'citation_date': md['resourceDescription']['citationDates']['EventDateObject'].get('dateTime', None),
            'authors': authors,
            'res_contacts': res_contacts,
            'geographic_extent': md['resourceDescription'].get('geographicExtent', None)[0],
        }

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
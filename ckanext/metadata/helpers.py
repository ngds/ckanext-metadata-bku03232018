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

def md_package_extras_processor(extras):
    pkg = [extra for extra in extras if extra.get('key') == 'md_package'][0]
    md = json.loads(pkg.get('value'))

    authors = []
    for agent in md['resourceDescription']['citedSourceAgents']:
        agent = agent['relatedAgent']['agentRole']
        author = {
            'Name': agent.get('individual', None).get('personName', None),
            'Position': agent.get('individual',  None).get('personPosition', None),
            'Organization': agent.get('organizationName', None),
            'Address': agent.get('contactAddress', None),
            'Phone': agent.get('phoneNumber', None),
            'Email': agent.get('contactEmail', None),
        }
        authors.append(author)

    return {
        'citation_date': md['resourceDescription']['citationDates']['EventDateObject']['dateTime'],
        'authors': authors,
        'geographic_extent': md['resourceDescription']['geographicExtent'][0],
    }

def md_resource_extras_processer(res):
    md = json.loads(res.get('md_resource'))
    agent = md['resourceAccessOptions'][0]['distributor']\
        ['relatedAgent']['agentRole']
    distributor = {
        'Name': agent['individual']['personName'],
        'Position': agent['individual']['personPosition'],
        'Organization': agent['organizationName'],
        'Address': agent['contactAddress'],
        'Phone': agent['phoneNumber'],
        'Email': agent['contactEmail']
    }

    return {
        'distributor': distributor,
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
import json
import logging
import urllib2
import simplejson
import os
import usginmodels
import shutil

from shapely.geometry import asShape
from dateutil import parser as date_parser
from ckanext.metadata.common import plugins as p
from ckanext.metadata.common import logic
from ckanext.metadata.common import base
from ckanext.metadata.common import config
from ckanext.metadata.common import app_globals

log = logging.getLogger(__name__)
get_action = logic.get_action

"""
Lifted from ckanext-ngds/ckanext/ngds/csw/logic/view.py
Kudos goes to Ryan Clark on this function and the template that it renders.  It takes any
CKAN package in JSON format and parses it into a dictionary object that can be passed into
a Jinja2 template to render an ISO XML metadata record of the package.
"""
@logic.side_effect_free
def iso_19139(context, data_dict):
    """
    Serialize a CKAN Package as an ISO 19139 XML document

    Gets the package to be converted, processes it, and passes it through a Jinja2 template
    which generates an XML string

    @param context: CKAN background noise
    @param data_dict: Must contain an "id" key which is a pointer to the package to serialize
    @return: ISO19139 XML string
    """

    pkg = logic.action.get.package_show(context, data_dict)

    # ---- Reformat extras so they can be looked up
    pkg["additional"] = {}
    for extra in pkg["extras"]:
        pkg["additional"][extra["key"]] = extra["value"]

    # ---- Remove milliseconds from metadata dates
    pkg["metadata_modified"] = date_parser.parse(pkg.get("metadata_modified", "")).replace(microsecond=0).isoformat()
    pkg["metadata_created"] = date_parser.parse(pkg.get("metadata_created", "")).replace(microsecond=0).isoformat()

    # ---- Make sure that there is a publication date (otherwise you'll get invalid metadata)
    if not pkg["additional"].get("publication_date", False):
        pkg["additional"]["publication_date"] = pkg["metadata_created"]

    # ---- Figure out URIs
    other_ids = pkg["additional"].get("other_id", "[]")
    if len(json.loads(other_ids)) > 0:
        pkg["additional"]["datasetUri"] = json.loads(other_ids)[0]
    else:
        pkg["additional"]["datasetUri"] = config.get("ckan.site_url", "http://default.ngds.com").rstrip("/") + \
            "/dataset/%s" % pkg["name"]

    # ---- Any other identifiers
    pkg['additional']['other_id'] = json.loads(pkg['additional'].get('other_id', '[]'))

    # ---- Load the authors
    authors = pkg["additional"].get("authors", None)
    try:
        pkg["additional"]["authors"] = json.loads(authors)
    except:
        pkg["additional"]["authors"] = [{"name": pkg["author"], "email": pkg["author_email"]}]

    # ---- Load Location keywords
    location = pkg["additional"].get("location", "[]")
    try:
        loc = json.loads(location)
        if not isinstance(loc, list):
            pkg["additional"]["location"] = [loc]
        else:
            pkg["additional"]["location"] = loc
    except:
        pkg["additional"]["location"] = []

    # ---- Reformat facets
    faceted_ones = [t for t in pkg.get("tags", []) if t.get("vocabulary_id") is not None]
    pkg["additional"]["facets"] = {}
    for faceted_tag in faceted_ones:
        vocab = p.toolkit.get_action("vocabulary_show")(None, {"id": faceted_tag.get("vocabulary_id", "")})
        vocab_name = vocab.get("name", None)
        if vocab_name is not None and vocab_name in pkg["additional"]["facets"]:
            pkg["additional"]["facets"][vocab_name].append(faceted_tag.get("display_name"))
        elif vocab_name is not None:
            pkg["additional"]["facets"][vocab_name] = [faceted_tag.get("display_name")]

    # ---- Extract BBOX coords from extras
    pkg["extent"] = {}

    geojson = pkg["additional"].get("spatial", None)

    if geojson is not None:
        try:
            bounds = asShape(json.loads(geojson)).bounds
            pkg["extent"] = {
                "west": bounds[0],
                "south": bounds[1],
                "east": bounds[2],
                "north": bounds[3]
            }
        except:
            # Couldn't parse spatial extra into bounding coordinates
            pass

    # ---- Reorganize resources by distributor, on/offline
    online = {}
    offline = {}
    for resource in pkg.get("resources", []):
        try:
            distributor = json.loads(resource.get("distributor", "{}"))
        except ValueError:
            # This will happen if the content of the distributor field is invalid JSON
            distributor = {}

        if json.loads(resource.get("is_online", "true")):
            resources = online
        else:
            resources = offline

        if distributor != {}:
            name = distributor.get("name", "None")
        else:
            name = "None"

        if name not in resources.keys():
            resources[name] = {
                "distributor": distributor,
                "resources": [resource]
            }
        else:
            resources[name]["resources"].append(resource)

    pkg["additional"]["online"] = [value for key, value in online.iteritems()]
    pkg["additional"]["offline"] = [value for key, value in offline.iteritems()]

    # ---- All done, render the template
    output = base.render("xml/package_to_iso.xml", pkg)

    return output

# This is a local function
def http_get_content_models():
    cm_url = 'http://schemas.usgin.org/contentmodels.json'
    open_url = urllib2.urlopen(cm_url)
    content_models = simplejson.load(open_url)
    models = []
    for model in content_models:
        m = {}
        m['title'] = model['title']
        m['description'] = model['description']
        versions = []
        for version in model['versions']:
            v = {}
            v['uri'] = version['uri']
            v['version'] = version['version']
            v['layers'] = version['layers_info']
            versions.append(v)
        m['versions'] = versions
        m['uri'] = model['uri']
        m['label'] = model['label']
        models.append(m)
    return models

@logic.side_effect_free
def get_content_models(context, data_dict):
    try:
        return app_globals.config.get('usgin.content_models')
    except:
        try:
            return http_get_content_models()
        except:
            return json.loads({'success': False})

@logic.side_effect_free
def get_content_models_short(context, data_dict):
    models = http_get_content_models()
    short = map(lambda x: {'title': x['title'],
        'uri': x['uri'],
        'versions': x['versions']
    }, models)
    return short

#local method
def get_md_package(context, data_dict):

    md_package = None

    try:
	extras = data_dict.get('extras', [])

        for extra in extras:
            key = extra.get('key', None)
            if key == 'md_package':
                md_package = json.loads(extra.get('value'))
                break
    except:
        log.info("Missing md_package in extras field.")

    return md_package

@logic.side_effect_free
def is_usgin_structure_used(context, data_dict):

    md_package = get_md_package(context, data_dict)

    if None in [md_package]:
	return False

    resourceDescription = md_package.get('resourceDescription', {})
    uri = resourceDescription.get('usginContentModel', None)
    version = resourceDescription.get('usginContentModelVersion', None)
    layer = resourceDescription.get('usginContentModelLayer', None)

    if None in [uri, version, layer] or 'none' in [uri.lower(), version.lower(), layer.lower()]:
	return False

    return True

@logic.side_effect_free
def get_file_path(context, data_dict):

    res_id = data_dict.get('resourceId', None)
    suffix = data_dict.get('suffix', '')
    dir_1 = res_id[0:3]
    dir_2 = res_id[3:6]
    file = res_id[6:]
    storage_base = config.get('ckan.storage_path', 'default')

    return {'path': os.path.join(storage_base, 'resources', dir_1, dir_2, file+suffix)}

@logic.side_effect_free
def usginmodels_validate_file(context, data_dict):

    NewFilePath = ''
    resourceId = data_dict.get('resource_id', None)
    resourceName = data_dict.get('resource_name', None)
    packageId = data_dict.get('package_id', None)

    if None in [resourceId, packageId, resourceName]:
        log.info("Missing Package ID or Resource ID")
        return {'valid': False, 'message': '', 'log': 'Missing Package ID or Resource ID or Resource name', 'resourceId': resourceId}

    pkg = get_action('package_show')(context, {'id': packageId})

    md_package = get_md_package(context, pkg)

    if None in [md_package]:
        log.info("Missing md_package")
        return {'valid': False, 'message': '', 'log': 'Missing md_package', 'resourceName': resourceName, 'resourceId': resourceId}

    resourceDescription = md_package.get('resourceDescription', {})
    uri = resourceDescription.get('usginContentModel', None)
    version = resourceDescription.get('usginContentModelVersion', None)
    layer = resourceDescription.get('usginContentModelLayer', None)

    if None in [uri, version, layer] or 'none' in [uri.lower(), version.lower(), layer.lower()]:
        log.info("Missing content model information (URI, Version, Layer)")
        return {'valid': False, 'message': ['Missing content model information (URI, Version, Layer) or none given.'], 'resourceName': resourceName, 'resourceId': resourceId}

    #def get_file_path(res_id):
    #    dir_1 = res_id[0:3]
    #    dir_2 = res_id[3:6]
    #    file = res_id[6:]
    #    storage_base = config.get('ckan.storage_path', 'default')
    #    return os.path.join(storage_base, 'resources', dir_1, dir_2, file)

    path = get_file_path(context, {'resourceId': resourceId, 'suffix': ''})
    csv_file = path.get('path', None)

    if csv_file:
        log.info("Filename full path: %s " % csv_file)
    else:
        log.info("Cannot find the full path of the resources from %s" % resourceName)
        return {'valid': False, 'message': '', 'log': "Cannot find the full path of the resources from %s" % resourceName, 'resourceName': resourceName, 'resourceId': resourceId}

    try:
        log.debug("Start USGIN content model validation")

        # intializing variables to resove this issue:
        # Error - <type 'exceptions.UnboundLocalError'>: local variable 'valid, messages ...' referenced before assignment
        valid = False
	messages = None
	dataCorrected = None
	long_fields = None
	srs = None

        csv = open(csv_file, 'rbU')
        valid, messages, dataCorrected, long_fields, srs = usginmodels.validate_file(csv, version, layer)
    except:
        log.info("the file format is not supported.")
	return {'valid': False, 'message': ["the file format is not supported."], 'resourceName': resourceName, 'resourceId': resourceId}

    #close the file
    csv.close()

    #write the correcte data into a new file
    if (valid and messages) or (not valid):
	#No automatic erasing content, let the user fix his file, https://github.com/REI-Systems/ckanext-metadata/issues/3
	#Create a new file has correctedData instead
	if dataCorrected:
	#    try:
	#	shutil.copy2(csv_file, csv_file+'_original')
	#	log.debug("%s: New file copy is made %s." % (resourceName, csv_file+'_original'))
	#    except:
	#	log.debug("%s: Couldn't make a file copy." % resourceName)
	    import csv
	    try:
		NewFilePath = csv_file+'_CorrectedData'
		with open(NewFilePath, "wb") as f:
			writer = csv.writer(f)
			writer.writerows(dataCorrected)
		log.debug("%s: The new corrected data file has been created %s" % (resourceName, NewFilePath))
            except:
            	log.debug("%s: Couldn't erase the file content." % resourceName)

    if valid and messages:
	log.debug('%s: With changes the USGIN document will be valid' % resourceName)
    elif valid and not messages:
        log.debug("%s: USGIN document is valid" % resourceName)
    else:
        log.debug('%s: USGIN document is not valid' % resourceName)

    log.debug("%s: Finished USGIN content model validation." % resourceName)

    return {'valid': valid, 'message': messages, 'dataCorrected': dataCorrected, 'long_fields': long_fields, 'srs': srs, 'resourceName': resourceName, 'resourceId': resourceId}

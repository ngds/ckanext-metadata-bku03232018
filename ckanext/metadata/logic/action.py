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

import pprint
import re

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
        valid, messages, dataCorrected, long_fields, srs = usginmodels.validate_file(csv, version, layer, True) # True to fill default on row1
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


def package_create(context, data_dict):
    
    new_package = process_tags(data_dict)

    return logic.action.create.package_create(context, new_package) 
    

def package_update(context, data_dict):
    
    new_package = process_tags(data_dict)
    
    return logic.action.update.package_update(context, new_package) 


def process_tags(new_package):
    if 'md_package' in new_package:
        md_package = json.loads(new_package['md_package'])
    
        resourceDescription = md_package.get('resourceDescription', {})
    
        uri = resourceDescription.get('usginContentModel', None)
        version = resourceDescription.get('usginContentModelVersion', None)
        layer = resourceDescription.get('usginContentModelLayer', None)
    
        if None in [uri, version, layer] or 'none' in [uri.lower(), version.lower(), layer.lower()]:
	        usgin_used = False
        else:
            usgin_used = True

        if usgin_used:
            pp = pprint.PrettyPrinter(indent=4)
    
            #remove tags which start with usgincm:
            remove_tags = []
            for tags in new_package['tags']:
                if tags['name'].startswith("usgincm:"):
                   remove_tags.append(tags)
            
            new_package['tags'] = [item for item in new_package['tags'] if item not in remove_tags]          
            
            content_models = http_get_content_models()                        
            
            for data in content_models:
                if str(uri).strip() in data['uri'].strip():
                    title = data['title'].strip()  
                    break
            
            key = title + "+" + layer + "+" + version

            prefix_map = get_usgin_prefix()
            
            for prefix in prefix_map.get(key):
                if not tag_exists(prefix.decode('UTF-8'), new_package['tags']):
                    new_package['tags'].append({ 'name': prefix.decode('UTF-8'), 'state': 'active'})
    
                    if(new_package['tag_string'] != u''):
                        tag_string = new_package['tag_string'].split(',')
                        tag_string = [x for x in tag_string if not x.startswith('usgincm:')]
                        tag_string.append(prefix)
                        tag_string = ', '.join([str(x) for x in tag_string])
                        new_package['tag_string'] = tag_string.decode('UTF-8')
                    else:
                        keyword = prefix
                        new_package['tag_string'] =  keyword.decode('UTF-8')
            
    return new_package
     

def tag_exists(prefix, tags_list):
    for tags in tags_list:
        if prefix in tags['name']:
           return True
    
    return False


def get_usgin_prefix():
    prefix_map = {
        
        "Active Fault/Quaternary Fault+ActiveFault+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/activefault/1.1" : ["usgincm:Quaternary Fault","usgincm:Active Fault"],
        "Active Fault/Quaternary Fault+ActiveFault+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/activefault/1.2" : ["usgincm:Active Fault1.2"],
        "Aqueous Chemistry+BaseMetals+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.BaseMetals1.10"],
        "Aqueous Chemistry+CommonAnalytes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.CommonAnalytes1.10"],
        "Aqueous Chemistry+FreeGas+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.FreeGas1.10"],
        "Aqueous Chemistry+GasIsotopes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.GasIsotopes1.10"],
        "Aqueous Chemistry+IsotopesDissolved+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.IsotopesDissolved1.10"],
        "Aqueous Chemistry+MajorDissolvedConstituents+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.MajorDissolvedConstituents1.10"],
        "Aqueous Chemistry+MinorDissolvedConstituents+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.MinorDissolvedConstituents1.10"],
        "Aqueous Chemistry+Nitrogen+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.Nitrogen1.10"],
        "Aqueous Chemistry+SingleAnalyte+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.SingleAnalyte1.10"],
        "Aqueous Chemistry+WaterDissolvedGas+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.WaterDissolvedGas1.10"],
        "Aqueous Chemistry+WaterIsotopes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.WaterIsotopes1.10"],
        "Aqueous Chemistry+WaterQuality+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.10" : ["usgincm:Aqueous Chemistry.WaterQuality1.10"],
        "Aqueous Chemistry+BaseMetals+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.BaseMetals"],
        "Aqueous Chemistry+CommonAnalytes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.CommonAnalytes"],
        "Aqueous Chemistry+FreeGas+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.FreeGas"],
        "Aqueous Chemistry+GasIsotopes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.GasIsotopes"],
        "Aqueous Chemistry+IsotopesDissolved+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.IsotopesDissolved"],
        "Aqueous Chemistry+MajorDissolvedConstituents+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.MajorDissolvedConstituents"],
        "Aqueous Chemistry+MinorDissolvedConstituents+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.MinorDissolvedConstituents"],
        "Aqueous Chemistry+Nitrogen+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.Nitrogen"],
        "Aqueous Chemistry+SingleAnalyte+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.SingleAnalyte"],
        "Aqueous Chemistry+WaterDissolvedGas+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.WaterDissolvedGas"],
        "Aqueous Chemistry+WaterIsotopes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.WaterIsotopes"],
        "Aqueous Chemistry+WaterQuality+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/1.9" : ["usgincm:Aqueous Chemistry.WaterQuality"],
        "Aqueous Chemistry+MineralRecoveryBrine+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/aqueouschemistry/draft" : ["usgincm:Aqueous Chemistry.MineralRecoveryBrine"],
        "Borehole Lithology Intercepts+BoreholeLithIntercept+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/bhlithintercept/1.1" : ["usgincm:Borehole Lithology Intercepts"],
        "Borehole Lithology Interval Feature+BoreholeLithInterval+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/bhlithinterval/0.9" : ["usgincm:Borehole Lithology Interval Feature"],
        "Borehole Temperature Observation+BoreholeTemperature+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/boreholetemperature/1.5" : ["usgincm:Borehole Temperature Observation"],
        "Contour Lines+ContourLine+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/contourlines/1.0" : ["usgincm:Contour Lines"],
        "Direct Use Feature+DirectUseSite+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/directusesite/1.5" : ["usgincm:Direct Use Feature"],
        "Drill Stem Test Observations (deprecated)+DrillStemTest+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/drillstemtest/1.8" : ["usgincm:DrillStemTest"],
        "Fluid Flux Injection and Disposal+FluidFluxInjection+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/fluidfluxinjection/1.1" : ["usgincm:Fluid Flux Injection and Disposal"],
        "Well Fluid Production+FluidProduction+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/fluidproduction/1.1" : ["usgincm:Well Fluid Production"],
        "Geologic Reservoir+GeologicReservoir+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geologicreservoir/0.2" : ["usgincm:Geologic Reservoir"],
        "Geologic Contact Feature+ContactView+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geosciml-portrayal-contacts/2.0" : ["usgincm:Geologic Contact Feature"],
        "Geologic Fault Feature / Shear Displacement Structure+Fault+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geosciml-portrayal-faults/1.0" : ["usgincm:Fault Feature"],
        "Geologic Fault Feature / Shear Displacement Structure+Fault+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geosciml-portrayal-faults/1.1" : ["usgincm:Fault Feature1.1"],
        "Geologic Fault Feature / Shear Displacement Structure+ShearDisplacementStructureView+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geosciml-portrayal-faults/2.0" : ["usgincm:Fault Feature2.0 , usgincm:Shear Displacement Structure"],
        "Geologic Units+GeologicUnitView+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geosciml-portrayal-units/2.0" : ["usgincm:Geologic Units"],
        "Geothermal Area+GeothermalArea+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geothermalarea/0.5" : ["usgincm:Geothermal Area"],
        "Geothermal Area+GeothermalArea+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geothermalarea/0.7" : ["usgincm:Geothermal Area0.7"],
        "Geothermal Fluid Production (deprecated)+GeothermalFluidProduction+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geothermalfluidproduction/1.1" : ["usgincm:Geothermal Fluid Production"],
        "Powell and Cumming Geothermometry+GasAnalysis+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geothermometry/0.1" : ["usgincm:Powell Cummings Geothermometry.GasAnalysis"],
        "Powell and Cumming Geothermometry+LiquidAnalysis+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geothermometry/0.1" : ["usgincm:Powell Cummings Geothermometry.LiquidAnalysis"],
        "Powell and Cumming Geothermometry+GasAnalysis+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geothermometry/2.0" : ["usgincm:Powell Cummings Geothermometry.GasAnalysis2.0"],
        "Powell and Cumming Geothermometry+LiquidAnalysis+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/geothermometry/2.0" : ["usgincm:Powell Cummings Geothermometry.LiquidAnalysis2.0"],
        "Gravity Stations+GravityStation+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/gravitystations/0.1" : ["usgincm:Gravity Stations"],
        "Heat Flow+HeatFlow+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/heatflow/1.15" : ["usgincm:Heat Flow"],
        "Heat Flow+HeatFlow+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/heatflow/1.23" : ["usgincm:Heat Flow1.23"],
        "Heat Pump Facility+HeatPumpFacility+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/HeatPumpFacility/0.6" : ["usgincm:Heat Pump Facility"],
        "Hydraulic Properties+HydraulicProperty+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/hydraulicproperties/1.0" : ["usgincm:Hydraulic Properties"],
        "Seismic Event Hypocenter+EarthquakeHypocenter+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/hypocenter/1.2.2" : ["usgincm:Seismic Event Hypocenter"],
        "Seismic Event Hypocenter+EarthquakeHypocenter+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/hypocenter/1.6" : ["usgincm:Seismic Event Hypocenter1.6"],
        "Seismic Event Hypocenter+Hypocenter+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/hypocenter/1.7" : ["usgincm:Seismic Event Hypocenter1.7"],
        "Mineral Recovery Brine+MineralRecoveryBrine+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/mineralrecoverybrine/draft" : ["usgincm:Mineral Recovery Brine"],
        "Abandoned Mines+AbandonedMine+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/mines/0.3" : ["usgincm:Abandoned Mines"],
        "Physical Sample+PhysicalSample+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/physicalsample/0.8" : ["usgincm:Physical Sample"],
        "Geothermal Power Plant Facility+PowerPlantFacility+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/PowerPlantFacility/0.2" : ["usgincm:Geothermal Power Plant Facility"],
        "Power Plant Production+PlantProduction+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/PowerPlantProduction/0.8" : ["usgincm:Power Plant Production"],
        "Power Plant Production+PlantProduction+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/PowerPlantProduction/1.0" : ["usgincm:Power Plant Production1.0"],
        "Radiogenic Heat Production+RadiogenicHeatProduction+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/radiogenicheatproduction/0.5" : ["usgincm:Radiogenic Heat Production"],
        "Rock Chemistry+Isotopes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.Isotopes"],
        "Rock Chemistry+NobleGases+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.NobleGases"],
        "Rock Chemistry+RareEarths+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.RareEarths"],
        "Rock Chemistry+SingleAnalytes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.SingleAnalytes"],
        "Rock Chemistry+StableIsotopes+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.StableIsotopes"],
        "Rock Chemistry+TraceElements+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.TraceElements"],
        "Rock Chemistry+USeries+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.USeries"],
        "Rock Chemistry+Volatiles+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.Volatiles"],
        "Rock Chemistry+WRMajorElements+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/0.4" : ["usgincm:Rock Chemistry.WRMajorElements"],
        "Rock Chemistry+MineralRecoveryBrine+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/rockchemistry/draft" : ["usgincm:Rock Chemistry.MineralRecoveryBrine"],
        "Thermal Conductivity Observation+MDThermalConductivity+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/thermalconductivity/1.5" : ["usgincm:Thermal Conductivity Observation"],
        "Thermal Conductivity Observation+ThermalConductivity+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/thermalconductivity/1.6" : ["usgincm:Thermal Conductivity Observation1.6"],
        "Thermal Conductivity Observation+ThermalConductivity+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/thermalconductivity/2.0" : ["usgincm:Thermal Conductivity Observation2.0"],
        "Thermal Conductivity Observation+ThermalConductivity+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/thermalconductivity/2.1" : ["usgincm:Thermal Conductivity Observation2.1"],
        "Thermal/Hot Spring Feature+ThermalSpring+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/thermalspring/1.6" : ["usgincm:Hot Spring Feature"],
        "Thermal/Hot Spring Feature+ThermalSpring+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/thermalspring/1.8" : ["usgincm:Hot Spring Feature1.8"],
        "Volcanic Vents+VolcanicVent+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/volcanicvent/1.0" : ["usgincm:Volcanic Vents"],
        "Volcanic Vents+VolcanicVent+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/volcanicvent/1.4" : ["usgincm:Volcanic Vents1.4"],
        "Well Header Observation+Wellheader+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/wellheader/1.5" : ["usgincm:Well Header Observation"],
        "Well Log Observation+WellLog+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/welllog/0.8" : ["usgincm:Well Log Observation"],
        "Well Tests+WellTest+http://stategeothermaldata.org/uri-gin/aasg/xmlschema/welltest/1.0" : ["usgincm:Well Tests"],
    }    
    
    return prefix_map


    
    

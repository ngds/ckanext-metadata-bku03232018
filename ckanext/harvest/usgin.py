import json
import re
import datetime

from ckanext.spatial.harvesters import CSWHarvester
from ckanext.harvest.xml_reader import NgdsXmlMapping

class USGINHarvester(CSWHarvester):

    def info(self):
        """Return some information about this particular harvester"""
        return {
            'name': 'ngds',
            'title': 'NGDS CSW Server',
            'description': 'CSW Server offering metadata that conforms to the NGDS ISO Profile'
        }

    def buildRelatedAgent(self, data):
        agent = {}
        role = agent["agentRole"] = {}
        role["contactAddress"] = None
        role["contactEmail"] = data.get("contact-info", None).get("email", None)
        role["individual"] = {}
        role["individual"]["personName"] = data.get("individual-name", None)
        role["individual"]["personPosition"] = data.get("position-name", None)
        role["individual"]["personRole"] = data.get("role", None)
        role["organizationName"] = data.get("organisation-name", None)
        return agent

    def buildAccessLink(self, data):
        protocol = data.get("protocol", None)
        link_obj = {}
        link_obj = link_obj["linkObject"] = {}
        link_obj["url"] = data.get("url", None)
        link_obj["linkTitle"] = data.get("name", None)
        link_obj["linkTargetResourceType"] = protocol
        link_obj["linkContentResourceType"] = protocol

        description = data.get("description", None)
        link_description = link_obj["description"] = None
        ogc_layer = link_obj["ogc_layer"] = None

        if description and protocol.lower() == 'ogc:wms':
            regex = re.compile('parameters:layers:(?P<layer_name>{.+})$')
            layer_search = regex.search(description)
            layer = layer_search.group('layer_name') if layer_search else None
            ogc_layer = layer
            link_description = None

        if description and protocol.lower() == 'ogc:wfs':
            regex = re.compile('parameters:typeName:(?P<layer_name>{.+})$')
            layer_search = regex.search(description)
            layer = layer_search.group('layer_name') if layer_search else None
            ogc_layer = layer
            link_description = None

        if description and protocol.lower() not in ['ogc:wfs', 'ogc:wms']:
            link_description = description

        return link_obj

    def get_package_dict(self, iso_values, harvest_object):
        """
        Override's ckanext.spatial.harvesters.SpatialHarvester.get_package_dict

        This function generates the package dictionary from the harvested object. This package_dict
        will be fed to the `package_create` action.
        """

        # First lets generate exactly the same package dict that the standard harvester would.
        package_dict = super(USGINHarvester, self).get_package_dict(iso_values, harvest_object)

        # Then lets parse the harvested XML document with a customized NGDS parser
        doc = NgdsXmlMapping(xml_str=harvest_object.content)
        values = doc.read_values()

        # Then lets customize the package_dict further
        extras = package_dict['extras']

        # Published or unpublished
        package_dict['private'] = False

        # Any otherID
        other_id = {"key": "other_id", "value": json.dumps([values['other_id']])}
        extras.append(other_id)

        # The data type
        data_type = {"key": "dataset_category", "value": values['data_type']}
        extras.append(data_type)

        # Pub date
        publication_date = {"key": "publication_date", "value": values['publication_date']}
        extras.append(publication_date)

        # Maintainers
        maintainers = {
            "key": "maintainers",
            "value": json.dumps([self.buildRelatedAgent(agent) for agent in \
                                 values.get('maintainers', [])])
        }
        extras.append(maintainers)

        # Authors
        authors = {
            "key": "authors",
            "value": json.dumps([self.buildRelatedAgent(agent) for agent in \
                                 values.get('authors', [])])
        }
        extras.append(authors)

        # Quality
        quality = {"key": "quality", "value": values.get('quality', '')}
        extras.append(quality)

        # Lineage
        lineage = {"key": "lineage", "value": values.get('lineage', '')}
        extras.append(lineage)

        # Status
        status = {"key": "status", "value": values.get('status', '')}
        extras.append(status)

        md_package = {}

        harvest_info = md_package["harvestInformation"] = {}
        harvest_info["version"] = values.get("metadata-standard-version", "")
        harvest_info["crawlDate"] = ""
        harvest_info["indexDate"] = values.get("date-released", "")
        harvest_info["originalFileIdentifier"] = values.get("guid", "")
        harvest_info["originalFormat"] = values.get("metadata-standard-name", "")
        harvest_info["harvestURL"] = ""
        harvest_info["sourceInfo"] = ""
        harvest_source = harvest_info["sourceInfo"] = {}
        harvest_source["harvestSourceID"] = ""
        harvest_source["viewID"] = ""
        harvest_source["harvestSourceName"] = ""

        md_properties = md_package["metadataProperties"] = {}
        mp_contact = md_properties["metadataContact"] = {}
        mp_agent = mp_contact["relatedAgent"] = {}
        mp_agent_role = mp_agent["agentRole"] = {}
        mp_agent_role["agentRoleURI"] = ""
        mp_agent_role["agentRoleLabel"] = ""
        mp_individual = mp_agent_role["individual"] = {}
        mp_individual["personURI"] = ""
        mp_individual["personName"] = ""
        mp_individual["personPosition"] = ""
        mp_agent["organizationName"] = values.get("contact", "")
        mp_agent["organizationURI"] = ""
        mp_agent["phoneNumber"] = ""
        mp_agent["contactEmail"] = values.get("contact-email", "")
        mp_agent["contactAddress"] = ""

        dates = md_package["citationDates"] = {}
        dates["EventDateObject"] = {}
        dates["EventDateObject"]["dateTime"] = values.get("metadata-date", "")

        md_package["resourceDescription"] = values.get("abstract", "")
        md_package["resourceTitle"] = values.get("title", "")


        geo_ext = md_package["geographicExtent"] = []
        geo_ext.append({
            "eastBoundLongitude": values.get("bbox", "")[0].get("east", ""),
            "northBoundLatitude": values.get("bbox", "")[0].get("north", ""),
            "southBoundLatitude": values.get("bbox", "")[0].get("south", ""),
            "westBoundLongitude": values.get("bbox", "")[0].get("west", "")
        })

        md_package["citedSourceAgents"] = [
            self.buildRelatedAgent(agent) for agent in values.get('authors', [])
        ]

        md_package["resourceContact"] = [
            self.buildRelatedAgent(agent) for agent in values.get('maintainers', [])
        ]

        md_access = md_package["resourceAccessOptions"] = {}
        distributors = md_access["distributors"] = [
            self.buildRelatedAgent(agent) for agent in values.get('distributor', [])
        ]

        accessLinks = [self.buildAccessLink(res) for res in values.get('resource-locator', [])]

        access_links = md_access["accessLinks"] = accessLinks

        #json_package = json.dumps(md_package)

        #print json_package

        extras.append({"key": "md_package", "value": str(md_package)})

        # When finished, be sure to return the dict
        return package_dict
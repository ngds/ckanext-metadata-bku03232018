import json
import re

from ckanext.spatial.harvesters import CSWHarvester
from ckanext.harvest.xml_reader import NgdsXmlMapping

class USGINHarvester(CSWHarvester):
    '''
    related_agent = {
        "agentRole": {
            "contactAddress": None,
            "contactEmail": None,
            "individual": {
                "personName": None,
                "personPosition": None,
            },
            "organizationName": None,
            "phoneNumber": None
        }
    }
    '''
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
        role["contactAddress"] = ""
        role["contactEmail"] = data.get("contact-info", "").get("email", "")
        role["individual"]["personName"] = data.get("individual-name", "")
        role["individual"]["personPosition"] = data.get("position-name", "")
        role["individual"]["personRole"] = data.get("role", "")
        role["organizationName"] = data.get("organisation-name", "")
        return agent

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

        print values

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
        dates = md_package["citationDates"] = {}
        dates["EventDateObject"] = {}
        dates["EventDateObject"]["dateTime"] = package_dict.get

        md_package = {
            "citationDates": {
                "EventDateObject": {
                    "dateTime": None
                }
            },
            "resourceDescription": "",
            "resourceTitle": "",
            "resourceContact": {""" related agent here """},
            "citedSourceAgents": [""" related agents here """],
            "geographicExtent": [{
                "eastBoundLongitude": None,
                "northBoundLatitude": None,
                "southBoundLatitude": None,
                "westBoundLongitude": None
            }]
        }

        md_resource = {
            "accessLinks": {
                "LinkObject": {
                    "linkDescription": None,
                    "linkTitle": None
                }
            },
            "distributor": """ related agent here """
        }

        # When finished, be sure to return the dict
        print package_dict
        return package_dict
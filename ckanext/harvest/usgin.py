import json
import re
import pytz
from dateutil.parser import parse
from pylons import config

from ckanext.spatial.harvesters import CSWHarvester
from ckanext.spatial.harvesters.base import guess_resource_format
from ckanext.harvest.xml_reader import NgdsXmlMapping

#CSWHarvester extends SpatialHarvester, which appears to implement ISpatialHarvester
#  but does not explicitly declare that it does.

class USGINHarvester(CSWHarvester):

    def info(self):
        """Return some information about this particular harvester"""
        return {
            'name': 'ngds',
            'title': 'NGDS CSW Server',
            'description': 'CSW Server offering metadata that conforms to the NGDS ISO Profile'
        }

    def buildRelatedAgent(self, data):
        return {
            "relatedAgent": {
                "agentRole": {
                    "contactAddress": None,
                    "contactEmail": data.get("contact-info", None).get("email", None),
                    "individual": {
                        "personName": data.get("individual-name", None),
                        "personPosition": data.get("position-name", None),
                        "personRole": data.get("role", None),
                    },
                    "organizationName": data.get("organisation-name", None)
                }
            }
        }

    def buildBbox(self, data):
        bbox = data.get("bbox", None)
        if bbox:
            return [{
                "eastBoundLongitude": bbox[0].get("east", ""),
                "northBoundLatitude": bbox[0].get("north", ""),
                "southBoundLatitude": bbox[0].get("south", ""),
                "westBoundLongitude": bbox[0].get("west", "")
            }]

    def buildAccessLink(self, data):
        protocol = data.get("protocol", None)

        if protocol is None:
            protocol = data.get("resource_locator_protocol", None)

        description = data.get("description", None)
        ogc_layer = None
        link_description = None

        if description and protocol.lower() == 'ogc:wms':
            regex = re.match('parameters:{layers:"(.*)"}', description)

            try:
                layer = regex.group(1) if regex else None
            except:
                layer = None

            ogc_layer = layer
            link_description = None

        if description and protocol.lower() == 'ogc:wfs':
            regex = re.match('parameters:{typeName:"(.*)"}', description)

            try:
                layer = regex.group(1) if regex else None
            except:
                layer = None

            ogc_layer = layer
            link_description = None

        if description and protocol.lower() not in ['ogc:wfs', 'ogc:wms']:
            link_description = description

        link_obj = {
            "linkObject": {
                "url": data.get("url", None),
                "linkTitle": data.get("name", None),
                "linkTargetResourceType": protocol,
                "linkContentResourceType": protocol,
                "description": link_description,
                "ogc_layer": ogc_layer
            }
        }

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

        # Pub date -- make datetime 'naive', as in unaware of timezones because
        # CKAN doesn't support timezones
        pub_date = values.get('publication_date', None)
        if pub_date:
            date_obj = parse(pub_date)
            pub_date = date_obj.replace(tzinfo=None)
        publication_date = {"key": "publication_date", "value": pub_date}
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


        resource_locators = iso_values.get('resource-locator', []) +\
            iso_values.get('resource-locator-identification', [])

        cited_source_agent = [self.buildRelatedAgent(agent) for agent in values.get('authors', [])]
        resource_contact = [self.buildRelatedAgent(agent) for agent in values.get('maintainers', [])]
        distributors = [self.buildRelatedAgent(agent) for agent in values.get('distributor', [])]
        access_links = [self.buildAccessLink(res) for res in values.get('resource-locator', [])]

        for resource in package_dict['resources']:
            md_resource = json.dumps({
                "distributors": distributors,
                "accessLink": self.buildAccessLink(resource)
            })

            resource["md_resource"] = md_resource

        md_package = {
            "harvestInformation": {
                "version": values.get("metadata-standard-version", ""),
                "crawlDate": "",
                "indexDate": values.get("date-released", ""),
                "originalFileIdentifier": values.get("guid", ""),
                "originalFormat": values.get("metadata-standard-name", ""),
                "harvestURL": "",
                "sourceInfo": {
                    "harvestSourceID": "",
                    "viewID": "",
                    "harvestSourceName": ""
                }
            },
            "metadataProperties": {
                "metadataContact": {
                    "relatedAgent": {
                        "agentRole": {
                            "agentRoleURI": "",
                            "agentRoleLabel": "",
                            "individual": {
                                "personURI": "",
                                "personName": "",
                                "personPosition": ""
                            },
                            "organizationName": values.get("contact", ""),
                            "organizationURI": "",
                            "phoneNumber": "",
                            "contactEmail": values.get("contact-email", ""),
                            "contactAddress": ""
                        }
                    }
                }
            },
            "resourceDescription": {
                "resourceTitle": values.get("title", ""),
                "resourceDescription": values.get("abstract", ""),
                "usginContentModel": "",
                "usginContentModelLayer": "",
                "usginContentModelVersion": "",
                "citedSourceAgents": cited_source_agent,
                "citationDates": {
                    "EventDateObject": {
                        "dateTime": values.get("metadata-date", "")
                    }
                },
                "resourceContact": resource_contact,
                "resourceAccessOptions": {
                    "distributors": distributors,
                    "accessLinks": access_links,
                },
                "geographicExtent": self.buildBbox(values),
            },
        }

        md_package = json.dumps(md_package)

        extras.append({"key": "md_package", "value": md_package})

        # When finished, be sure to return the dict
        return package_dict
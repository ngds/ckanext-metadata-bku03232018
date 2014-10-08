import json
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

        harvest_info = md_package["harvestInformation"] = {}
        harvest_info["version"] = values.get("metadata-standard-version", None)
        harvest_info["crawlDate"] = datetime.datetime.now().isoformat()
        harvest_info["indexDate"] = values.get("date-released", None)
        harvest_info["originalFileIdentifier"] = values.get("guid", None)
        harvest_info["originalFormat"] = values.get("metadata-standard-name", None)
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
        mp_agent_role["agentRoleURI"] = None
        mp_agent_role["agentRoleLabel"] = None
        mp_individual = mp_agent_role["individual"] = {}
        mp_individual["personURI"] = None
        mp_individual["personName"] = None
        mp_individual["personPosition"] = None
        mp_agent["organizationName"] = values.get("contact", None)
        mp_agent["organizationURI"] = None
        mp_agent["phoneNumber"] = None
        mp_agent["contactEmail"] = values.get("contact-email", None)
        mp_agent["contactAddress"] = None

        dates = md_package["citationDates"] = {}
        dates["EventDateObject"] = {}
        dates["EventDateObject"]["dateTime"] = values.get("metadata-date", None)

        md_package["resourceDescription"] = values.get("abstract", None)
        md_package["resourceTitle"] = values.get("title", None)


        geo_ext = md_package["geographicExtent"] = {[]}
        geo_ext[0].append({
            "eastBoundLongitude": values.get("bbox", None)[0].get("east", None),
            "northBoundLatitude": values.get("bbox", None)[0].get("north", None),
            "southBoundLatitude": values.get("bbox", None)[0].get("south", None),
            "westBoundLongitude": values.get("bbox", None)[0].get("west", None)
        })

        md_package["citedSourceAgents"] = json.dumps([
            self.buildRelatedAgent(agent) for agent in values.get('authors', [])
        ])

        md_package["resourceContact"] = json.dumps([
            self.buildRelatedAgent(agent) for agent in values.get('maintainers', [])
        ])


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
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
#CSWHarvester is defined in ckanext-spatial/ckanest/spatial/harversters/csw.py

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
                    "jmd:conceptPrefLabel":  data.get("role", None),
                    "jmd:vocabularyURI":  data.get("role-codespace", None),
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
    #smr attempt 2015-10-14
##    def buildTelephone(self,data):
##        return {
##            "jmd:phoneNumber": data,
##            "jmd:phoneLabel":"voice"
##        }

    #smr attempt 2015-10-14
##    def buildRelatedAgentNew(self, data):
##        # data is ISOResponsibleParty class from harvested_metadata.py
##
##        the-contact-address = '"' & data.get("contact-info", None).get("postal-address", None).get("delivery-point", None) & ', ' & \
##                data.get("contact-info", None).get("postal-address", None).get("city", None) & ', ' & \
##                data.get("contact-info", None).get("postal-address", None).get("administrative-area", None) & ', ' & \
##                data.get("contact-info", None).get("postal-address", None).get("postal-code", None) & ', ' & \
##                data.get("contact-info", None).get("postal-address", None).get("country", None) & '"'
##            
##        return  {
##        "jmd:agentRole": {
##            "jmd:conceptPrefLabel":  data.get("role", None),
##            "jmd:vocabularyURI":  data.get("role-codespace", None)
##        },
##        "jmd:agents": [{
##            "jmd:personName": data.get("individual-name", None),
##            "jmd:personPosition": data.get("position-name", None),
##            "jmd:organizationNames": [data.get("organisation-name", None)],
##            # if data.get("contact-info", None).get("telephone-voice", []): 
##            "jmd:phoneContacts":[ self.buildTelephone(thetel) for thetel in data.get("contact-info", None).get("telephone-voice", [])
##                ],
##            "jmd:contactEmails": [data.get("contact-info", None).get("email", None)],
##            "jmd:contactAddress": the-contact-address,   
##              } 
##            ]
##        }

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


    def buildDistributorOptions(self, data):
        """
        Each distributor may have multiple digitalTrasferOptions, MD_format, standard order process. 
        if only on distributor is present, links from MD_Distribution to transferOptions and format have to be projected to distributor
        if no distributor provided, create an unknown and associate with the required DigitalTransferOptions linksage
        """
        pass  #TODO 
    
    def get_package_dict(self, iso_values, harvest_object):
        """
        Override's ckanext.spatial.harvesters.SpatialHarvester.get_package_dict

        This function generates the package dictionary from the harvested object. This package_dict
        will be fed to the `package_create` action.
        """

        # First lets generate exactly the same package dict that the standard harvester would.
        #this executes get_package_dict on CSWHarvester, which is the parent of USGINHarvester
        #CSWHarverster inherits get_package_dict from SpatialHarvester, defined in 
        #ckanext-spatial/ ckanext/spatial/harversters/base.py
        package_dict = super(USGINHarvester, self).get_package_dict(iso_values, harvest_object)

        # Then lets parse the harvested XML document with a customized NGDS parser
        doc = NgdsXmlMapping(xml_str=harvest_object.content)
        values = doc.read_values()

        # pull extras from package_dict created with base.py (harvested_metadata.py)
        extras = package_dict['extras']

        # Published or unpublished
        package_dict['private'] = False

        # Any otherID; smr got it datasetURI
        other_id = {"key": "other_id", "value": json.dumps([values['other_id']])}
        extras.append(other_id)

        # The data type; smr got it hierarchyLevelName
        data_type = {"key": "dataset_category", "value": values['data_type']}
        extras.append(data_type)

        # Pub date -- make datetime 'naive', as in unaware of timezones because
        # CKAN doesn't support timezones
        pub_date = values.get('publication_date', None)
        #smr moved this code to harvested_metadata.py; should be able to leave out this if block.
        #if pub_date:
        #   date_obj = parse(pub_date)
        #   pub_date = date_obj.replace(tzinfo=None) 
        #smr still need to append to the extras so leave this
        publication_date = {"key": "publication_date", "value": pub_date}
        extras.append(publication_date)

        # Metadata maintainers
        # smr this is the metadata pointOfContact. metadata-point-of-contact handled by harvested_metadata.py
        maintainers = {
            "key": "maintainers",
            "value": json.dumps([self.buildRelatedAgent(agent) for agent in \
                                 values.get('metadata-point-of-contact', [])])
        }
        extras.append(maintainers)

        # SMR add 2015-10-14 resource-contacts
        # smr handled by harvested_metadata.py
        resourcecontact = {
            "key": "resource-contact",
            "value": json.dumps([self.buildRelatedAgent(agent) for agent in \
                                 values.get('responsible-organisation', [])])
        }
        extras.append(resourcecontact)

        # Authors  smr add authors to harvested_metadata.py
        authors = {
            "key": "authors",
            "value": json.dumps([self.buildRelatedAgent(agent) for agent in \
                                 values.get('authors', [])])
        }
        extras.append(authors)

        # Quality  SMR copy to harvested_metadata.py
        quality = {"key": "quality", "value": values.get('quality', '')}
        extras.append(quality)

        # Lineage  SMR handled in harvested_metadata.py
        lineage = {"key": "lineage", "value": values.get('lineage', '')}
        extras.append(lineage)

        # Status  SMR add in harvested_metadata.py
        status = {"key": "status", "value": values.get('status', '')}
        extras.append(status)

        # SMR handled in harvested_metadata.py
        resource_locators = iso_values.get('resource-locator', []) +\
            iso_values.get('resource-locator-identification', [])

        cited_source_agent = [self.buildRelatedAgent(agent) for agent in values.get('authors', [])]
        metadata_contact = [self.buildRelatedAgent(agent) for agent in values.get('maintainers', [])]
        resource_contact = [self.buildRelatedAgent(agent) for agent in values.get('resource-contact', [])]
        distributors = [self.buildRelatedAgent(agent) for agent in values.get('distributor', [])]
        access_links = [self.buildAccessLink(res) for res in values.get('resource-locator', [])]

        # this treatment loses binding between different links and different formats/distributors.
        # resources in package_dict is defined in base.py line 396-417, is Accesslinks constructed from
        # everything in resource_locators defined above
        for resource in package_dict['resources']:
            md_resource = json.dumps({
                "distributors": distributors,
                "accessLink": self.buildAccessLink(resource)
            })
            
        # TODO  construct a distributor access options object to put in md_package.  Group on distributors, with a collection of online or offline distributions options associated with each distributor
        
        

            resource["md_resource"] = md_resource

        md_package = {
            "harvestInformation": {
                "version": values.get("metadata-standard-version", ""),
                "crawlDate": "",
                "indexDate": values.get("metadata-date", ""),
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
                "metadataContact": metadata_contact
##                {
##                    "relatedAgent": {
##                        "agentRole": {
##                            "agentRoleURI":  values.get("metadata-point-of-contact", "").get("role-codelist",""),
##                            "agentRoleLabel":  values.get("metadata-point-of-contact", "").get("role",""),
##                            "individual": {
##                                "personURI": "",
##                                "personName":  values.get("metadata-point-of-contact", "").get("individual-name",""),
##                                "personPosition":  values.get("metadata-point-of-contact", "").get("position-name","")
##                            },
##                            "organizationName": values.get("metadata-point-of-contact", "").get("organisation-name",""),
##                            "organizationURI": "",
##                            "phoneNumber":  values.get("metadata-point-of-contact", "").get("contact-info","").get("telephone-voice",""),
##                            "contactEmail": values.get("metadata-point-of-contact", "").get("contact-info","").get("email",""),
##                            "contactAddress": ""
##                        }
##                    }
##                }
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
                        "dateTime": values.get("dataset-reference-date", "").get("value","")
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

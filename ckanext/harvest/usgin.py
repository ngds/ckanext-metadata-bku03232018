import json
import re
import pytz
from dateutil.parser import parse
from pylons import config

from ckanext.spatial.harvesters import CSWHarvester
from ckanext.spatial.harvesters.base import guess_resource_format
from ckanext.harvest.usgin_xml_reader import USGINXmlMapping

#CSWHarvester extends SpatialHarvester, which appears to implement ISpatialHarvester
#  but does not explicitly declare that it does.
#CSWHarvester is defined in ckanext-spatial/ckanest/spatial/harversters/csw.py

class USGINHarvester(CSWHarvester):

    force_import = False

    def info(self):
        """Return some information about this particular harvester"""
        return {
            'name': 'USGIN-harvester',
            'title': 'USGIN CSW harvester',
            'description': 'Class for processing USGINXmlMapping into a JSON object'
        }

    
    def contact(self, data):
        return {
            "contactRef": {
                "agentRole": {
                    "conceptPrefLabel":  data.get("role", None),
                    "vocabularyURI":  data.get("role-codespace", None),
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
    # assume voice telephone
    def buildTelephone(self,data):
        return {
            "phoneNumber": data,
            "phoneLabel":"voice"
        }

    #smr responsible party-- an agent in a role
    def buildContactInRole(self, data):
        # data is ISOResponsibleParty class from harvested_metadata.py
        the-contact-address = '"' & \
			data.get("contact-info", None).get("postal-address", None).get("delivery-point", None) & ', ' & \
            data.get("contact-info", None).get("postal-address", None).get("city", None) & ', ' & \
            data.get("contact-info", None).get("postal-address", None).get("administrative-area", None) & ', ' & \
            data.get("contact-info", None).get("postal-address", None).get("postal-code", None) & ', ' & \
            data.get("contact-info", None).get("postal-address", None).get("country", None) & '"'
        # concatenate all the fields into one address string.
        return  {
		"agentRole":{
		"conceptURI":data.get("agentRoleConceptURI", None),
		"conceptPrefLabel":data.get("agentRolePrefLabel", None),
		"vocabularyURI":data.get("agentRoleVocabularyURI", None)
		},
        "agent": {
            "personName": data.get("contact", None).data.get("personName", None),
            "personPosition": data.get("contact", None).data.get("personPosition", None),
            "organizationNames": [data.get("contact", None).data.get("organizationNames", None)],
            # if data.get("contact-info", None).get("telephone-voice", []): 
            "phoneContacts":[ self.buildTelephone(thetel) for thetel in data.get("contact", None).data.get("contact-info", None).get("telephone-voice", [])
                ],
            "contactEmails": [data.get("contact", None).data.get("contact-info", None).get("contactEmails", None)],
            "contactAddress": the-contact-address,   
			"organizationLinks": [data.get("contact", None).data.get("contact-info", None).data.get("contact-link", None)]
			  }
        }

    def buildBboxes(self, data):
		#modify to return multiple bboxes if they exist. target to populate boundingBoxesWGS84
		# in USGIN JSON metadata
		bboxes = []
        for bbox in data.get("bbox", None)
			if bbox:
				bboxes = bboxes.append({
                "eastBoundLongitude": bbox.get("east", ""),
                "northBoundLatitude": bbox.get("north", ""),
                "southBoundLatitude": bbox.get("south", ""),
                "westBoundLongitude": bbox.get("west", "")
            })
		return bboxes

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
			
			#toDo-- need to pull parameters out of description string and put in the linkObject.linkParameters array

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

    def buildDistributions(self, data):
        """
        Each distributor may have multiple digitalTrasferOptions, MD_format, standard order process. 
        if only one distributor is present, links from MD_Distribution to transferOptions and format have to be projected to distributor
        if no distributor provided, create an unknown and associate with the required DigitalTransferOptions linksage
		These distributions correspond to ckan package.resources
        """
		
		
		
        pass  #TODO 
		
	def buildContentInfo(self, data):
	"""
	scan keywords for usgincm: prefix and pull content model name to gmd:contentInfo/gmd:MD_FeatureCatalogDescription/
	gmd:featureTypes genericName, and put link for schema.usgin.org/models/ in the featureCatalogCitation.
	Should probably implement mapping for gmd:contentInfo part of metadata as well...
	Model version goes in citation edition, model URI (namespace URI) goes in citation identifier
	"""
		pass #ToDo
		
	def buildResourceType(self, data):
	"""
	put hierachyLevel/scopeCode, hierachrylevelName, and keywords with usginres: prefix in here as resource types, with appropriate citation tiles for the sources.
	"""
		pass #ToDo
    
    def get_package_dict(self, iso_values, harvest_object):
        """
        This function gets the package dict from spatial/haravester/base.py, and 
        used the USGIN ISO mapping (in usgin_xml_mapper) to construct extras.usginmdpackage
        with USGIN metadata content.
        """

        # First generate exactly the same package dict that the standard harvester would.
        # this executes get_package_dict on CSWHarvester, which is the parent of USGINHarvester
        # CSWHarverster inherits get_package_dict from SpatialHarvester, defined in 
        # ckanext-spatial/ ckanext/spatial/harversters/base.py. 
        # the idea is that everything outside of the extra.usginmd_package is the same as out of
        # the box spatial harvester, so it doesn't break other stuff.
        package_dict = super(USGINHarvester, self).get_package_dict(iso_values, harvest_object)

        # Then lets parse the harvested XML document with a customized NGDS parser; this function
        # is defined in ckanext-metadata/ckanext/usginxml_reader.py
        doc = USGINXmlMapping(xml_str=harvest_object.content)
        values = doc.read_values()

        # pull extras from package_dict created with base.py (harvested_metadata.py)
        extras = package_dict['extras']

        # Published or unpublished
        package_dict['private'] = False



        cited_source_agent = [self.buildRelatedAgent(agent) for agent in values.get('citationResponsibleParties', [])]
        metadata_contact = [self.buildRelatedAgent(agent) for agent in values.get('metadataPointOfContact', [])]
        resource_contact = [self.buildRelatedAgent(agent) for agent in values.get('resource-contact', [])]
		
		#build new handler for distributions; distributors array will have the transferOptions (access_links) and formats 
		# inside, along with distributor contact information
        # distributors = [self.buildRelatedAgent(agent) for agent in values.get('distributor', [])]
        # access_links = [self.buildAccessLink(res) for res in values.get('resource-locator', [])]
  
        # TODO  construct a distributor access options object to put in md_package.  Group on distributors, with a collection of online or offline distributions options associated with each distributor
        
        # this md_package is constructed against USGINMetadataJSONv3.0, 
        # the value dictionary is constructed in usgin_xml_reader.py, should be in the same 
		# directory as this file

        datelist = values.get("dataset-reference-date", "")
        usgin_md_package = {
            "metadataProperties" : {
            	"metadataIdentifier" : values.get("metadataIdentifier", ""),
            	"metadataLastUpdate" : values.get("metadataDate", ""),
            	"metadataContacts" : metadata_contact,
            	"metadataSpecification" : {
            		"referenceLabel" : "USGIN JSON metadata v3.0",
            		"referenceURI" : "http://resources.usgin.org/uri-gin/usgin/schema/json/3.0/metadata"
            	},
            	"parentMetadata" : {
            		"referenceURI" : values.get("metadataParentIdentifier", "")
            	},
            	"metadataMaintenance" : values.get("metadataMaintenance", ""),

            	"metadataLanguage" : {
            		"languageCode" : values.get("metadataLanguageCode", ""),
            		"languageReference" : {
            			"referenceURI" : values.get("metadataLanguageCodeList", ""),

            		}
            	},

            	# this will be filled from metadataRecordLineageItems;
            	# but content is sparse at this point
				
            	"metadataRecordLineageItems" : [],
            	"metadataUsageConstraint" : [values.get("metadataUsageConstraint","")], 
            	"harvestInformation" : {
            		"harvestDate" : "",
            		"harvestedFileIdentifier" : values.get("metadataIdentifiervalues.get("
            		"harvestedMetadataFormat" : {
            			"referenceLabel" : values.get("metadataStandardName", ""),
            			"version" : values.get("metadataStandardVersion", "")
            		},
            		"harvestURL" : "",
            	},
            },
			
			    # have to handle these...
				# "usginContentModel" : "",
            	# "usginContentModelLayer" : "",
            	# "usginContentModelVersion" : "",
            "resourceDescription" : {
            	"resourceTitle" : values.get("title", ""),
            	"resourceAbstract" : values.get("abstract", ""),
            	"citationResponsibleParties" : cited_source_agent,
            	"citationDates" : {
            		"EventDateObject" : {
            			"dateTime" : datelist[0].get("value", "")
            		}
            	},
				"citationAlternateTitles":"",
				"citationRecommendation":"",
				"citationDetails":"",
				"resourceTypes":[],
				"resourceStatus":"",
            	"resourceContacts" : resource_contact,
				"resourceBrowseGraphic":"",
				"resourceTemporalExtents":"",
				"resourceCharacterSet":"",
				"resourceLanguages":[],
				"resourceSpatialExtents":[],
				"resourceSpatialDescription":{},
				"resourceIndexTerms":[],
            	"resourceAccessOptions" : [],
				"resourceLineageItems":[],
				"resourceQualityItems":[],
				"resourceUsageConstraints":[],
				"resourceMaintenance":{},
				"resourcePurpose":"",
				"resourceCredit":"",
				"topicCategory":[],
				"resourceEnvironmentDescription":"",
				"resourceSpecificUsage":[],
				"relatedResources":[],
				"resourceDetails":{
					"dataset":{},
					"service":{}
				}
            },
            }
        usgin_md_package = json.dumps(usgin_md_package)

        extras.append({"key": "md_package", "value": usgin_md_package})

        # When finished, be sure to return the dict
        return package_dict

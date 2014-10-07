from ckanext.spatial.model import ISOElement
from ckanext.spatial.model import ISODocument
from ckanext.spatial.model import ISOResponsibleParty
from ckanext.spatial.model import ISOBoundingBox
from ckanext.spatial.model import ISOKeyword

class NgdsXmlMapping(ISODocument):
    """
    Inherits from ckanext.spatial.model.MappedXmlDocument.
    ckanext.spatial.model.ISODocument is a similar example
    (see https://github.com/ckan/ckanext-spatial/blob/master/ckanext/spatial/model/harvested_metadata.py)

    - Invoke with `my_ngds_mapping = NgdsXmlMapping(xml_str=None, xml_tree=None)`
    - Then get values by `my_ngds_mapping.read_values()`
    """

    elements = [
        ISOElement(
            name="title",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()",
            ],
            multiplicity="1",
        ),
        #file identifier
        ISOElement(
            name="guid",
            search_paths="gmd:fileIdentifier/gco:CharacterString/text()",
            multiplicity="0..1",
        ),
        #resource alternate title
        ISOElement(
            name="alternate-title",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        #abstract--description of resource
        ISOElement(
            name="abstract",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:abstract/gco:CharacterString/text()",
            ],
            multiplicity="1",
        ),
        # geographic bounding box, EX_GeographicBoundingBox object
        ISOBoundingBox(
            name="bbox",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox",
            ],
            multiplicity="*",
        ),
        #keywords; returns gmd:MD_Keywords object
        ISOKeyword(
            name="keywords",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords",
            ],
            multiplicity="*"
        ),
        #metadata date stamp
        ISOElement(
            name="metadata-date",
            search_paths=[
                "gmd:dateStamp/gco:DateTime/text()",
                "gmd:dateStamp/gco:Date/text()",
            ],
            multiplicity="1",
        ),
        #metadata standard name
        ISOElement(
            name="metadata-standard-name",
            search_paths="gmd:metadataStandardName/gco:CharacterString/text()",
            multiplicity="0..1",
        ),
        #metadata standard version
        ISOElement(
            name="metadata-standard-version",
            search_paths="gmd:metadataStandardVersion/gco:CharacterString/text()",
            multiplicity="0..1",
        ),
        # Metadata Maintainer responsible party
        ISOResponsibleParty(
            name="maintainers",
            search_paths=[
                "gmd:contact/gmd:CI_ResponsibleParty"
            ],
            multiplicity="*"
        ),

        # Other ID
        ISOElement(
            name="other_id",
            search_paths="gmd:dataSetURI/gco:CharacterString/text()",
            multiplicity="0..1", # "*", "1..*", "1" are other options
        ),

        # Data Type
        ISOElement(
            name="data_type",
            search_paths="gmd:hierarchyLevelName/gco:CharacterString/text()",
            multiplicity="*", # "*", "1..*", "1" are other options
        ),

        # Pub Date
        ISOElement(
            name="publication_date",
            search_paths="gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:DateTime/text()",
            multiplicity="0..1", # "*", "1..*", "1" are other options
        ),

        # Authors
        ISOResponsibleParty(
            name="authors",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty"
            ],
            multiplicity="*"
        ),

        # Quality <<<  Node that CKAN ISODocument object pulls explanation from gmd:DQ_DomainConsistency
        #   into conformity-explanation. Handler for quality needs to be a complex object like ResponsibleParty
        #   Include in this array of paths the paths for DQ_Elements that seem likely tohave text explanations... [SMR 2014-03-21]
        ISOElement(
            name="quality",
            search_paths=[
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_CompletenessCommission/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_CompletenessOmission/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_ConceptualConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_FormatConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_TopologicalConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_NonQuantitativeAttributeAccuracy/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_ThematicClassificationCorrectness/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_TemporalConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
                "/gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_TemporalValidity/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()"
            ],
            multiplicity="*", # "*", "1..*", "1" are other options
        ),

        # Lineage <<<  Note that the CKAN ISODocument object already defines this. Its not clear why
        #  its defined here as well...
         ISOElement(
             name="lineage",
             search_paths="gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString/text()",
             multiplicity="0..1", # "*", "1..*", "1" are other options
         ),

        # Status  <<< NOte that CKAN ISODocument object harvests this element into 'progress'
        ISOElement(
            name="status",
            search_paths="gmd:identificationInfo/gmd:MD_DataIdentification/gmd:status/gmd:MD_ProgressCode/@codeListValue",
            multiplicity="0..1", # "*", "1..*", "1" are other options
        )
    ]

    def infer_values(self, values):
        return values
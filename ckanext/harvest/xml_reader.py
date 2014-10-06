# Original code by @rclark
from ckanext.spatial.model import ISOElement, ISODocument, ISOResponsibleParty

class NgdsXmlMapping(ISODocument):
    """
    Inherits from ckanext.spatial.model.MappedXmlDocument.
    ckanext.spatial.model.ISODocument is a similar example
    (see https://github.com/ckan/ckanext-spatial/blob/master/ckanext/spatial/model/harvested_metadata.py)

    - Invoke with `my_ngds_mapping = NgdsXmlMapping(xml_str=None, xml_tree=None)`
    - Then get values by `my_ngds_mapping.read_values()`
    """

    elements = [
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
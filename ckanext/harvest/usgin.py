# Original code by @rclark
import json
import re

from ckanext.spatial.harvesters import CSWHarvester
from ckanext.harvest.xml_reader import NgdsXmlMapping

class USGINHarvester(CSWHarvester):
    """
    Inherits from ckanext-spatial's CSW Harvester,
        which inherits from ckanext.spatial.harvesters:SpatialHarvester
        which inherits from ckanext.harvest.harvester:HarvesterBase
    """

    def info(self):
        """Return some information about this particular harvester"""
        return {
            'name': 'ngds',
            'title': 'NGDS CSW Server',
            'description': 'CSW Server offering metadata that conforms to the NGDS ISO Profile'
        }

    def get_package_dict(self, iso_values, harvest_object):
        """
        Override's ckanext.spatial.harvesters.SpatialHarvester.get_package_dict

        This function generates the package dictionary from the harvested object. This package_dict
        will be fed to the `package_create` action.
        """

        # First lets generate exactly the same package dict that the standard harvester would.
        package_dict = super(USGINHarvester, self).get_package_dict(iso_values, harvest_object)

        # Then lets parse the harvested XML document with a customized NGDS parser
        ngds_doc = NgdsXmlMapping(xml_str=harvest_object.content)
        ngds_values = ngds_doc.read_values()

        # Then lets customize the package_dict further
        extras = package_dict['extras']

        # Published or unpublished
        package_dict['private'] = False

        def party2person(party):
            """For converting an ISOResponsibleParty to an NGDS contact"""
            name = ""
            email = ""
            if party.get('individual-name', '') != '':
                name = party.get('individual-name', '')
            else:
                if party.get('organisation-name', '') != '':
                    name = party.get('organisation-name', '')
            if party.get('contact-info', {}):
                email = party.get('contact-info', {}).get('email', '')
            return {
                "name": name,
                "email": email
            }

        # Any otherID
        other_id = {"key": "other_id", "value": json.dumps([ngds_values['other_id']])}
        extras.append(other_id)

        # The data type
        data_type = {"key": "dataset_category", "value": ngds_values['data_type']}
        extras.append(data_type)

        # Pub date
        publication_date = {"key": "publication_date", "value": ngds_values['publication_date']}
        extras.append(publication_date)

        # Maintainers
        maintainers = {
            "key": "maintainers",
            "value": json.dumps([party2person(party) for party in ngds_values.get('maintainers', [])])
        }
        extras.append(maintainers)

        # Authors
        authors = {
            "key": "authors",
            "value": json.dumps([party2person(party) for party in ngds_values.get('authors', [])])
        }
        extras.append(authors)

        # Quality
        quality = {"key": "quality", "value": ngds_values.get('quality', '')}
        extras.append(quality)

        # Lineage
        lineage = {"key": "lineage", "value": ngds_values.get('lineage', '')}
        extras.append(lineage)

        # Status
        status = {"key": "status", "value": ngds_values.get('status', '')}
        extras.append(status)

        # Resources
        layer_expr = re.compile('parameters: (?P<layer_name>{.+})$')
        for res in package_dict.get('resources',[]):
            res['protocol'] = res.get('resource_locator_protocol', '')

            format = res.get('format')
            if format == 'wfs':
                res['protocol'] = 'OGC:WFS'
            elif format == 'wms':
                res['protocol'] = 'OGC:WMS'
            elif format == 'arcgis_rest':
                res['protocol'] = 'ESRI'

            layer_identifier = 'featureTypes' if res['protocol'] == 'OGC:WFS' else 'layers'
            layer_name = layer_expr.search(res.get('description', ''))
            layer_name = layer_name.group('layer_name') if layer_name else '{}'
            layer_name = json.loads(layer_name).get(layer_identifier, '')

            res['layer'] = layer_name

        # When finished, be sure to return the dict
        return package_dict
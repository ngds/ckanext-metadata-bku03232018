import re
import json
import logging
import usginmodels
import os.path as path
from ckanext.metadata.common import config
from ckanext.metadata.common import pylons_i18n
from ckanext.metadata.common import base, logic
from ckanext.metadata.common import helpers as h
from itertools import count
from ckan.lib.navl.dictization_functions import Invalid
from ckan.model import (MAX_TAG_LENGTH, MIN_TAG_LENGTH)

#from ckan.logic import ValidationError
ValidationError = logic.ValidationError
import ckan.lib.navl.dictization_functions as df
StopOnError = df.StopOnError
get_action = logic.get_action
import os


log = logging.getLogger(__name__)

def is_valid_json(key, data, errors, context):
    """
    Checks that a string can be parsed as JSON.

    @param key:
    @param data:
    @param errors:
    @param context:
    @return: None
    """

    try:
        json.loads(data[key])
    except:
        errors[key].append(pylons_i18n._('Must be JSON serializable'))

def is_usgin_valid_data(key, data, errors, context):
    resource_id = data.get(('resources', 0, 'id'), None)

    if resource_id is None:
        return

    resource_name = data.get(('resources', 0, 'name'), None)

    md_resource = None
    for k, v in data.iteritems():
        if k[0] == 'resources' and k[-1] == 'md_resource':
            query_key = k
            md_resource = json.loads(data.get(query_key, None))

    md_package = None
    for k, v in data.iteritems():
        if k[0] == 'extras' and v == 'md_package':
            query_key = (k[0], k[1], 'value')
            md_package = json.loads(data.get(query_key, None))

    resourceDescription = md_package.get('resourceDescription', {})
    uri = resourceDescription.get('usginContentModel', None)
    version = resourceDescription.get('usginContentModelVersion', None)
    layer = resourceDescription.get('usginContentModelLayer', None)

    if None in [uri, version, layer]:
        return

    def get_file_path(res_id):
        dir_1 = res_id[0:3]
        dir_2 = res_id[3:6]
        file = res_id[6:]
        storage_base = config.get('ckan.storage_path', 'default')
        return path.join(storage_base, 'resources', dir_1, dir_2, file)

    validation_msg = []
    csv_file = get_file_path(resource_id)

    if csv_file:
        log.info("Filename full path: %s " % csv_file)
    else:
        msg = base._("Cannot find the full path of the resources from %s"\
            % resource_name)
        validation_msg.append({
            'row': 0,
            'col': 0,
            'errorType': 'systemError',
            'message': msg
        })

    if 'none' in [uri.lower(), version.lower(), layer.lower()]:
        log.debug("Start USGIN content model validation")
        log.debug("USGIN tier 2 data model/version/layer are none")
        return {'valid': True}
    else:
	try:
	    # Valid intialization to resove this issue:
            # Error - <type 'exceptions.UnboundLocalError'>: local variable 'valid' referenced before assignment
            valid = False

            csv = open(csv_file, 'rbU')
	    valid, messages, dataCorrected, long_fields, srs = usginmodels.validate_file(csv, version, layer)
        except:
            log.info("The given format's file is not a CSV")
	    os.remove(csv_file)
	    get_action('resource_delete')(context, {'id': resource_id})
	    errors[key].append(base._("The given format's file is not a CSV"))
	    #raise ValidationError(errors)
	    #raise StopOnError

        log.debug("Finished USGIN content model validation")

	if valid and messages:
            log.debug('With changes the USGIN document will be valid')
            h.flash_error(base._('With changes the USGIN document will be valid'))
        elif valid and not messages:
            log.debug("USGIN document is valid")
        else:
            log.debug('USGIN document is not valid')
            h.flash_error(base._('The USGIN document is not valid'))

def ngds_tag_name_validator(value, context):

    tagname_match = re.compile('[\w \-.:]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise Invalid(_('Tag "%s" must be alphanumeric characters or symbols: -_.:') % (value))
    return value

def ngds_tag_string_convert(key, data, errors, context):
    '''Takes a list of tags that is a comma-separated string (in data[key])
    and parses tag names. These are added to the data dict, enumerated. They
    are also validated.'''

    if isinstance(data[key], basestring):
        tags = [tag.strip() \
                for tag in data[key].split(',') \
                if tag.strip()]
    else:
        tags = data[key]

    current_index = max( [int(k[1]) for k in data.keys() if len(k) == 3 and k[0] == 'tags'] + [-1] )

    for num, tag in zip(count(current_index+1), tags):
        data[('tags', num, 'name')] = tag

    for tag in tags:
        ngds_tag_length_validator(tag, context)
        ngds_tag_name_validator(tag, context)

def ngds_tag_length_validator(value, context):

    if len(value) < MIN_TAG_LENGTH:
        raise Invalid(('Tag "%s" length is less than minimum %s') % (value, MIN_TAG_LENGTH))
    if len(value) > MAX_TAG_LENGTH:
        raise Invalid(('Tag "%s" length is more than maximum %i') % (value, MAX_TAG_LENGTH))
    return value

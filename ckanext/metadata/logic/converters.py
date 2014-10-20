def convert_to_md_package_extras(key, data, errors, context):
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    extras.append({'key': key[-1], 'value': data[key]})

def convert_to_md_resource_extras(key, data, errors, context):
    extras = data.get(('__extras',), {})
    if not extras:
        data[('__extras',)] = extras
    md_key = key[-1]
    md_data = data[key]
    extras[md_key] = md_data
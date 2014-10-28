### ckanext-metadata
CKAN extension that provides interfaces for creating, editing, harvesting and searching based on USGIN compliant 
ISO metadata standards.

#### Dependencies
* CKAN v2.3

#### Installation
```
$ git clone https://github.com/ngds/ckanext-metadata.git
$ cd ckanext-metadata
$ pip install -r requirements.txt

# If you're installing for development:
$ python setup.py develop

# If you're installing for production:
$ python setup.py build
$ python setup.py install

# Enable extension by adding ckanext-metadata plugins to ckan.plugins
nano ../path/to/ckan/configuration.ini
ckan.plugins = ... ... usgin_metadata usgin_harvester usgin_facets
```

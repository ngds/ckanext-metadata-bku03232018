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

### Run Tests

This extension has 3 subpackages (facets, harvest and metadata). However the instructions below, applied for all of them).

#### Step 1
Before running tests, there are 2 configs files for test, need to be configured regarding the test environment of your machine:
- ckanext-metadata/ckanext/facets_or_harvest_or_metadata/test.ini: overrides ckan environment.ini variables or you can point it into a different environment.ini (e.g: use different database for test)
- ckanext-metadata/ckanext/facets_or_harvest_or_metadata/tests/tests_config.cfg:
> ckan_host: by default, CKAN Host on your machine
> sample_file_path: by default, path to test data "xml format" (Dataset).
> ckan_metadata_iso_19139_path: by default, URI to generate dataset into XML.
> data_test_dataset: by default, path to test data "json format" (Dataset).
> data_test_resource: by default, path to test data "json format" (Resource).

#### Step 2
Command line to perform the tests:

```
$ cd ckanext-metadata/ckanext/facets_or_harvest_or_metadata/
$ nosetests --ckan --with-pylons=test.ini tests/
```
- --with-pylons it's an option to specify the path to environment.ini to use for the test (override ckan default ini).
- tests/ it's the path to all tests files where located

#### Note
Before testing metadata: ckanext-metadata/ckanext/metadata/, your ckan environment on your machine has to point to the same database that you're going to use in ckanext-metadata/ckanext/metadata/test.ini.
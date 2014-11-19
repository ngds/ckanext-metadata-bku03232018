########################
###### IMPORTANT #######
# Before running this test, make sure CKAN is using
# test database (same as defined in ckanext-metadata/ckanext/metadata/test.ini)
########################

import ckan.tests as tests
import ckan.model as model
import paste.fixture
import pylons.test

import ConfigParser
import os
import requests

class TestMetadataAction(object):

    #setup_class executes (auto once) before anything in this class
    @classmethod
    def setup_class(self):
        print ("")

        # get config options
        config = ConfigParser.RawConfigParser({
            'ckan_host': '0.0.0.0',
        })
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'tests_config.cfg'))

        self.host = config.get('tests', 'ckan_host')
        self.path = config.get('tests', 'ckan_metadata_iso_19139_path')

        if not self.host:
            raise Exception('You must add a Host to the tests '
                            ' configuration file')

        if not self.path:
            raise Exception('You must add metadata iso-19139 path to the tests '
                            ' configuration file')

        # Make the Paste TestApp that we'll use to simulate HTTP requests to CKAN.
        self.app = paste.fixture.TestApp(pylons.test.pylonsapp)

        # Access CKAN's model directly (bad) to create a sysadmin user and save
        # it against self for all test methods to access.
        self.sysadmin_user = model.User(name='test_sysadmin', sysadmin=True)
        model.Session.add(self.sysadmin_user)
        model.Session.commit()
        model.Session.remove()

        #Create organization
        organization = {'name': 'test_org',
                        'title': 'Africa - Maroc',
                        'description': 'Maroc in north Africa.'}

        self.organization = tests.call_action_api(self.app, 'organization_create', apikey=self.sysadmin_user.apikey, **organization)

        #Create Dataset and tied it to created org
        dataset = {'name': 'test_org_dataset_md',
                   'title': 'Africa - Maroc: Beautiful country for tourist',
                   'owner_org': organization['name'],
                   'md_package': "{\"harvestInformation\":{\"crawlDate\":\"\",\"harvestURL\":\"\",\"indexDate\":\"\",\"originalFileIdentifier\":\"\",\"originalFormat\":\"\",\"version\":\"\",\"sourceInfo\":{\"harvestSourceID\":\"\",\"harvestSourceName\":\"\",\"viewID\":\"\"}},\"metadataProperties\":{\"metadataContact\":{\"relatedAgent\":{\"agentRole\":{\"agentRoleLabel\":\"\",\"agentRoleURI\":\"\",\"contactAddress\":\"\",\"contactEmail\":\"\",\"organizationName\":\"\",\"organizationURI\":\"\",\"phoneNumber\":\"\",\"individual\":{\"personName\":\"\",\"personPosition\":\"\",\"personURI\":\"\"}}}}},\"resourceDescription\":{\"citationDates\":{\"EventDateObject\":{\"dateTime\":\"2014-1-1\"}},\"resourceDescription\":\"Creating a new account\",\"resourceTitle\":\"Creating a new account\",\"citedSourceAgents\":[{\"relatedAgent\":{\"agentRole\":{\"individual\":{\"personName\":\"teste\",\"personPosition\":\"teste\"},\"organizationName\":\"teste\",\"phoneNumber\":\"teste\",\"contactEmail\":\"teste\",\"contactAddress\":\"teste\"}}},{\"relatedAgent\":{\"agentRole\":{\"individual\":{\"personName\":\"\",\"personPosition\":\"\"},\"organizationName\":\"\",\"phoneNumber\":\"\",\"contactEmail\":\"\",\"contactAddress\":\"\"}}}],\"resourceContact\":[{\"relatedAgent\":{\"agentRole\":{\"individual\":{\"personName\":\"meta data teste\",\"personPosition\":\"meta data teste\"},\"organizationName\":\"meta data teste\",\"phoneNumber\":\"meta data teste\",\"contactEmail\":\"meta data teste\",\"contactAddress\":\"meta data teste\"}}}],\"geographicExtent\":[{\"northBoundLatitude\":44,\"southBoundLatitude\":-44,\"eastBoundLongitude\":24,\"westBoundLongitude\":33}]}}"}

        self.dataset = tests.call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey, **dataset)

        #Create Resource and tied it to created dataset
        resource = {'package_id': self.dataset['id'], 'url': 'http://teste.teste', 'md_resource': "{\"distributors\":[{\"relatedAgent\":{\"agentRole\":{\"individual\":{\"personName\":\"\",\"personPosition\":\"\"},\"organizationName\":\"\",\"phoneNumber\":\"\",\"contactEmail\":\"\",\"contactAddress\":\"\"}}}],\"accessLink\":{\"LinkObject\":{\"linkDescription\":\"teste\",\"linkTitle\":\"test\"}}}"}

        self.resource = tests.call_action_api(self.app, 'resource_create', apikey=self.sysadmin_user.apikey, **resource)

    #teardown_class executes (auto once) after anything in this class
    @classmethod
    def teardown_class(self):
        print ("")

        #Delete Resource created for test
        tests.call_action_api(self.app, 'resource_delete', apikey=self.sysadmin_user.apikey, **{'id': self.resource['id']})

        #Delete Dataset created for test
        tests.call_action_api(self.app, 'package_delete', apikey=self.sysadmin_user.apikey, **{'id': self.dataset['id']})

        #delete organization created
        tests.call_action_api(self.app, 'organization_delete', apikey=self.sysadmin_user.apikey, **{'id': self.organization['id']})

        self.app = None
        self.sysadmin_user = None
        self.dataset = None
        self.organization = None
        self.resource = None
        self.path = None
        self.host = None
        del self.app
        del self.sysadmin_user
        del self.dataset
        del self.organization
        del self.resource
        del self.host
        del self.path

    #setup executes before each method in this class
    def setup(self):
        print ("")
        print ("TestUM:setup() before each test method")

    #setup executes after each method in this class
    def teardown(self):
        print ("")
        print ("TestUM:teardown() after each test method")

    #Test data xml package after schema been overriden
    def test_dataPackageSchemaXML(self):
        print "test_dataPackageSchemaXML(): Running actual test code .........................."

        try:
            oResponse = requests.head("http://%s/%s/%s.xml" % (self.host, self.path, self.dataset['id']))
            assert oResponse.status_code == 200

        except requests.ConnectionError:
            print "failed to connect"
            assert False

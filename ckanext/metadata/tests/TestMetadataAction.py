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
import json
import uuid

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
        dataTestDataset = config.get('tests', 'data_test_dataset')
        dataTestResource = config.get('tests', 'data_test_resource')

        if not self.host:
            raise Exception('You must add a Host to the tests '
                            ' configuration file')

        if not self.path:
            raise Exception('You must add metadata iso-19139 path to the tests '
                            ' configuration file')

        if not dataTestDataset:
            raise Exception('You must add dataset data path to the tests '
                            ' configuration file')

        if not dataTestResource:
            raise Exception('You must add dataset data path to the tests '
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


        sampleDatasetFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), dataTestDataset)

        if not os.path.exists(sampleDatasetFile):
            raise Exception('The file %s not found' % sampleDatasetFile)

        with open(sampleDatasetFile, 'rb') as content_file:
            self.contentDataset = content_file.read()

        self.contentDataset = json.loads(self.contentDataset)

        #Create Dataset and tied it to created org
        self.contentDataset['owner_org'] = organization['name']

        self.dataset = tests.call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey, **self.contentDataset)

        #Create Resource and tied it to created dataset
        sampleResourceFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), dataTestResource)

        if not os.path.exists(sampleResourceFile):
            raise Exception('The file %s not found' % sampleResourceFile)

        with open(sampleResourceFile, 'rb') as content_file:
            self.contentResource = content_file.read()

        self.contentResource = json.loads(self.contentResource)
        self.contentResource['package_id'] = self.dataset['id']

        self.resource = tests.call_action_api(self.app, 'resource_create', apikey=self.sysadmin_user.apikey, **self.contentResource)

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

    #Test bad data xml package not exist
    def testBad_dataPackageSchemaXML(self):
        print "testBad_dataPackageSchemaXML(): Running actual test code .........................."

        try:
            oResponse = requests.head("http://%s/%s/%s.xml" % (self.host, self.path, str(uuid.uuid4())))
            assert oResponse.status_code == 404

        except requests.ConnectionError:
            print "failed to connect"
            assert False

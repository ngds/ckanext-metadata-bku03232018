import ckanext.metadata.plugin as metadataPlugin
import ckanext.metadata.logic.action as action
import ckanext.metadata.helpers as helper
import ckanext.metadata.logic.converters as converters
from ckanext.metadata.common import logic

import ckan.tests as tests
import ckan.model as model
import paste.fixture
import pylons.test

get_action = logic.get_action

class TestMetadataPlugin(object):

    #setup_class executes (auto once) before anything in this class
    @classmethod
    def setup_class(self):
        print ("")

        self.oMetadataPlugin = metadataPlugin.MetadataPlugin()

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
        dataset = {'name': 'test_org_dataset_mapsearch',
                   'title': 'Africa - Maroc: Beautiful country for tourist',
                   'owner_org': organization['name'],
                   'md_package': ""}

        self.dataset = tests.call_action_api(self.app, 'package_create', apikey=self.sysadmin_user.apikey, **dataset)

        #Create Resource and tied it to created dataset
        resource = {'package_id': self.dataset['id'], 'url': 'http://teste.teste', 'md_resource': ""}

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

        self.oMetadataPlugin = None
        self.app = None
        self.sysadmin_user = None
        self.dataset = None
        self.organization = None
        self.resource = None
        del self.oMetadataPlugin
        del self.app
        del self.sysadmin_user
        del self.dataset
        del self.organization
        del self.resource

    #setup executes before each method in this class
    def setup(self):
        print ("")
        print ("TestUM:setup() before each test method")

    #setup executes after each method in this class
    def teardown(self):
        print ("")
        print ("TestUM:teardown() after each test method")

    #Test get_actions method
    def test_getActions(self):
        print 'test_getActions(): Running actual test code ..........................'

        result = self.oMetadataPlugin.get_actions()
        listMethods = dir(action)

        for name in result:
            assert name in listMethods

    #Test get_actions method
    def test_getHelpers(self):
        print 'test_getHelpers(): Running actual test code ..........................'

        result = self.oMetadataPlugin.get_helpers()
        listMethods = dir(helper)

        for name in result:
            assert name in listMethods

    #Test create_package_schema, update_package_schema and show_package_schema and show_package_schema methods
    # (both are the same)
    def test_packageSchema(self):
        print "test_packageSchema(): Running actual test code .........................."

        result = self.oMetadataPlugin.create_package_schema()
        #All the same
        #result = self.oMetadataPlugin.update_package_schema()
        #result = self.oMetadataPlugin.show_package_schema()

        assert 'md_package' in result
        assert 'md_resource' in result['resources']

        assert result['md_package'][1].__name__ in dir(converters)
        assert result['resources']['md_resource'][1].__name__ in dir(converters)

    #Test data package after been overriden
    def test_dataPackageSchema(self):
        print "test_dataPackageSchema(): Running actual test code .........................."

        context = {'model': model,
                   'session': model.Session,
                   'user': self.sysadmin_user.name}

        resourceDict = get_action('resource_show')(context, {'id': self.resource['id']})
        datasetDict = get_action('package_show')(context, {'id': self.dataset['id']})

        assert 'md_resource' in resourceDict
        assert 'md_package' in datasetDict['extras'][0]['key']

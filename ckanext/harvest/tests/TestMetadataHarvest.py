import paste.fixture
import pylons.test
import os
import ConfigParser
import ckan.model as model
from ckan.plugins import toolkit
from ckan.lib.base import config
from ckan.logic import get_action

from ckanext.harvest.model import (setup as harvest_model, HarvestSource, HarvestJob, HarvestObject, setup)

from ckanext.spatial.harvesters.csw import CSWHarvester

from ckan.logic.schema import default_update_package_schema

import pprint

class TestMetadataHarvest(object):

    #setup_class executes (auto once) before anything in this class
    @classmethod
    def setup_class(self):
        print ("")

        harvest_model()

        # Make the Paste TestApp that we'll use to simulate HTTP requests to CKAN.
        self.app = paste.fixture.TestApp(pylons.test.pylonsapp)

        # get config options
        config = ConfigParser.RawConfigParser({
            'ckan_host': '0.0.0.0',
        })
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'tests_config.cfg'))

        self.SampleDatasetFile = config.get('tests', 'sample_file_path')

        if not self.SampleDatasetFile:
            raise Exception('You must add the sample xml path to the tests '
                            ' configuration file')

        sampleDatasetFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.SampleDatasetFile)

        if not os.path.exists(sampleDatasetFile):
            raise Exception('The file %s not found' % sampleDatasetFile)

        with open(sampleDatasetFile, 'rb') as content_file:
            contentDataset = content_file.read()

        self.contentDataset = contentDataset

    #teardown_class executes (auto once) after anything in this class
    @classmethod
    def teardown_class(self):
        print ("")

        model.repo.rebuild_db()

        self.app = None
        self.contentDataset = None
        self.SampleDatasetFile = None

        del self.app
        del self.contentDataset
        del self.SampleDatasetFile

    #setup executes before each method in this class
    #Create harvest object
    def setup(self):
        print ("")
        print ("TestUM:setup() before each test method")

        # Add sysadmin user
        self.harvestUser = model.User(name=u'harvest', password=u'test', sysadmin=True)
        model.Session.add(self.harvestUser)
        model.Session.commit()

        source_fixture = {
            'title': 'Test Source',
            'name': 'test-source',
            'url': u'xml/sample.xml',
            'source_type': u'ngds'
        }

        context = {
            'model': model,
            'session': model.Session,
            'user': u'harvest'
        }

        if config.get('ckan.harvest.auth.profile') == u'publisher' \
           and not 'publisher_id' in source_fixture:
           source_fixture['publisher_id'] = self.publisher.id

        source_dict=get_action('harvest_source_create')(context, source_fixture)
        self.oHarvestSource = HarvestSource.get(source_dict['id'])

        job_dict=get_action('harvest_job_create')(context,{'source_id': self.oHarvestSource.id})
        self.oHarvestJob = HarvestJob.get(job_dict['id'])

        context = {
            'model' : model,
            'session': model.Session,
            'ignore_auth': True,
        }

        data_dict = {
            'guid' : 'guid',
            'content' : self.contentDataset,
            'job_id' : self.oHarvestJob.id,
            'extras' : { 'a key' : 'a value' },
        }

        oHarvestObject = toolkit.get_action('harvest_object_create')(context, data_dict)
        self.oHarvestObject = HarvestObject.get(oHarvestObject['id'])

        package_schema = default_update_package_schema()
        self.context = {
            'model':model,
            'session': model.Session,
            'user':u'harvest',
            'schema':package_schema,
            'api_version': '2'
        }

    #setup executes after each method in this class
    def teardown(self):
        print ("")
        print ("TestUM:teardown() after each test method")

    #Test data xml package after schema been overriden
    def test_metadataHarvest(self):
        print "test_metadataHarvest(): Running actual test code .........................."

        harvester = CSWHarvester()

        result = harvester.import_stage(self.oHarvestObject)

        assert result is True

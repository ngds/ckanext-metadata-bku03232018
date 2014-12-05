import ckanext.metadata.helpers as metadataHelper

import pprint

class TestMetadataHelpers(object):

    #setup_class executes (auto once) before anything in this class
    @classmethod
    def setup_class(self):
        print ("")

        #create test data
        self.testData = {
            'individual': {
                'personName': 'Nicola Pipo',
                'personPosition': 'Software Engineer',
            },
            'organizationName': 'Company LLC',
            'contactAddress': 'VA',
            'phoneNumber': '703-xxx-xxxx',
            'contactEmail': 'nicola.pipo@companyllc.com',
            'originalFileIdentifier': 'x8asf7v7zx9c0-xxzc',
            'northBoundLatitude': 120.00,
            'southBoundLatitude': 130.33,
            'eastBoundLongitude': 100.07,
            'westBoundLongitude': 87.98
        }

        #create bad test data
        self.testDataBad = {
            'individual': {
            }
        }

    #teardown_class executes (auto once) after anything in this class
    @classmethod
    def teardown_class(self):
        print ("")


    #setup executes before each method in this class
    def setup(self):
        print ("")
        print ("TestUM:setup() before each test method")

    #setup executes after each method in this class
    def teardown(self):
        print ("")
        print ("TestUM:teardown() after each test method")

    #Test make_author method
    def test_getMakeAuthor(self):
        print 'test_getMakeAuthor(): Running actual test code ..........................'

        result = metadataHelper.make_author(self.testData)

        assert result['Name'] == self.testData['individual']['personName']
        assert result['Position'] == self.testData['individual']['personPosition']
        assert result['Organization'] == self.testData['organizationName']
        assert result['Address'] == self.testData['contactAddress']
        assert result['Phone'] == self.testData['phoneNumber']
        assert result['Email'] == self.testData['contactEmail']

    #Test bad make_author method
    def testBad_getMakeAuthor(self):
        print 'testBad_getMakeAuthor(): Running actual test code ..........................'

        try:
            result = metadataHelper.make_author(self.testDataBad)
	    assert result is False
        except:
            print "Important parameters are missing."
            pass

    #Test check_harvest_info method
    def test_checkHarvestInfo(self):
        print 'test_checkHarvestInfo(): Running actual test code ..........................'
        result = metadataHelper.check_harvest_info(self.testData)
        assert result is True

    #Test Bad check_harvest_info method
    def testBad_checkHarvestInfo(self):
        print 'testBad_checkHarvestInfo(): Running actual test code ..........................'
        try:
            result = metadataHelper.check_harvest_info(self.testDataBad)
	    assert result is False
        except:
            print "Important parameters are missing."
            pass

    #Test check_author method
    def test_checkAuthor(self):
        print 'test_checkAuthor(): Running actual test code ..........................'
        data = metadataHelper.make_author(self.testData)
        result = metadataHelper.check_author(data)
        assert result is True

    #Test Bad check_author method
    def testBad_checkAuthor(self):
        print 'testBad_checkAuthor(): Running actual test code ..........................'
        try:
            data = metadataHelper.make_author(self.testDataBad)
            result = metadataHelper.check_author(data)

	    assert result is False
        except:
            print "Important parameters are missing."
            pass

    #Test check_author method
    def test_checkGeoExt(self):
        result = metadataHelper.check_geo_ext(self.testData)
        assert result is True

    #Test Bad check_author method
    def testBad_checkGeoExt(self):
        try:
            result = metadataHelper.check_geo_ext(self.testDataBad)
            assert result is False
        except:
            print "Important parameters are missing."
            pass

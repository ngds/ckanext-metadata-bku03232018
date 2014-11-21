import ckanext.facets.plugin as plugin
from pylons import config
import ckan.lib.search as search

class TestMetadataFacet(object):

    #setup_class executes (auto once) before anything in this class
    @classmethod
    def setup_class(self):
        print ("")

        if not search.is_available():
            raise Exception('Solr not reachable')

        self.solr_client = search.make_connection()

        self.fq = " +site_id:\"%s\" +md_author_names:[* TO *] +md_content_models:[* TO *] +md_organization_names:[* TO *] +res_format:[* TO *] " % config['ckan.site_id']

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

    #Test Metadata Facet methods (dataset_facets, organization_facets)
    def test_metadataFacets(self):
        print "test_metadataFacetIsLoaded(): Running actual test code .........................."

        result = plugin.FacetsPlugin().dataset_facets({}, 'regular')

        assert 'md_author_names' in result
        assert 'md_content_models' in result
        assert 'md_organization_names' in result
        assert 'res_format' in result

        result = plugin.FacetsPlugin().organization_facets({}, {}, 'regular')

        assert 'md_author_names' in result
        assert 'md_content_models' in result
        assert 'md_organization_names' in result
        assert 'res_format' in result

    #Test plugin facets fields if exist in indexed package in solr
    def test_searchSolrPackage(self):
        print "test_searchSolrPackage(): Running actual test code .........................."

        response = self.solr_client.query('name:*', fq=self.fq, rows=1)

        assert 'md_author_names' in response.results[0]
        assert 'md_content_models' in response.results[0]
        assert 'md_organization_names' in response.results[0]
        assert 'res_format' in response.results[0]

import sys, os, copy
from flask_testing import TestCase
import httpretty
import json
from collections import defaultdict
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__),'../../'))
sys.path.append(PROJECT_HOME)
import requests
from vis_services import app
from vis_services.lib import word_cloud
from vis_services.lib import author_network
from vis_services.lib import paper_network
from vis_services.lib import tf_idf
import logging


log_directory = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_directory, exist_ok=True)

file_handler = logging.FileHandler(os.path.join(log_directory, 'logfile.log'))
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
#input data

STUBDATA_DIR = PROJECT_HOME + "/vis_services/tests/stubdata"
# has fewer than 50 nodes
input_js_author_network_small = json.load(open(STUBDATA_DIR + "/test_input/author_network_before_groups_func_small.json"))
input_js_data_parameter = json.load(open(STUBDATA_DIR + "/test_input/author_network_second_parameter.json"))
input_js_paper_network = json.load(open(STUBDATA_DIR + "/test_input/paper_network_before_groups_func_large.json"))


#result data

test_js_author_network = json.load(open(STUBDATA_DIR + "/test_output/author_network_accomazzi,a.json"))
test_js_author_network_max_groups = json.load(open(STUBDATA_DIR + "/test_output/author_network_accomazzi,a_max_groups_3.json"))
test_js_author_network_alberto = json.load(open(STUBDATA_DIR + "/test_input/kurtz_query.json"))

class TestEndpointLogic(TestCase):
    
    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    def test_word_cloud_resource(self):
        text1 = "This is a sentence. And this is another sentence (although less important). I bought a car at http://www.car.com."
        text2 = "Testing is good! href='#three' 2.3e2 + 4 = $\\alpha$"
        records = [text1, text2]
        word_cloud_json = word_cloud.generate_wordcloud(records, n_most_common = 100, accepted_pos = ('NN', 'NNP', 'NNS', 'NNPS',))
        expected_word_cloud_json = {'car': {'idf': 0.3010299956639812,
                                      'record_count': 1,
                                      'total_occurrences': 1},
                                     'sentence': {'idf': 0.22184874961635634,
                                      'record_count': 2,
                                      'total_occurrences': 1},
                                     'testing': {'idf': 0.3010299956639812,
                                      'record_count': 1,
                                      'total_occurrences': 1}}
        self.assertEqual(word_cloud_json, expected_word_cloud_json)

    def test_author_network_resource(self):

        #current default
        max_groups = 8
        self.maxDiff = None


        #testing group aggregation function
        #if it receives fewer than 50 nodes, it should just return the graph in the form {fullgraph : graph}

        processed_data_small = author_network.augment_graph_data(input_js_author_network_small, input_js_data_parameter)

        self.assertNotIn("summaryGraph", processed_data_small)

        # otherwise, it should return json containing three items :
        # bibcode_dict, root (d3 structured data), and link_data

        input_js_author_network = json.load(open(STUBDATA_DIR + "/test_input/author_network_before_groups_func_large.json"))

        processed_data = author_network.augment_graph_data(input_js_author_network, input_js_data_parameter)

        self.assertTrue("bibcode_dict" in processed_data)
        self.assertTrue("root" in processed_data)
        self.assertTrue("link_data" in processed_data)

        # testing entire function

        processed_data = json.loads(json.dumps(author_network.augment_graph_data(input_js_author_network, input_js_data_parameter), sort_keys=True))

        self.assertEqual(processed_data, test_js_author_network)
        
    def test_paper_network_resource(self):

        #first, test the tf-idf library

        self.maxDiff = None

        input_js_tf_idf = json.load(open(STUBDATA_DIR + "/test_input/tf_idf_input.json"))

        test_js_tf_idf = json.load(open(STUBDATA_DIR + "/test_output/tf_idf_output.json"))

        processed_data = json.loads(json.dumps(tf_idf.get_tf_idf_vals(input_js_tf_idf), sort_keys=True))

        self.assertEqual(processed_data, test_js_tf_idf)
        
        #now test reference counting function

        processed_data = json.loads(json.dumps(paper_network.get_papernetwork(input_js_paper_network["response"]["docs"], 10), sort_keys=True))

        topCommonReferences = list(processed_data["summaryGraph"]["nodes"][0]["top_common_references"].items()).sort()

        def get_group_references(group):
            indexes =[i for i,n in enumerate(processed_data["fullGraph"]["nodes"]) if n["group"] == group]
            links =[l for l in processed_data["fullGraph"]["links"] if l["source"] in indexes and l["target"] in indexes]
            freq_dict = defaultdict(list)
            for l in links:
                for o in l["overlap"]:
                    freq_dict[o].extend([l["source"], l["target"]])

            for f in freq_dict:
                freq_dict[f] = len(list(set(freq_dict[f])))

            final = sorted(list(freq_dict.items()), key=lambda x:x[1], reverse=True)[:5]

            num_papers = processed_data["summaryGraph"]["nodes"][0]["paper_count"]

            final = [(f[0], f[1]/float(num_papers)) for f in final].sort()
            return final

        self.assertEqual(topCommonReferences, get_group_references(0))

        # now just test input/output

        test_js_paper_network =  json.load(open(STUBDATA_DIR + "/test_output/paper_network_star.json"))
        processed_data = json.loads(json.dumps(paper_network.get_papernetwork(input_js_paper_network["response"]["docs"], 10), sort_keys=True))

        self.assertEqual(sorted(processed_data), sorted(test_js_paper_network))

class TestAppLogic(TestCase):
    
    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app(**{
            'FOO': ['bar', {}],
            'SERVICE_TOKEN': 'secret_token',
               })            

        return app_
    
    def test_solr_client(self):
        from vis_services.client import client,Client
        
        cl = client()
        # Check whether the client is an instance of the correct type
        self.assertIsInstance(cl, Client)

    def test_author_helper_functions(self):
        import vis_services.lib.author_network as AN
        # test the author weight
        # an empty list should return 0
        res = AN._get_author_weight([])
        self.assertEqual(res, 0)
        # a non-empty list of length N should return 1/N
        res = AN._get_author_weight(['a','b'])
        self.assertEqual(res, 0.5)
        # The dictionary remap function should remap the following dictionary
        test_dict = {'a': 10, 'b': 10}
        # into
        expected = {'a': 1.0, 'b': 1.0}
        res = AN._remap_dict_in_range(test_dict)
        self.assertEqual(res, expected)
        # Calling the main author network creation routine with an empty author list
        # should return an empty dictionary
        res = AN.get_network_with_groups([], {})
        self.assertEqual(res, {})
        # With current settings, the stub data should result in 6 children
        input_js_author_network = json.load(open(STUBDATA_DIR + "/test_input/author_network_before_groups_func_large.json"))
        processed_data = AN.augment_graph_data(input_js_author_network, input_js_data_parameter)
        self.assertEqual(len(processed_data['root']['children']), 6)
        # When we set the max_num_auth_nodes parameter to 10, this number should be 1
        AN.max_num_auth_nodes = 10        
        processed_data = AN.augment_graph_data(input_js_author_network, input_js_data_parameter)
        self.assertEqual(len(processed_data['root']['children']), 1)
        # Now test the main network building routine
        author_norm = [['Accomazzi, A', 'Henneken, E'],  ['Accomazzi, A', 'Henneken, E', 'Kurtz, M']]
        author_network_json = author_network.get_network_with_groups(author_norm, input_js_data_parameter)
        expected = {'fullGraph': 
                        {'nodes': [
                            {'nodeName': 'Accomazzi, A', 'nodeWeight': 150.0},
                            {'nodeName': 'Henneken, E', 'nodeWeight': 150.0}, 
                            {'nodeName': 'Kurtz, M', 'nodeWeight': 5.0}
                        ],
                         
                         'links': [
                             {'source': 0, 'target': 2, 'value': 1.0},
                             {'source': 1, 'target': 2, 'value': 1.0},
                             {'source': 0, 'target': 1, 'value': 40.0}
                         ]
                        }
                    }


        self.maxDiff = None
        self.assertEqual(author_network_json, expected)
        
        # Now if we set the maximum number of links with the same weight to 1, one of the links should disappear
        AN.max_num_links_same_weight = 1
        author_network_json = author_network.get_network_with_groups(author_norm, input_js_data_parameter)
        self.assertEqual(len([l for l in author_network_json['fullGraph']['links'] if l['value'] == 1.0]), 1)

    def test_paper_helper_functions(self):
        import vis_services.lib.paper_network as PN
        # Check that the 'get_paper_data' function returns a bibcode-keyed data dictionary
        data = [{'bibcode':'a','title':'foo'}, {'bibcode':'b','title':'bar'}]
        res = PN._get_paper_data(data)
        expected = {'a': {'bibcode': 'a', 'title': 'foo'}, 'b': {'bibcode': 'b', 'title': 'bar'}}
        self.assertEqual(res, expected)
        # A result dictionary with less that 'cutoff' entries should be returned untouched
        test_dict = {'a':1.0, 'b':0.75, 'c':3.3}
        res = PN._sort_and_cut_results(test_dict,cutoff=3)
        self.assertEqual(res, test_dict)
        # Now lower the cutoff
        res = PN._sort_and_cut_results(test_dict,cutoff=2)
        expected = {'a': 1.0, 'c': 3.3}
        self.assertEqual(res, expected)
        # Augmenting graph data for a small network should return just the full graph
        nodeA = {'nodeName':'A',
                 'nodeWeight':1,
                 'citation_count':0,
                 'read_count':0,
                 'title':'title',
                 'year':'NA',
                 'first_author':'NA'
                }
        nodeB = {'nodeName':'B',
                 'nodeWeight':1,
                 'citation_count':0,
                 'read_count':0,
                 'title':'title',
                 'year':'NA',
                 'first_author':'NA'
                }
        linkA = {'source': 'A', 'target': 'A', 'value':1, 'overlap':['C']}
        paper_network =  json.load(open(STUBDATA_DIR + "/test_output/paper_network_star.json"))
        small_network = {'nodes': [nodeA, nodeB], 'links': [linkA]}
        res = PN.augment_graph_data(small_network, 10)
        expected = {'fullGraph': {'nodes': [{'read_count': 0, 'nodeName': 'A', 'title': 'title', 'first_author': 'NA', 'citation_count': 0, 'year': 'NA', 'nodeWeight': 1}, {'read_count': 0, 'nodeName': 'B', 'title': 'title', 'first_author': 'NA', 'citation_count': 0, 'year': 'NA', 'nodeWeight': 1}], 'links': [{'source': 'A', 'target': 'A', 'value': 1, 'overlap': ['C']}]}}
        self.assertEqual(res, expected)

    def test_general_helper_functions(self):
        import vis_services.lib.histeq as histeq
        
        test_dict = {'a':1, 'b':1, 'c':6, 'd':9}
        
        HE = histeq.HistEq(test_dict, myrange=[1,5])
        
        expected = {'numseq_len': 4, 
                    'numseq_unique': [1, 6, 9], 
                    'numseq': [1, 1, 6, 9], 
                    'occurrences': {0: 0, 1: 2, 2: 0, 3: 0, 4: 0, 5: 0, 6: 1, 7: 0, 8: 0, 9: 1}, 
                    'myrange': [1, 5], 
                    'orig_list': {'a': 1, 'c': 6, 'b': 1, 'd': 9}}
        
        # We expect the HistEq class to be instantiated with he data above
        self.assertEqual(HE.__dict__, expected)
        # and produce the correct output
        res = HE.hist_eq()
        expected = {'a': 1.0, 'c': 3.0, 'b': 1.0, 'd': 5.0}
        self.assertEqual(res, expected)
        # if the values in the input dictionary are all the same, test for correct behavior (nothing needs to be done)
        test_dict = {'a':1, 'b':1}
        HE = histeq.HistEq(test_dict, myrange=[1,5])
        res = HE.hist_eq()
        expected = {'a': 1.0, 'b': 1.0}
        self.assertEqual(res, expected)
        # The the contents of "numseq" would cause to generate an exception with "max", we get an empty dictionary
        # This will never happen, though
        HE.numseq = []
        res = HE.hist_eq()
        self.assertEqual(res, {})

    @httpretty.activate    
    def test_views_helper_functions(self):
        from vis_services.views import make_request
        from vis_services.views import QueryException
        SOLRBIGQUERY_URL = self.app.config.get("VIS_SERVICE_BIGQUERY_PATH")
        httpretty.register_uri(
                    httpretty.POST, SOLRBIGQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps({'foo':'bar'}))
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps({'foo':'bar'}))
        # Check a call when a list of bibcodes is submitted
        required_fields = ['bibcode']
        with self.app.test_request_context(path='/wordcloud',method='POST', data=json.dumps({'bibcodes': ['a','b']}), content_type='application/json') as request:
            res = make_request(request.request, "PN", required_fields)
            self.assertEqual(res.json(), {'foo':'bar'})
        # Check a call when a query is submitted
        params = {}
        params['query'] = [json.dumps({'q':'author:"Henneken,E"'})]
        with self.app.test_request_context(path='/wordcloud',method='POST', data=json.dumps(params), content_type='application/json') as request:
            res = make_request(request.request, "PN", required_fields)
            self.assertEqual(res.json(), {'foo':'bar'})
        # Both bibcodes and a query in the request should result in an Exception
        params = {}
        params['query'] = [json.dumps({'q':'author:"Henneken,E"'})]
        params['bibcodes'] = ['a']
        with self.app.test_request_context(path='/wordcloud',method='POST', data=json.dumps(params), content_type='application/json') as request:
            err = 'success'
            try:
                res = make_request(request.request, "PN", required_fields)
            except QueryException as e:
                err = e
            except Exception as e:
                err = e
            self.assertEqual(str(err), 'Cannot send both bibcodes and query')
        # No bibcodes in a bibcode query should result in an Exception
        with self.app.test_request_context(path='/wordcloud',method='POST', data=json.dumps({'bibcodes': []}), content_type='application/json') as request:
            err = 'success'
            try:
                res = make_request(request.request, "PN", required_fields)
            except QueryException as e:
                err = e
            except Exception as e:
                err = e
            self.assertEqual(str(err), 'No bibcodes found in POST body')
        # Too many bibcodes should result in an Exception
        max_recs = self.app.config.get("VIS_SERVICE_PN_MAX_RECORDS")
        params = {}
        params['bibcodes'] = ['a']*(max_recs+1)
        with self.app.test_request_context(path='/wordcloud',method='POST', data=json.dumps(params), content_type='application/json') as request:
            err = 'success'
            try:
                res = make_request(request.request, "PN", required_fields)
            except QueryException as e:
                err = e
            except Exception as e:
                err = e
            self.assertEqual(str(err), 'No results: number of submitted bibcodes exceeds maximum number')
        # Wrongly encoded JSON for a query should result in an exception
        params = {}
        params['query'] = {'q':'author:"Henneken,E"'}
        with self.app.test_request_context(path='/wordcloud',method='POST', data=json.dumps(params), content_type='application/json') as request:
            err = 'success'
            try:
                res = make_request(request.request, "PN", required_fields)
            except QueryException as e:
                err = e
            except Exception as e:
                err = e
            self.assertEqual(str(err), 'couldn\'t decode query, it should be json-encoded before being sent (so double encoded)')
        # We should get either 'bibcode' or 'query' requests!
        params = {'foo':'bar'}
        with self.app.test_request_context(path='/wordcloud',method='POST', data=json.dumps(params), content_type='application/json') as request:
            err = 'success'
            try:
                res = make_request(request.request, "PN", required_fields)
            except QueryException as e:
                err = e
            except Exception as e:
                err = e
            self.assertEqual(str(err), 'Nothing to calculate network!')
        
        

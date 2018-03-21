import sys, os
import unittest
import json
from collections import defaultdict
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__),'../../'))
sys.path.append(PROJECT_HOME)
from lib import author_network, word_cloud, paper_network, tf_idf


#input data


input_js_word_cloud = json.load(open(PROJECT_HOME + "/tests/test_input/word_cloud_input.json"))

# has fewer than 50 nodes
input_js_author_network_small = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_before_groups_func_small.json"))
input_js_data_parameter = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_second_parameter.json"))
input_js_paper_network = json.load(open(PROJECT_HOME + "/tests/test_input/paper_network_before_groups_func_large.json"))


#result data

test_js_word_cloud = json.load(open(PROJECT_HOME + "/tests/test_output/word_cloud_accomazzi,a.json"))
test_json_word_cloud_min_occurrences = json.load(open(PROJECT_HOME + "/tests/test_output/word_cloud_accomazzi,a_min_occurrence_word_5.json"))

test_js_author_network = json.load(open(PROJECT_HOME + "/tests/test_output/author_network_accomazzi,a.json"))
test_js_author_network_max_groups = json.load(open(PROJECT_HOME + "/tests/test_output/author_network_accomazzi,a_max_groups_3.json"))
test_js_author_network_alberto = json.load(open(PROJECT_HOME + "/tests/test_input/kurtz_query.json"))

class TestEndpointLogic(unittest.TestCase):

    def test_word_cloud_resource(self):

        self.maxDiff = None

        # function: add_punc_and_remove_redundancies
        # uses the text returned from solr to do some cleaning up of the idf info returned by solr,
        # reducing counts of token components of slashed or dashed words
        # after this point the solr text is ignored, only the tf/idf data is used

        tf_idf_dict = {'word':{'tf' :[3], 'tf-idf' : [0.5]}, 'dashed' : {'tf' :[1], 'tf-idf' : [0.5]}, 'slashed' : {'tf' :[1], 'tf-idf' : [0.5]}, 'dashedword' : {'tf' :[1], 'tf-idf' : [0.5]}, 'slashedword' : {'tf' :[1], 'tf-idf' : [0.5]}}

        text_list = ['word', 'dashed-word', 'slashed/word']

        updated_info_dict = word_cloud.add_punc_and_remove_redundancies(tf_idf_dict, text_list)

        expected_outcome_info_dict = {'word':{'tf' :[1], 'tf-idf' : [0.5]}, 'dashed-word': {'tf' :[1], 'tf-idf' : [0.5]}, 'slashed/word' : {'tf' :[1], 'tf-idf' : [0.5]}, 'dashed' : {'tf' :[-1], 'tf-idf' : [0.5]}, 'slashed' : {'tf' :[0], 'tf-idf' : [0.5]}}

        self.assertEqual(updated_info_dict, expected_outcome_info_dict)

        # function: build_dict
        # is a parent function to add_punc_and_remove_redundancies that takes an tf idf info and text info
        # and returns a token and acronym dictionary. The token dictionary is grouped by stem and includes
        # a list of idf for each different word


        tf_idf_dict = {
            'fakeId': {
            'abstract': {
                'word': {
                'tf': [3],
                'tf-idf': [0.5]
                },
                'dashed': {
                'tf': [1],
                'tf-idf': [0.5]
                },
                'slashed': {
                'tf': [1],
                'tf-idf': [0.5]
                },
                'dashedword': {
                'tf': [1],
                'tf-idf': [0.5]
                },
                'slashedword': {
                'tf': [1],
                'tf-idf': [0.5]
                }
            },
            'title': {
                'research': {
                'tf': [1],
                'tf-idf': [0.1]
                },
                'researcher': {
                'tf': [1],
                'tf-idf': [0.9]
                },
                'acr::fake': {
                'tf': [1],
                'tf-idf': [0.5]
                }
            }
            }
        }

        text_list = [{'id': 'fakeId', 'abstract': 'word dashed-word slashed/word', 'title' : 'research researcher FAKE'}]


        expected_outcome_info_dict = ({'dashedword': {'idf': [0.5], 'tokens': {'dashed-word': 1},  'record_count' : ['fakeId']},
        'research': {'idf': [0.9, 0.1], 'tokens': {'research': 1, 'researcher': 1},  'record_count' : ['fakeId', 'fakeId']},
        'slashedword': {'idf': [0.5], 'tokens': {'slashed/word': 1},  'record_count' : ['fakeId']},
        'word': {'idf': [0.5], 'tokens': {'word': 1}, 'record_count' : ['fakeId']}},
        {'FAKE': {'idf': [0.5], 'total_occurrences': 1, 'record_count' : ['fakeId']}})


        updated_info_dict = word_cloud.build_dict(tf_idf_dict, text_list)

        self.assertEqual(updated_info_dict, expected_outcome_info_dict)


        #function: combine_and_process_dicts
        #uses the expected outcome from the previous function

        combined_dict = word_cloud.combine_and_process_dicts(expected_outcome_info_dict[0], expected_outcome_info_dict[1])

        expected_combined_dict = {
        'dashed-word': {'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 },
        'research' : {'idf': 0.5, 'total_occurrences' :2, 'record_count' :1 },
        'slashed/word':{'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 },
        'word': {'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 },
        'FAKE' : {'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 }
        }

        self.assertEqual(combined_dict, expected_combined_dict)

         #testing the main word cloud generation function with large data

        processed_data = word_cloud.generate_wordcloud(input_js_word_cloud, min_occurrences_word=2, min_percent_word=3)

        self.assertEqual(json.loads(json.dumps(processed_data)), test_js_word_cloud)

        processed_data = word_cloud.generate_wordcloud(input_js_word_cloud, min_occurrences_word=5, min_percent_word=3)

        self.assertEqual(json.loads(json.dumps(processed_data)), test_json_word_cloud_min_occurrences)



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

        input_js_author_network = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_before_groups_func_large.json"))

        processed_data = author_network.augment_graph_data(input_js_author_network, input_js_data_parameter)

        self.assertTrue("bibcode_dict" in processed_data)
        self.assertTrue("root" in processed_data)
        self.assertTrue("link_data" in processed_data)

        # testing entire function

        input_js_author_network = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_before_groups_func_large.json"))

        processed_data = json.loads(json.dumps(author_network.augment_graph_data(input_js_author_network, input_js_data_parameter), sort_keys=True))
        self.assertEqual(processed_data, test_js_author_network)



    def test_paper_network_resource(self):

        #first, test the tf-idf library

        self.maxDiff = None

        input_js_tf_idf = json.load(open(PROJECT_HOME + "/tests/test_input/tf_idf_input.json"))

        test_js_tf_idf = json.load(open(PROJECT_HOME + "/tests/test_output/tf_idf_output.json"))

        processed_data = json.loads(json.dumps(tf_idf.get_tf_idf_vals(input_js_tf_idf), sort_keys=True))

        self.assertEqual(processed_data, test_js_tf_idf)

        #now test reference counting function

        processed_data = json.loads(json.dumps(paper_network.get_papernetwork(input_js_paper_network["response"]["docs"], 10), sort_keys=True))

        topCommonReferences = processed_data["summaryGraph"]["nodes"][0]["top_common_references"].items().sort()

        def get_group_references(group):
            indexes =[i for i,n in enumerate(processed_data["fullGraph"]["nodes"]) if n["group"] == group]
            links =[l for l in processed_data["fullGraph"]["links"] if l["source"] in indexes and l["target"] in indexes]
            freq_dict = defaultdict(list)
            for l in links:
                for o in l["overlap"]:
                    freq_dict[o].extend([l["source"], l["target"]])

            for f in freq_dict:
                freq_dict[f] = len(list(set(freq_dict[f])))

            final = sorted(freq_dict.items(), key=lambda x:x[1], reverse=True)[:5]

            num_papers = processed_data["summaryGraph"]["nodes"][0]["paper_count"]

            final = [(f[0], f[1]/float(num_papers)) for f in final].sort()
            return final

        self.assertEqual(topCommonReferences, get_group_references(0))

        # now just test input/output

        test_js_paper_network =  json.load(open(PROJECT_HOME + "/tests/test_output/paper_network_star.json"))

        processed_data = json.loads(json.dumps(paper_network.get_papernetwork(input_js_paper_network["response"]["docs"], 10), sort_keys=True))
        self.assertEqual(processed_data, test_js_paper_network)

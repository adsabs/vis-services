import sys
import os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__),'../../'))
sys.path.append(PROJECT_HOME)
from flask_testing import TestCase
from flask import request
from flask import url_for, Flask
import unittest
import requests
import time
from vis_services import app
import json
import httpretty

STUBDATA_DIR = PROJECT_HOME + "/vis_services/tests/stubdata"
solr_data = json.load(open(STUBDATA_DIR + "/test_input/paper_network_before_groups_func_large.json"))
solr_data_err = json.load(open(STUBDATA_DIR + "/test_input/paper_network_without_cocitations.json"))
wordcloud = json.load(open(STUBDATA_DIR + "/test_output/wordcloud.json"))

class TestExpectedResults(TestCase):

    '''Check if the service returns expected results'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    @httpretty.activate
    def test_word_cloud_200(self):
        '''test query for generating a word cloud'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data))
        r = self.client.post(
                    url_for('wordcloud'),
                    content_type='application/json',
                    data=json.dumps(query_params))

        self.assertTrue(r.status_code == 200)

    @httpretty.activate
    def test_word_cloud_empty_request(self):
        '''test query for generating a word cloud - empty request should throw 403'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data))
        r = self.client.post(
                    url_for('wordcloud'),
                    content_type='application/json',
                    data=json.dumps(query_params))
        expected = {'Error Info': 'no data provided with request', 'Error': 'there was a problem with your request'}
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json, expected)

    @httpretty.activate
    def test_word_cloud_wrong_solr_data(self):
        '''test query for generating a word cloud - incorrect Solr request should throw 403'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'query': None}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data))
        r = self.client.post(
                    url_for('wordcloud'),
                    content_type='application/json',
                    data=json.dumps(query_params))
        expected = {'Error Info': "couldn't decode query, it should be json-encoded before being sent (so double encoded)", 'Error': 'there was a problem with your request'}
        self.assertEqual(r.status_code, 403)

    @httpretty.activate
    def test_word_cloud_solr_error(self):
        '''test query for generating a word cloud - Solr comes back with an HTTP error code'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=500,
                    body='Oops. Something went wrong!')
        r = self.client.post(
                    url_for('wordcloud'),
                    content_type='application/json',
                    data=json.dumps(query_params))

        expected = {'Error Info': 'Oops. Something went wrong!', 'Error': 'There was a connection error. Please try again later'}
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.json, expected)

    @httpretty.activate
    def test_author_network_200(self):
        '''test query for generating an author network'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data))
        r = self.client.post(
                    url_for('authornetwork'),
                    content_type='application/json',
                    data=json.dumps(query_params))

        self.assertTrue(r.status_code == 200)

    @httpretty.activate
    def test_author_network_solr_error(self):
        '''test query for generating an author network - Solr comes back with an HTTP error code'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=500,
                    body='Oops. Something went wrong!')
        r = self.client.post(
                    url_for('authornetwork'),
                    content_type='application/json',
                    data=json.dumps(query_params))

        expected = {'Error Info': 'Oops. Something went wrong!', 'Error': 'There was a connection error. Please try again later'}
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.json, expected)

    @httpretty.activate
    def test_author_network_data_error(self):
        '''test query for generating an author network'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'bibcodes': [], 'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data))
        r = self.client.post(
                    url_for('authornetwork'),
                    content_type='application/json',
                    data=json.dumps(query_params))
        expected = {'Error Info': 'Cannot send both bibcodes and query', 'Error': 'there was a problem with your request'}
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json, expected)

    @httpretty.activate
    def test_paper_network_200(self):
        '''test query for generating a paper network'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data))
        r = self.client.post(
                    url_for('papernetwork'),
                    content_type='application/json',
                    data=json.dumps(query_params))
        
        self.assertTrue(r.status_code == 200)

    @httpretty.activate
    def test_paper_network_empty(self):
        '''test query for generating a paper network'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_BIGQUERY_PATH")
        query_params = {'bibcodes': ['2025Meas..25618270J', '2025EPJQT..12...30B', '2025TUSTI.16406865Y', '2025OptL...50.5961A', '2025ThApC.156..514I']}
        httpretty.register_uri(
                    httpretty.POST, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data_err))
        r = self.client.post(
                    url_for('papernetwork'),
                    content_type='application/json',
                    data=json.dumps(query_params))
        expected_output = {'Error': 'Empty network.'}
        self.assertTrue(r.status_code == 200)
        self.assertTrue(r.json == expected_output)

    @httpretty.activate
    def test_paper_network_solr_error(self):
        '''test query for generating a paper network - Solr comes back with an HTTP error code'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=500,
                    body='Oops. Something went wrong!')
        r = self.client.post(
                    url_for('papernetwork'),
                    content_type='application/json',
                    data=json.dumps(query_params))

        expected = {'Error Info': 'Oops. Something went wrong!', 'Error': 'There was a connection error. Please try again later'}
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.json, expected)

    @httpretty.activate
    def test_paper_network_data_error(self):
        '''test query for generating an author network'''
        SOLRQUERY_URL = self.app.config.get("VIS_SERVICE_SOLR_PATH")
        query_params = {'bibcodes': [], 'query': ['{"q": "author:\\"Henneken,E\\""}']}
        httpretty.register_uri(
                    httpretty.GET, SOLRQUERY_URL,
                    content_type='application/json',
                    status=200,
                    body='%s'%json.dumps(solr_data))
        r = self.client.post(
                    url_for('papernetwork'),
                    content_type='application/json',
                    data=json.dumps(query_params))
        expected = {'Error Info': 'Cannot send both bibcodes and query', 'Error': 'there was a problem with your request'}
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json, expected)

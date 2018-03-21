from flask import current_app, request
from flask_restful import Resource, reqparse
from flask_discoverer import advertise
from lib import word_cloud
from lib import author_network
from lib import paper_network
from client import client
import json

# the function make_request is used for paper and author network,
# to get a solr response from the query or bibcodes parameter
# provided by the user
# if a query is sent, it has to be double-encoded

class QueryException(Exception):
    pass

def make_request(request, service_string, required_fields):
    bibcodes = []
    query = None

    if 'bibcodes' in request.json:
        if 'query' in request.json and request.json['query']:
            raise QueryException('Cannot send both bibcodes and query')

        bibcodes = map(str, request.json['bibcodes'])

        if len(bibcodes) > current_app.config.get("VIS_SERVICE_" + service_string + "_MAX_RECORDS"):
            raise QueryException('No results: number of submitted bibcodes exceeds maximum number')

        elif len(bibcodes) == 0:
            raise QueryException('No bibcodes found in POST body')

        #we have bibcodes, which might be up to 1000 ( too long for solr using GET),
        #so use bigquery
        headers = {'X-Forwarded-Authorization' : request.headers.get('Authorization')}
        big_query_params = {'q':'*:*', 'wt':'json', 'fl': required_fields, 'fq': '{!bitset}', 'rows' : len(bibcodes)}

        response = client().post(   current_app.config.get("VIS_SERVICE_BIGQUERY_PATH"),
                                    params = big_query_params,
                                    headers = headers,
                                    data = 'bibcode\n' + '\n'.join(bibcodes)
                                )
        return response

    #this shouldnt be advertised, it's there only as a convenience for Bumblebee
    elif 'query' in request.json:
        try:
            solr_args = json.loads(request.json["query"][0])
        except Exception:
            raise QueryException('couldn\'t decode query, it should be json-encoded before being sent (so double encoded)')
        solr_args["rows"] = min(int(solr_args.get("rows", [current_app.config.get("VIS_SERVICE_AN_MAX_RECORDS")])[0]), current_app.config.get("VIS_SERVICE_AN_MAX_RECORDS"))
        solr_args['fl'] = required_fields
        solr_args['wt'] ='json'
        headers = {'X-Forwarded-Authorization' : request.headers.get('Authorization')}

        response = client().get(current_app.config.get("VIS_SERVICE_SOLR_PATH"), params = solr_args, headers = headers )
        return response

    else:
        #neither bibcodes nor query were provided
        raise QueryException('Nothing to calculate network!')


class WordCloud(Resource):
    '''Returns collated tf/idf data for a solr query'''
    decorators = [advertise('scopes', 'rate_limit')]
    scopes = []
    rate_limit = [500,60*60*24]

    def post(self):

        solr_args = request.json
        if not solr_args:
            return {'Error' : 'there was a problem with your request', 'Error Info': 'no data provided with request'}, 403

        if 'max_groups' in solr_args:
            del solr_args['min_percent_word']
        if 'min_occurrences_word' in solr_args:
            del solr_args['min_occurrences_word']

        elif 'query' in request.json:
            try:
                solr_args = json.loads(request.json["query"][0])
            except Exception:
                return {'Error' : 'there was a problem with your request', 'Error Info': 'couldn\'t decode query, it should be json-encoded before being sent (so double encoded)'}, 403

        solr_args["rows"] = min(int(solr_args.get("rows", [current_app.config.get("VIS_SERVICE_WC_MAX_RECORDS")])[0]), current_app.config.get("VIS_SERVICE_WC_MAX_RECORDS"))
        solr_args['fields'] = ['id']
        solr_args['defType'] = 'aqp'
        solr_args['tv'] = 'true'
        solr_args['tv.tf_idf'] = 'true'
        solr_args['tv.tf'] = 'true'
        solr_args['tv.positions'] ='false'
        solr_args['tf.offsets'] = 'false'
        solr_args['tv.fl'] ='abstract,title'
        solr_args['fl'] ='id,abstract,title'
        solr_args['wt'] = 'json'

        headers = {'X-Forwarded-Authorization' : request.headers.get('Authorization')}

        response = client().get(current_app.config.get("VIS_SERVICE_TVRH_PATH") , params = solr_args, headers=headers)

        if response.status_code == 200:
            data = response.json()
        else:
            return {"Error": "There was a connection error. Please try again later", "Error Info": response.text}, response.status_code

        if data:
            min_percent_word = request.args.get("min_percent_word", current_app.config.get("VIS_SERVICE_WC_MIN_PERCENT_WORD"))
            min_occurrences_word = request.args.get("min_occurrences_word", current_app.config.get("VIS_SERVICE_WC_MIN_OCCURRENCES_WORD"))

            word_cloud_json = word_cloud.generate_wordcloud(data, min_percent_word = min_percent_word, min_occurrences_word = min_occurrences_word)
        if word_cloud_json:
            return word_cloud_json, 200
        else:
            return {"Error": "Empty word cloud. Try changing your minimum word parameters or expanding your query."}, 200

class AuthorNetwork(Resource):
    '''Returns author network data for a solr query'''
    decorators = [advertise('scopes', 'rate_limit')]
    scopes = []
    rate_limit = [500,60*60*24]

    def post(self):

        try:
            required_fields = ['author_norm', 'title', 'citation_count', 'read_count','bibcode', 'pubdate']
            response = make_request(request, "AN", required_fields)
        except QueryException as error:
            return {'Error' : 'there was a problem with your request', 'Error Info': error}, 403

        if response.status_code == 200:
            full_response = response.json()
        else:
            return {"Error": "There was a connection error. Please try again later", "Error Info": response.text}, response.status_code

        #get_network_with_groups expects a list of normalized authors
        author_norm = [d.get("author_norm", []) for d in full_response["response"]["docs"]]
        author_network_json = author_network.get_network_with_groups(author_norm, full_response["response"]["docs"])

        if author_network_json:
          return { "msg" :
          { "numFound" : full_response["response"]["numFound"],
            "start": full_response["response"].get("start", 0),
            "rows": int(full_response["responseHeader"]["params"]["rows"])
           }, "data" : author_network_json}, 200
        else:
          return {"Error": "Empty network."}, 200


class PaperNetwork(Resource):
    '''Returns paper network data for a solr query'''
    decorators = [advertise('scopes', 'rate_limit')]
    scopes = []
    rate_limit = [500,60*60*24]

    def post(self):

        try:
            required_fields = ['bibcode,title,first_author,year,citation_count,read_count,reference']
            response = make_request(request, "PN", required_fields)
        except QueryException as error:
            return {'Error' : 'there was a problem with your request', 'Error Info': error}, 403

        if response.status_code == 200:
            full_response = response.json()
        else:
            return {"Error": "There was a connection error. Please try again later", "Error Info": response.text}, response.status_code

        #get_network_with_groups expects a list of normalized authors
        data = full_response["response"]["docs"]
        paper_network_json = paper_network.get_papernetwork(data, request.json.get("max_groups", current_app.config.get("VIS_SERVICE_PN_MAX_GROUPS")))
        if paper_network_json:
            return { "msg" : {
            "numFound" : full_response["response"]["numFound"],
            "start": full_response["response"].get("start", 0),
            "rows": int(full_response["responseHeader"]["params"]["rows"])
             },
             "data" : paper_network_json}, 200
        else:
            return {"Error": "Empty network."}, 200

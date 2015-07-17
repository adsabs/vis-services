from flask import current_app, Blueprint, jsonify, request
from flask.ext.restful import Resource, reqparse
import inspect
import sys
from lib import word_cloud
from lib import author_network
from lib import paper_network



blueprint = Blueprint(
    'visualization',
    __name__,
    static_folder=None,
)

#This resource must be available for every adsabs webservice.
class Resources(Resource):
  '''Overview of available resources'''
  scopes = []
  rate_limit = [500,60*60*24]
  def get(self):
    func_list = {}

    clsmembers = [i[1] for i in inspect.getmembers(sys.modules[__name__], inspect.isclass)]
    for rule in current_app.url_map.iter_rules():
      f = current_app.view_functions[rule.endpoint]
      #If we load this webservice as a module, we can't guarantee that current_app only has these views
      if not hasattr(f,'view_class') or f.view_class not in clsmembers:
        continue
      methods = f.view_class.methods
      scopes = f.view_class.scopes
      rate_limit = f.view_class.rate_limit
      description = f.view_class.__doc__
      func_list[rule.rule] = {'methods':methods,'scopes': scopes,'description': description,'rate_limit':rate_limit}
    return func_list, 200



class WordCloud(Resource):
  '''Returns collated tf/idf data for a solr query'''
  scopes = [] 
  rate_limit = [500,60*60*24]

  def get(self):

    solr_args = {k : v for k, v in request.args.items() if k not in ["min_percent_word", "min_occurrences_word"]}
    solr_args.setdefault("rows", current_app.config.get("WC_MAX_RECORDS"))
    solr_args["rows"] = min(int(solr_args.get("rows")), current_app.config.get("WC_MAX_RECORDS"))
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

    response = current_app.client.session.get(current_app.config.get("TVRH_SOLR_PATH") , params = solr_args, headers=headers)
    return solr_args, ", ", headers, ", ", response

    if response.status_code == 200:
        data = response.json()
    else:
        return {"Error": "There was a connection error. Please try again later", "Error Info": response.text}, response.status_code

    if data:
        min_percent_word = request.args.get("min_percent_word", current_app.config.get("WC_MIN_PERCENT_WORD"))
        min_occurrences_word = request.args.get("min_occurrences_word", current_app.config.get("WC_MIN_OCCURRENCES_WORD"))

        word_cloud_json = word_cloud.generate_wordcloud(
            data, min_percent_word = min_percent_word, min_occurrences_word = min_occurrences_word)
    if word_cloud_json:
        return word_cloud_json, 200
    else:
        return {"Error": "Empty word cloud. Try changing your minimum word parameters or expanding your query."}, 200

class AuthorNetwork(Resource):
  '''Returns author network data for a solr query'''
  scopes = [] 
  rate_limit = [500,60*60*24]

  def get(self):

    solr_args = {k : v for k,v in request.args.items()}
    
    solr_args.setdefault("rows", current_app.config.get("AN_MAX_RECORDS"))
    solr_args["rows"] = min(int(solr_args.get("rows")), current_app.config.get("AN_MAX_RECORDS"))
    solr_args['fl'] = ['author_norm', 'title', 'citation_count', 'read_count','bibcode', 'pubdate']
    solr_args['wt'] ='json'

    headers = {'X-Forwarded-Authorization' : request.headers.get('Authorization')}

    response = current_app.client.session.get(current_app.config.get("SOLR_PATH") , params = solr_args, headers=headers)

    if response.status_code == 200:
      full_response = response.json()
    else:
      return {"Error": "There was a connection error. Please try again later", "Error Info": response.text}, response.status_code

    #get_network_with_groups expects a list of normalized authors
    author_norm = [d.get("author_norm", []) for d in full_response["response"]["docs"]]
    author_network_json = author_network.get_network_with_groups(author_norm, full_response["response"]["docs"])

    if author_network_json:
      return {"msg" : {"numFound" : full_response["response"]["numFound"],
       "start": full_response["response"].get("start", 0),
        "rows": int(full_response["responseHeader"]["params"]["rows"])
       }, "data" : author_network_json}, 200
    else:
      return {"Error": "Empty network."}, 200


class PaperNetwork(Resource):
  '''Returns paper network data for a solr query'''
  scopes = [] 
  rate_limit = [500,60*60*24] 

  def get(self):

    solr_args = {k : v for k,v in request.args.items() if k != "max_groups"}
    
    solr_args.setdefault("rows", current_app.config.get("PN_MAX_RECORDS"))
    solr_args["rows"] = min(int(solr_args.get("rows")), current_app.config.get("PN_MAX_RECORDS"))
    solr_args['fl'] = ['bibcode,title,first_author,year,citation_count,read_count,reference']
    solr_args['wt'] ='json'

    assert "q" in solr_args and solr_args["q"] is not None
    headers = {'X-Forwarded-Authorization' : request.headers.get('Authorization')}
    response = current_app.client.session.get(current_app.config.get("SOLR_PATH") , params = solr_args, headers=headers)

    if response.status_code == 200:
      full_response = response.json()
    else:
      return {"Error": "There was a connection error. Please try again later", "Error Info": response.text}, response.status_code
    #get_network_with_groups expects a list of normalized authors
    data = full_response["response"]["docs"]
    return data
    paper_network_json = paper_network.get_papernetwork(data, request.args.get("max_groups", current_app.config.get("PN_MAX_GROUPS")))
    if paper_network_json:
      return {"msg" : {"numFound" : full_response["response"]["numFound"],
       "start": full_response["response"].get("start", 0),
        "rows": int(full_response["responseHeader"]["params"]["rows"])
       }, "data" : paper_network_json}, 200
    else:
      return {"Error": "Empty network."}, 200


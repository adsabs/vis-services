SOLR_PATH = 'api.adsabs.harvard.edu/v1/search/query'

TVRH_SOLR_PATH = 'http://0.0.0.0:9000/solr/tvrh/'


#This section configures this application to act as a client, for example to query solr via adsws
CLIENT = {
  'TOKEN': 'BzPWOPni1pfR1KAiu7y9GBf6gU4zrwIOy2RyFY76bJDm6lPyNWGb7t8n6DU0'
}



#word cloud config

WC_MAX_RECORDS = 500
WC_START = 0

#threshold that a word stem has to pass before being included
WC_MIN_PERCENT_WORD = 3

WC_MIN_OCCURRENCES_WORD = 2




#author network config

AN_MAX_RECORDS = 1000
AN_START = 0

#configuration for augmented graph data
AN_MAX_GROUPS = 8


#paper network config

#paper network calculation is kind of slow, so limiting the number of records for now.
PN_MAX_RECORDS = 1000
PN_START = 0

#configuration for augmented graph data
PN_MAX_GROUPS = 10



VIS_SERVICE_SOLR_PATH = 'http://api.adsabs.harvard.edu/v1/search/query'

VIS_SERVICE_TVRH_PATH = 'http://0.0.0.0:9000/solr/tvrh/'

#This section configures this application to act as a client, for example to query solr via adsws
VIS_SERVICE_API_TOKEN = 'This should be changed'

#word cloud config
VIS_SERVICE_WC_MAX_RECORDS = 500
VIS_SERVICE_WC_START = 0

#threshold that a word stem has to pass before being included
VIS_SERVICE_WC_MIN_PERCENT_WORD = 3
VIS_SERVICE_WC_MIN_OCCURRENCES_WORD = 2

#author network config
VIS_SERVICE_AN_MAX_RECORDS = 1000
VIS_SERVICE_AN_START = 0

#configuration for augmented graph data
VIS_SERVICE_AN_MAX_GROUPS = 8

#paper network config
#paper network calculation is kind of slow, so limiting the number of records for now.
VIS_SERVICE_PN_MAX_RECORDS = 1000
VIS_SERVICE_PN_START = 0

#configuration for augmented graph data
VIS_SERVICE_PN_MAX_GROUPS = 10



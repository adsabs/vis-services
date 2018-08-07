import os

LOG_STDOUT = True

VIS_SERVICE_BIGQUERY_PATH = 'http://ecs-staging-elb-2044121877.us-east-1.elb.amazonaws.com/v1/search/bigquery'
VIS_SERVICE_TVRH_PATH = 'http://ecs-staging-elb-2044121877.us-east-1.elb.amazonaws.com/v1/search/tvrh'
VIS_SERVICE_SOLR_PATH = 'http://ecs-staging-elb-2044121877.us-east-1.elb.amazonaws.com/v1/search/query'

#This section configures this application to act as a client, for example to query solr via adsws
VIS_SERVICE_API_TOKEN = None

#word cloud config
VIS_SERVICE_WC_MAX_RECORDS = 500
VIS_SERVICE_WC_MAX_WORDS = 100
VIS_SERVICE_WC_THREADS = 2
VIS_SERVICE_WC_MAX_TITLE_SIZE = 1000 # characters
VIS_SERVICE_WC_MAX_ABSTRACT_SIZE = 5000 # characters


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

# DEBUG = True
# TESTING = True

# In what environment are we?
ENVIRONMENT = os.getenv('ENVIRONMENT', 'staging').lower()
# Config for logging
VIS_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s\t%(process)d '
                      '[%(asctime)s]:\t%(message)s',
            'datefmt': '%m/%d/%Y %H:%M:%S',
        }
    },
    'handlers': {
        'file': {
            'formatter': 'default',
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/tmp/vis_service.app.{}.log'.format(ENVIRONMENT),
        },
        'console': {
            'formatter': 'default',
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

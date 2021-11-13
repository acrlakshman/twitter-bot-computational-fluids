import os
from enum import Enum
from datetime import timedelta
import random
import logging
from logging.handlers import TimedRotatingFileHandler

# Variables appended with _DEFAULT are used to initialize config parameters in the database.
HASH_TAGS_DEFAULT = ['computationalfluiddynamics', 'volumeoffluid', 'latticeboltzmann', 'multiphaseflows']
HASH_TAGS_META_DEFAULT = {'computationalfluiddynamics': {'include_strs': [], 'exclude_strs': [], 'exclude_users': []}}
HASH_TAGS_META_INCLUDE_STR_KEY = 'include_strs'
HASH_TAGS_META_EXCLUDE_STR_KEY = 'exclude_strs'
HASH_TAGS_META_EXCLUDE_USERS_KEY = 'exclude_users'
NUM_TWEETS_TO_SEARCH_DEFAULT = 10
PULL_TWEETS_INTERVAL_DEFAULT = timedelta(minutes=5) # Currently not being used.
PAUSE_APP_DEFAULT = False

HASH_TAGS = HASH_TAGS_DEFAULT
HASH_TAGS_META = HASH_TAGS_META_DEFAULT
NUM_TWEETS_TO_SEARCH = NUM_TWEETS_TO_SEARCH_DEFAULT
PULL_TWEETS_INTERVAL = PULL_TWEETS_INTERVAL_DEFAULT # Currently not being used.
PAUSE_APP = PAUSE_APP_DEFAULT

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# mongo config
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_DB = os.getenv("MONGO_DB")

MONGO_PORT = 27017
MONGO_COLL_PULLED_LIST = 'pulled_list'
MONGO_COLL_POSTED_LIST = 'posted_list'
MONGO_COLL_DISCARD_LIST = 'discard_list'
MONGO_COLL_TIME_STAMPS = 'time_stamps'
MONGO_COLL_COUNTERS = 'counters'
MONGO_COLL_CONFIG = 'config'


class MongoDocLists(Enum):
    PULLED_LIST = MONGO_COLL_PULLED_LIST
    POSTED_LIST = MONGO_COLL_POSTED_LIST
    DISCARD_LIST = MONGO_COLL_DISCARD_LIST


# twitter rate-limits
# https://developer.twitter.com/en/docs/basics/rate-limits
TWEET_RETWEET_ID = "tweet_retweet"
TWEET_RETWEET_LIMIT_WINDOW = timedelta(hours=3)
TWEET_RETWEET_APP_LIMIT = 300
FAVORITES_ID = "favorites"
FAVORITES_LIMIT_WINDOW = timedelta(hours=24)
FAVORITES_APP_LIMIT = 1000
SEARCH_TWEETS_ID = "search"
SEARCH_TWEETS_LIMIT_WINDOW = timedelta(minutes=15)
SEARCH_TWEETS_APP_LIMIT = 450

logger = logging.getLogger('cfdspace')
logger.setLevel(logging.DEBUG)
fh = TimedRotatingFileHandler('/var/log/cfdspace.log', when='midnight')
FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(FORMATTER)
logger.addHandler(fh)
logger.propagate = False


def get_rand_sleep_time():
    return random.randint(60, 180)

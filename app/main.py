import tweepy
import time
from datetime import datetime, timedelta
import config
from api_helper import APIHelper


def get_counters_log(mongo_client, id_str):
    """Returns mongo document from collection config.MONGO_COLL_COUNTERS
    for a given id_str
    """
    db = mongo_client[config.MONGO_DB]
    coll = db[config.MONGO_COLL_COUNTERS]
    mongo_query = {"idStr": id_str}

    return coll.find_one(mongo_query)


def get_api_call_counters(mongo_client, id_str):
    """Returns number of times api calls were made. Query is made on
    the provied id string.

    get_api_call_counters(mongo_client, config.TWEET_RETWEET_ID)
    """
    db = mongo_client[config.MONGO_DB]
    coll = db[config.MONGO_COLL_COUNTERS]
    time_now = datetime.now()
    mongo_query = {"idStr": id_str}
    num_calls = 0

    doc = coll.find_one(mongo_query)
    if doc:
        num_calls = doc["numCalls"]

    return num_calls


# e.x.: id_str = config.TWEET_RETWEET_ID
def reset_api_call_counters(mongo_client, id_str, limit_window):
    db = mongo_client[config.MONGO_DB]
    coll = db[config.MONGO_COLL_COUNTERS]
    time_now = datetime.now()
    mongo_query = {"idStr": id_str}

    if (coll.find_one(mongo_query)):
        coll.update_one(
            mongo_query, {"$set": {"numCalls": 0, "callWindowStart": time_now, "callWindowEnd": time_now + limit_window, "updatedAt": time_now}})


# e.x.: id_str = config.TWEET_RETWEET_ID
def inc_api_call_counters(mongo_client, id_str, limit_window):
    db = mongo_client[config.MONGO_DB]
    coll = db[config.MONGO_COLL_COUNTERS]
    time_now = datetime.now()
    mongo_query = {"idStr": id_str}

    if (coll.find_one(mongo_query)):
        coll.update_one(
            mongo_query, {"$inc": {"numCalls": 1, "totalCalls": 1}})
        coll.update_one(mongo_query, {"$set": {"updatedAt": time_now}})
    else:
        coll.insert_one({"idStr": id_str, "numCalls": 1,
                         "totalCalls": 1, "callWindowStart": time_now, "callWindowEnd": time_now + limit_window, "updatedAt": time_now, "createdAt": time_now})


def add_or_update_time(mongo_client, coll_name, id_str, hash_tag):
    # update time
    db = mongo_client[config.MONGO_DB]
    time_stamps_coll = db[coll_name]
    time_now = datetime.now()
    mongo_query = {"idStr": id_str, "hashTag": hash_tag}
    if (time_stamps_coll.find_one(mongo_query)):
        time_stamps_coll.update_one(
            mongo_query, {"$set": {"updatedAt": time_now}})
    else:
        time_stamps_coll.insert_one({"idStr": id_str, "hashTag": hash_tag,
                                     "updatedAt": time_now, "createdAt": time_now})


def can_call_pull_tweets(mongo_client):
    doc = get_counters_log(mongo_client, config.SEARCH_TWEETS_ID)
    time_now = datetime.now()

    if doc:
        delta = time_now - doc["callWindowEnd"]
        if time_now > doc["callWindowEnd"]:
            reset_api_call_counters(
                mongo_client, config.SEARCH_TWEETS_ID, config.SEARCH_TWEETS_LIMIT_WINDOW)
            return True
        else:
            if doc["numCalls"] < config.SEARCH_TWEETS_APP_LIMIT:
                return True
            else:
                return False
    else:
        return True


def exclude_tweet(hash_tag, tweet):
    """Returns True if tweet needs to be excluded."""
    # Check for exclude strings
    exclude = False
    if hash_tag in config.HASH_TAGS_META:
        if config.HASH_TAGS_META_EXCLUDE_STR_KEY in config.HASH_TAGS_META[hash_tag]:
            for val in config.HASH_TAGS_META[hash_tag][config.HASH_TAGS_META_EXCLUDE_STR_KEY]:
                if val and tweet['full_text'] and ('full_text' in tweet) and (val.lower() in tweet['full_text'].lower()):
                    exclude = True
                    break

    return exclude


def include_tweet(hash_tag, tweet):
    """Returns True if tweet needs to be included."""
    # Check for include strings
    include = False
    if hash_tag in config.HASH_TAGS_META:
        if config.HASH_TAGS_META_INCLUDE_STR_KEY in config.HASH_TAGS_META[hash_tag]:
            if len(config.HASH_TAGS_META[hash_tag][config.HASH_TAGS_META_INCLUDE_STR_KEY]):
                for val in config.HASH_TAGS_META[hash_tag][config.HASH_TAGS_META_INCLUDE_STR_KEY]:
                    if val and tweet['full_text'] and ('full_text' in tweet) and (val.lower() in tweet['full_text'].lower()):
                        include = True
                        break
            else:
                include = True
        else:
            include = True
    else:
        include = True

    return include


def tweet_is_a_reply(hash_tag, tweet):
    """Returns True if tweet is a reply."""
    if tweet['in_reply_to_status_id'] is not None:
        return True
    else:
        return False


def tweet_is_from_excluded_user(hash_tag, tweet):
    """Returns True if tweet is from excluded user."""
    from_excluded_user = False

    if hash_tag in config.HASH_TAGS_META:
        if config.HASH_TAGS_META_EXCLUDE_USERS_KEY in config.HASH_TAGS_META[hash_tag]:
            for val in config.HASH_TAGS_META[hash_tag][config.HASH_TAGS_META_EXCLUDE_USERS_KEY]:
                if val and (val.lower() in tweet['user']['screen_name'].lower()):
                    from_excluded_user = True
                    break

    return from_excluded_user


def include_tweet_to_process(hash_tag, tweet):
    return ((not exclude_tweet(hash_tag, tweet._json)) and
            include_tweet(hash_tag, tweet._json) and
            (not tweet_is_a_reply(hash_tag, tweet._json)) and
            (not tweet_is_from_excluded_user(hash_tag, tweet._json)))


def pull_tweets(tw_api, mongo_client, hash_tag):
    if can_call_pull_tweets(mongo_client):
        tweets = tweepy.Cursor(tw_api.search_tweets, q="#" + hash_tag,
                               tweet_mode="extended").items(config.NUM_TWEETS_TO_SEARCH)
        inc_api_call_counters(
            mongo_client, config.SEARCH_TWEETS_ID, config.SEARCH_TWEETS_LIMIT_WINDOW)

        db = mongo_client[config.MONGO_DB]
        pulled_list_coll = db[config.MONGO_COLL_PULLED_LIST]

        for tweet in tweets:
            if (not pulled_list_coll.find_one({"id_str": tweet.id_str})):
                if include_tweet_to_process(hash_tag, tweet):
                    pulled_list_coll.insert_one(tweet._json)

                    add_or_update_time(
                        mongo_client, config.MONGO_COLL_TIME_STAMPS, config.MONGO_COLL_PULLED_LIST, hash_tag)


def in_the_list(mongo_client, mongo_doc, mongo_doc_list):
    """Returns True if the id_str matches with id_str from the list."""

    db = mongo_client[config.MONGO_DB]
    coll = db[mongo_doc_list.value]

    if coll.find_one({"id_str": mongo_doc["id_str"]}):
        return True

    return False


def can_process_tweets(mongo_client):
    doc = get_counters_log(mongo_client, config.TWEET_RETWEET_ID)
    time_now = datetime.now()

    if doc:
        delta = time_now - doc["callWindowEnd"]
        if time_now > doc["callWindowEnd"]:
            reset_api_call_counters(
                mongo_client, config.TWEET_RETWEET_ID, config.TWEET_RETWEET_LIMIT_WINDOW)
            return True
        else:
            if doc["numCalls"] < config.TWEET_RETWEET_APP_LIMIT:
                return True
            else:
                return False
    else:
        return True


def process_pulled_tweets(tw_api, mongo_client):
    """Loop through pulled_list collection, if a tweet is valid, post it
    and save it in posted_list, else move it to discard_list.

    - Checks to pass to move to posted_list:
        - tweet is not a retweeted one.
        - tweet id is not found in posted_list.
        - tweet id is not found in discard_list.
        - language code is 'en'.
        - full_text does not match with another tweet in posted_list to avoid duplicate action.
        - TODO: check the context using ML model.
    """

    db = mongo_client[config.MONGO_DB]

    pulled_list_coll = db[config.MONGO_COLL_PULLED_LIST]
    posted_list_coll = db[config.MONGO_COLL_POSTED_LIST]
    discard_list_coll = db[config.MONGO_COLL_DISCARD_LIST]

    # process all that are retweets and remove them
    pulled_list = pulled_list_coll.find(
        {"retweeted_status": {"$exists": True}})
    for doc in pulled_list:
        pulled_list_coll.delete_one({"id_str": doc["id_str"]})

    pulled_list = pulled_list_coll.find({})

    for doc in pulled_list:
        if can_process_tweets(mongo_client):
            # Check tweet id in posted_list
            if in_the_list(mongo_client, doc, config.MongoDocLists.POSTED_LIST):
                pulled_list_coll.delete_one({"id_str": doc["id_str"]})
                continue

            # Check tweet id in discard_list
            if in_the_list(mongo_client, doc, config.MongoDocLists.DISCARD_LIST):
                pulled_list_coll.delete_one({"id_str": doc["id_str"]})
                continue

            # Check the language code
            if not (doc["metadata"]["iso_language_code"] == 'en'):
                pulled_list_coll.delete_one({"id_str": doc["id_str"]})
                continue

            # Check the full_text with existing documents' full_text in posted_list
            if posted_list_coll.find_one({"full_text": doc["full_text"]}):
                pulled_list_coll.delete_one({"id_str": doc["id_str"]})
                continue

            # retweet and add to posted_list
            try:
                retweet_status = tw_api.retweet(doc["id"])
                inc_api_call_counters(
                    mongo_client, config.TWEET_RETWEET_ID, config.TWEET_RETWEET_LIMIT_WINDOW)
                posted_list_coll.insert_one(doc)
                pulled_list_coll.delete_one({"id_str": doc["id_str"]})
            except tweepy.TweepyException as e:
                discard_list_coll.insert_one(doc)
                pulled_list_coll.delete_one({"id_str": doc["id_str"]})
                # FIXME: Below indexing is not right.
                #config.logger.error(
                #    "During retweet for ID: {}; message: {}".format(doc["id_str"], e.args[0][0]['message']))

        retweet_delay_time = config.get_rand_sleep_time()
        config.logger.info(
            "\tNext retweet attempt in {} s".format(retweet_delay_time))
        time.sleep(retweet_delay_time)


def initialize(mongo_client):
    """Save required configuration options into database."""
    db = mongo_client[config.MONGO_DB]
    coll = db[config.MONGO_COLL_CONFIG]
    config_key = "config"
    time_now = datetime.now()
    mongo_query = {"idStr": config_key}

    doc = coll.find_one(mongo_query)
    if (doc):
        config.logger.debug("Reading config from collection")

        config.HASH_TAGS = doc["hash_tags"]

        if not 'hash_tags_meta' in doc:
            doc["hash_tags_meta"] = config.HASH_TAGS_META
            coll.update_one(mongo_query, {"$set": {"hash_tags_meta": config.HASH_TAGS_META, "updatedAt": time_now}})
        else:
            config.HASH_TAGS_META = doc["hash_tags_meta"]

        config.NUM_TWEETS_TO_SEARCH = doc["num_tweets_to_search"]
        config.PULL_TWEETS_INTERVAL = timedelta(
            minutes=doc["pull_tweets_interval_in_minutes"])
        config.PAUSE_APP = doc["pause_app"]

        config.logger.debug("\thash tags: {}".format(config.HASH_TAGS))
        config.logger.debug("\tnum tweets to search: {}".format(
            config.NUM_TWEETS_TO_SEARCH))
        config.logger.debug("\tpull tweets interval: {}".format(
            config.PULL_TWEETS_INTERVAL))
        config.logger.debug("\tIs app paused? {}".format(config.PAUSE_APP))
    else:
        coll.insert_one({"idStr": config_key, "hash_tags": config.HASH_TAGS,
                         "hash_tags_meta": config.HASH_TAGS_META,
                         "num_tweets_to_search": config.NUM_TWEETS_TO_SEARCH,
                         "pull_tweets_interval_in_minutes": int(config.PULL_TWEETS_INTERVAL.seconds / 60),
                         "pause_app": config.PAUSE_APP,
                         "updatedAt": time_now, "createdAt": time_now})

        config.logger.debug("Created config collection")
        config.logger.debug("\thash tags: {}".format(config.HASH_TAGS))
        config.logger.debug("\thash tags meta: {}".format(config.HASH_TAGS_META))
        config.logger.debug("\tnum tweets to search: {}".format(
            config.NUM_TWEETS_TO_SEARCH))
        config.logger.debug("\tpull tweets interval: {}".format(
            config.PULL_TWEETS_INTERVAL))

    for hash_tag in config.HASH_TAGS:
        config.logger.debug("\t\thash_tag: {}".format(hash_tag))
        if hash_tag in config.HASH_TAGS_META:
            config.logger.debug("\t\t - meta has hash_tag: {}".format(hash_tag))
            for key in config.HASH_TAGS_META[hash_tag]:
                config.logger.debug("\t\t --- meta hash_tag has key")
                config.logger.debug("\t\t\t{}: {}".format(key, config.HASH_TAGS_META[hash_tag][key]))


def run(tw_api, mongo_client):
    while True:
        config.logger.info("App is running")
        initialize(mongo_client)

        if not config.PAUSE_APP:
            for hash_tag in config.HASH_TAGS:
                pull_tweets(tw_api, mongo_client, hash_tag)
                time.sleep(config.get_rand_sleep_time())

            process_pulled_tweets(tw_api, mongo_client)

        time.sleep(900)


if __name__ == "__main__":
    api_helper = APIHelper()
    tw_api, mongo_client = api_helper.create_api()
    config.logger.info("App started")
    run(tw_api, mongo_client)

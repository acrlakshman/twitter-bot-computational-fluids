import tweepy
import time
from langdetect import detect
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


def pull_tweets(tw_api, mongo_client):
    for hash_tag in config.HASH_TAGS:
        if can_call_pull_tweets(mongo_client):
            tweets = tweepy.Cursor(tw_api.search, q="#" + hash_tag,
                                   tweet_mode="extended").items(config.NUM_TWEETS_TO_SEARCH)
            inc_api_call_counters(
                mongo_client, config.SEARCH_TWEETS_ID, config.SEARCH_TWEETS_LIMIT_WINDOW)

            db = mongo_client[config.MONGO_DB]
            pulled_list_coll = db[config.MONGO_COLL_PULLED_LIST]

            for tweet in tweets:
                if (not pulled_list_coll.find_one({"id_str": tweet.id_str})):
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
            # One could use doc.metadata["iso_language_code"] == 'en'
            if not (detect(doc["full_text"]) == 'en'):
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
            except tweepy.TweepError as e:
                config.logger.error(
                    "During retweet for ID: {}; message: {}".format(doc["id_str"], e.args[0][0]['message']))
                discard_list_coll.insert_one(doc)
                pulled_list_coll.delete_one({"id_str": doc["id_str"]})

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
                         "num_tweets_to_search": config.NUM_TWEETS_TO_SEARCH,
                         "pull_tweets_interval_in_minutes": int(config.PULL_TWEETS_INTERVAL.seconds / 60),
                         "pause_app": config.PAUSE_APP,
                         "updatedAt": time_now, "createdAt": time_now})

        config.logger.debug("Created config collection")
        config.logger.debug("\thash tags: {}".format(config.HASH_TAGS))
        config.logger.debug("\tnum tweets to search: {}".format(
            config.NUM_TWEETS_TO_SEARCH))
        config.logger.debug("\tpull tweets interval: {}".format(
            config.PULL_TWEETS_INTERVAL))

    for hash_tag in config.HASH_TAGS:
        config.logger.debug("\t\thash_tag: {}".format(hash_tag))


def run(tw_api, mongo_client):
    while True:
        config.logger.info("App is running")
        initialize(mongo_client)

        if not config.PAUSE_APP:
            pull_tweets(tw_api, mongo_client)
            process_pulled_tweets(tw_api, mongo_client)

        time.sleep(30)


if __name__ == "__main__":
    api_helper = APIHelper()
    tw_api, mongo_client = api_helper.create_api()
    config.logger.info("App started")
    run(tw_api, mongo_client)

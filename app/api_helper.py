import tweepy
import logging
from pymongo import MongoClient
import config


class APIHelper:

    def __init__(self):
        return

    def print_tokens(self):
        print('API_KEY: {}, API_KEY_SECRET: {}'.format(
            config.TWITTER_API_KEY, config.TWITTER_API_KEY_SECRET))
        print('ACCESS_TOKEN: {}, ACCESS_TOKEN_SECRET: {}'.format(
            config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET))

    def create_api(self):
        # self.print_tokens()
        auth = tweepy.OAuthHandler(
            config.TWITTER_API_KEY, config.TWITTER_API_KEY_SECRET)
        auth.set_access_token(config.TWITTER_ACCESS_TOKEN,
                              config.TWITTER_ACCESS_TOKEN_SECRET)
        tw_api = tweepy.API(auth, wait_on_rate_limit=True,
                            wait_on_rate_limit_notify=True)

        try:
            tw_api.verify_credentials()
        except Exception as e:
            config.logger.error("Error creating API", exc_info=True)
            raise e
        config.logger.info("API created")

        mongo_client = MongoClient(config.MONGO_HOST, config.MONGO_PORT,
                                   username=config.MONGO_USER, password=config.MONGO_PASSWORD)
        return tw_api, mongo_client

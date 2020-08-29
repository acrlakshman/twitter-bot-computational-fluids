# Twitter bot that shares computational research

[@cfdspace](https://twitter.com/cfdspace)

### Hi,  I am a twitter bot and my goal is to share all computational research at one place.

## What do I do?

I search twitter feed every few minutes for some hashtags, focused on computational research and I retweet them for now.

## Can you make me do something else?

Sure you can, just fork me, change some code logic or default hashtags that suits your needs and deploy it as detailed below. But, please put me only to good use.

## Can you tune parameters without restarting me?

Yes you can. Connect to mongodb and change the values in the collection `config`. Some of the things you can do right now are:

- Change number of tweets that I can search for each time I make API call
- Pause me by setting `pause_app: true`. I won't talk to twitter :smile:
- Change hashtags for which I can scan twitter to find content
- Add or remove inclusion or exclusion strings that will be scanned in the full tweet before processing
- Add or remove users whose tweets won't be retweeted

## Want to know a little more on how I work?

- I scan for some tweets with predefined hashtags
- I store them in a database to do further processing. This avoids me to make too many API calls
- I scan for some metadata and post tweets that meet predefined criteria and save both posted tweets and discarded tweets
- Posted and discarded list are used to avoid spamming content. In future I will periodically clean these databases
- `Poll vs Stream`: Currently I rely on polling
- `Context analysis`: For now I can't handle this, but you can extend me to do that

## What hashtags I handle by default?

- `computationalfluiddynamics`
- `multiphaseflows`
- `volumeoffluid`
- `latticeboltzmann`

# Ingredients used

- [tweepy](https://pypi.org/project/tweepy/)
- [pymongo](https://pypi.org/project/pymongo/)
- [mongodb](https://github.com/mongodb/mongo)

## Docker images

* [twitter_cfdspace_bot](https://hub.docker.com/repository/docker/acrlakshman/twitter_cfdspace_bot)

# Note

* This app uses a persistent database, which keeps growing and will consume disk space. For now you need to manually perform the cleanup and keep an eye on the space used by mongodb. I will update the code to automate such that app does this automatically while it is running.
* Any changes made to the source code in `app/` requires rebuilding docker image.

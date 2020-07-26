# Deploy bot

Bot can be run either locally or on a server. There are many blog posts that describe how to deploy twitter bot on Amazon EC2, AWS Lambda, digitalocean, etc. Some randomly selected references are included in the bottom of this page. Here I will describe how I deployed [cfdspace](https://twitter.com/cfdspace) bot.

---

## Server space

I used digitalocean server space to run a docker container for this bot.

* [digitalocean](https://m.do.co/c/c647ddbfcfd9)
  * Above link includes a referral code, which when used, you will get $100 in credit over 60 days. Once you spent $25, I will get $25. Feel free to either create account using above code or create without referral.

_Please note that, to run this bot, you need not get a new server space, you could use your local machine too, as long as you have docker installed and can make sure to restart the bot when system restarts or the like scenarios._

---

## Docker

Install [docker](https://www.docker.com/) using one of the following links

* Linux: [get.docker.com](https://get.docker.com/)
* Mac: [Docker Desktop for Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac)
* Windows: [Docker Desktop for Windows](https://hub.docker.com/editions/community/docker-ce-desktop-windows)

### Installation instructions for docker

If you need detailed installation instructions for docker installation on each operating system, please go through these links

* Linux: [Install docker on Ubuntu](https://youtu.be/bwHIUN9gti0?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=211)
  * Time: [3:31](https://youtu.be/bwHIUN9gti0?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=211) to [4:50](https://youtu.be/bwHIUN9gti0?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=290)
* Mac: [Install docker on Mac](https://youtu.be/yWYfdam9iy4?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=129)
  * Time: [2.09](https://youtu.be/yWYfdam9iy4?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=129) to [3:27](https://youtu.be/yWYfdam9iy4?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=207)
* Windows: [Install docker on Windows](https://youtu.be/K_7wavPEtCc?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=112)
  * Time: [1:52](https://youtu.be/K_7wavPEtCc?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=112) to [6:26](https://youtu.be/K_7wavPEtCc?list=PL14zCGMQYkUprMVMXT-4-J1AIFYPEQmy-&t=386)

### Install docker-compose (optional)

* This bot can be deployed either using `docker-compose` or `docker stack`. If you prefer to deploy using `docker-compose`, make sure to have that installed.
  * Installation instructions: https://docs.docker.com/compose/install/

---

## Change `hashtags`

Before deploying, change the default hashtags to suite your needs.

`app/config.py`
  * Add `hashtag` (excluding `#`) of your choice to `HASH_TAGS_DEFAULT = ['hashtag']`

### Change `hashtags` during runtime

* Connect to `mongodb` and edit the field `hash_tags` in the collection `config`

_String `cfdspace` is used in few places in the source code (under `app/`), you may change that to your desired string or to match it with the name of your bot_

---

## Deploy bot

### Using docker-compose

#### Deploy

- Clone and configure the scripts

```sh
git clone https://github.com/acrlakshman/twitter-bot-computational-fluids twitter-bot
cd twitter-bot
mkdir -p logs db
```

- Enter API keys and ACCESS tokens in `docker-compose.yml`
- Enter desired credentials for mongodb admin.
- Start containers

```sh
docker-compose up -d
```

#### Stop

```sh
docker-compose down -v
```

### Using docker stack

#### Deploy

Make sure to create swarm

```sh
docker swarm init
# or
docker swarm init --advertise-addr <MANAGER_NODE_IP>
```

```sh
git clone https://github.com/acrlakshman/twitter-bot-computational-fluids twitter-bot
cd twitter-bot
mkdir -p logs db
```

- Enter API keys and ACCESS tokens in `docker-stack.yml`
- Enter desired credentials for mongodb admin.
- Start containers

```sh
docker stack deploy -c docker-stack.yml cfdspace_stack
```

#### Stop

```sh
docker stack rm cfdspace_stack
```

### Database and logs

- Database persists in the volume `db`
- App logs are stored in `logs/cfdspace.log`

---

**Some blog posts:**

* https://realpython.com/twitter-bot-python-tweepy/
* https://www.digitalocean.com/community/tutorials/how-to-create-a-twitterbot-with-python-3-and-the-tweepy-library
* https://victoria.dev/blog/running-a-free-twitter-bot-on-aws-lambda/
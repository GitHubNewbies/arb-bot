
# V3 Arbitrage Bot

**Build date:** 2025-04-19T22:51:12.534908 UTC

Quick start:

```bash
git clone <repo>  # if using git
cp .env.template .env  # fill in keys
pip install -r requirements.txt
python v3_bot.py
```

To run dashboard:
```bash
streamlit run dashboard.py
```

Docker one‑liner:
```bash
docker build -t v3bot .
docker run --env-file .env v3bot
```
# on server 

mkdir arb-bot
cd arb-bot

## connect to server in one terminal
ssh -i '~/Desktop/lightsail_keys/arb-bot-key' ubuntu@52.199.55.148

## Open another terminal from local machine to server
scp -r -i '~/Desktop/lightsail_keys/arb-bot-key' /Users/other/desktop/v3_arbitrage_bot_bundle ubuntu@52.199.55.148:/home/ubuntu/arb-bot

scp -r -i '~/Desktop/lightsail_keys/arb-bot-key' /Users/other/desktop/v3_arbitrage_bot_bundle/dashboard.py ubuntu@52.199.55.148:/home/ubuntu/arb-bot/v3_arbitrage_bot_bundle/

scp -r -i '~/Desktop/lightsail_keys/arb-bot-key' /Users/other/desktop/v3_arbitrage_bot_bundle/.env.template ubuntu@52.199.55.148:/home/ubuntu/arb-bot/v3_arbitrage_bot_bundle/


## Steps to configure and build
cp .env.template .env 
nano .env
## fill in keys 

## Install initial reqs 
sudo apt update && sudo apt upgrade
sudo apt install python3-pip
pip install -r requirements.txt --break-system-packages
python3 v3_bot.py

# Next
sudo apt install python3.12-venv
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit

## close terminal window, open new one

sudo snap install docker 
sudo docker build -t v3bot .


cd arb-bot/v3_arbitrage_bot_bundle/
 source .venv/bin/activate

streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

## needed as reqs within the .venv
pip install ccxt
pip install python-dotenv

mv env.template .env.template
import os
import ccxt
import pprint
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")

binance = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret_key
})

# 잔고 조회
balance = binance.fetch_balance()
print(balance['USDT'])

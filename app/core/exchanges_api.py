import pybit.exceptions
import requests
import logging

from pybit.unified_trading import HTTP
from pybit.exceptions import FailedRequestError, InvalidRequestError

# logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(name)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)


def get_price_binance(coin_ticker: str, base_coin: str) -> float:

    coin_ticker = coin_ticker.upper()
    base_coin = base_coin.upper()

    query = "https://api.binance.com/api/v3/ticker/price?symbol="+coin_ticker+base_coin
    r = ""

    try:
        r = requests.get(query)
        return float(r.json()["price"])
    except requests.exceptions.HTTPError as err:
        logger.error("HTTPError Binance API: ", err)
    except requests.exceptions.ConnectionError as err:
        logger.error("ConnectionError Binance API: ", err)
    except KeyError as err:
        logger.error(f"Bad response Binance API: {r.text}. error: {err}")


def get_price_bybit(coin_ticker: str, base_coin: str) -> float:

    coin_ticker = coin_ticker.upper()
    base_coin = base_coin.upper()

    try:
        session = HTTP(testnet=False)
        return float(session.get_tickers(
            category="spot",
            symbol=coin_ticker+base_coin,
        )["result"]['list'][0]["lastPrice"])
    except FailedRequestError as err:
        logger.error("FailedRequestError Bybit API: ", err)
    except InvalidRequestError as err:
        logger.error("InvalidRequestError Bybit API: ", err)
    except KeyError as err:
        logger.error(f"Bad response Bybit API: error: {err}")




def get_price(coin_ticker: str, exchange_name: str, base_coin: str) -> float:

    if exchange_name == "Binance":
        price = get_price_binance(coin_ticker=coin_ticker, base_coin=base_coin)
        return price
    elif exchange_name == "Bybit":
        price = get_price_bybit(coin_ticker=coin_ticker, base_coin=base_coin)
        return price
    else:
        print("Not supported exchange")
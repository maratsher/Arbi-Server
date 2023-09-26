import logging
from abc import ABC, abstractmethod
from enum import Enum
from binance.client import Client
from binance.enums import *
import ccxt


class ExchangeName(Enum):
    BINANCE = "Binance"
    BYBIT = "Bybit"


class BinanceError(Exception):
    pass


class BybitError(Exception):
    pass


class ExchangeInsufficientFunds(Exception):
    pass


class OrderStatus(Enum):
    NEW = "NEW",
    PARTIALLY_FILLED = "PARTIALLY_FILLED",
    FILLED = "FILLED",
    CANCELED = "CANCELED",
    PENDING_CANCEL = "PENDING_CANCEL",
    REJECTED = "REJECTED",
    EXPIRED = "EXPIRED"


class OrderType(Enum):
    MARKET = "MARKET",
    LIMIT = "LIMIT"


class OrderSide(Enum):
    SELL = "SELL",
    BUY = "BUY"


class Exchange(ABC):
    order_status_map: dict
    order_type_map: dict
    order_side_map: dict

    def __init__(self, name: ExchangeName, api_key: str, api_secret: str, test=False):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.test = test
        self.session = None

    @staticmethod
    @abstractmethod
    def make_symbol(coin1, coin2):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                    quantity: float, price: float) -> (tuple[str, str] | None):
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        pass

    @abstractmethod
    def check_order(self, symbol: str, order_id: int) -> OrderStatus:
        pass

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def get_balance(self, symbol) -> tuple[float, float]:
        pass


class BinanceExchange(Exchange):
    order_type_map = {
        OrderType.LIMIT: "LIMIT",
        OrderType.MARKET: "MARKET"
    }

    order_side_map = {
        OrderSide.SELL: "SELL",
        OrderSide.BUY: "BUY"
    }

    order_status_map = {
        "NEW": OrderStatus.NEW,
        "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
        "FILLED": OrderStatus.FILLED,
        "CANCELED": OrderStatus.CANCELED,
        "PENDING_CANCEL": OrderStatus.PENDING_CANCEL,
        "REJECTED": OrderStatus.REJECTED,
        "EXPIRED": OrderStatus.EXPIRED
    }

    def __init__(self, api_key, api_secret, test=False):
        super().__init__(ExchangeName.BINANCE, api_key, api_secret, test)

    @staticmethod
    def make_symbol(coin1: str, coin2: str):
        return str.upper(coin1 + coin2)

    def connect(self):
        self.session = Client(self.api_key, self.api_secret, testnet=self.test)

    def place_order(self, symbol, side, order_type, quantity, price, time_in_force=Client.TIME_IN_FORCE_GTC):
        try:
            if price <= 0 or quantity <= 0:
                logging.error(f"{self.name} Error placing order: Price and quantity must be positive numbers.")
                return None

            order = self.session.create_order(
                symbol=symbol,
                side=self.order_side_map.get(side),
                type=self.order_type_map.get(order_type),
                quantity=quantity,
                price=price,
                timeInForce=time_in_force,
            )

            status = order.get("status")
            if status is None:
                logging.error(f"{self.name} Error placing order: Order status not received.")
                return None

            return str(order['orderId']), self.order_status_map.get(status)
        except Exception as e:
            logging.error(f"{self.name} Error placing order: {e}")
            raise BinanceError(f"{self.name} Error placing order: {e}")

    def cancel_order(self, symbol, order_id):
        try:
            res = self.session.cancel_order(symbol=symbol, orderId=order_id)
            if res['status'] == 'CANCELED':
                return True
        except Exception as e:
            logging.error(f"{self.name} Error cancelling order: {e}")
            raise BinanceError(f"{self.name} Error cancelling order: {e}")
        return False

    def check_order(self, symbol, order_id):
        try:
            order_info = self.session.get_order(symbol=symbol, orderId=order_id)
            return self.order_status_map.get(order_info["status"])
        except Exception as e:
            logging.error(f"{self.name} Error checking order status: {e}")
            raise BinanceError(f"{self.name} Error checking order status: {e}")

    def get_price(self, symbol):
        try:
            ticker = self.session.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            return price
        except Exception as e:
            logging.error(f"{self.name} Error getting price: {e}")
            raise BinanceError(f"{self.name} Error getting price: {e}")

    def get_balance(self, symbol):
        try:
            balance = self.session.get_asset_balance(asset=symbol)
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            return free_balance, locked_balance
        except Exception as e:
            logging.error(f"{self.name} Error getting balance: {e}")
            raise BinanceError(f"{self.name} Error getting balance: {e}")

    def close(self):
        if self.session:
            self.session.close_connection()

    def __del__(self):
        self.close()


class BybitExchange(Exchange):
    order_type_map = {
        OrderType.LIMIT: "limit",
        OrderType.MARKET: "market"
    }

    order_side_map = {
        OrderSide.SELL: "sell",
        OrderSide.BUY: "buy"
    }

    order_status_map = {
        "NEW": OrderStatus.NEW,
        "PARTIALLYFILLED": OrderStatus.PARTIALLY_FILLED,
        "FILLED": OrderStatus.FILLED,
        "CANCELLED": OrderStatus.CANCELED,
        "PENDINGCANCEL": OrderStatus.PENDING_CANCEL,
        "REJECTED": OrderStatus.REJECTED,
        "EXPIRED": OrderStatus.EXPIRED
    }

    def __init__(self, api_key, api_secret, test=False):
        super().__init__(ExchangeName.BYBIT, api_key, api_secret, test)

    @staticmethod
    def make_symbol(coin1: str, coin2: str):
        return str.upper(coin1) + "/" + str.upper(coin2)

    def connect(self):
        self.session = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'test': self.test
        })
        if self.test:
            self.session.set_sandbox_mode(True)

    def place_order(self, symbol, side, order_type, quantity, price, **kwargs):
        try:
            if price <= 0 or quantity <= 0:
                logging.error(f"{self.name} Error placing order: Price and quantity must be positive numbers.")
                return None

            order_response = self.session.create_order(
                symbol,
                self.order_type_map.get(order_type),
                self.order_side_map.get(side),
                quantity,
                price,
                **kwargs
            )

            order_id = order_response['info']['orderId']
            status = order_response['info']['status']

            return order_id, self.order_status_map.get(status)
        except ccxt.BaseError as e:
            logging.error(f"{self.name} Error placing order: {e}")
            raise BybitError(f"{self.name} Error placing order: {e}")

    def cancel_order(self, symbol, order_id):
        try:
            order_response = self.session.cancel_order(order_id, symbol)
            order_id = order_response['info']['orderId']

            status = self.check_order(symbol, order_id)

            if status == None:
                return True
        except ccxt.BaseError as e:
            logging.error(f"{self.name} Error cancelling order: {e}")
            raise BybitError(f"{self.name} Error cancelling order: {e}")
        return False

    def check_order(self, symbol, order_id):
        try:
            order_response = self.session.fetch_order(order_id, symbol)
            order_status = order_response['info']['status']

            return self.order_status_map.get(order_status)
        except ccxt.BaseError as e:
            logging.error(f"{self.name} Error checking order status: {e}")
            raise BybitError(f"{self.name} Error checking order status: {e}")

    def get_price(self, symbol):
        try:
            ticker = self.session.fetch_ticker(symbol)
            price = ticker.get('last')

            return price
        except ccxt.BaseError as e:
            logging.error(f"{self.name} Error getting price: {e}")
            raise BybitError(f"{self.name} Error getting price: {e}")

    def get_balance(self, symbol):
        try:
            balance = self.session.fetch_balance({'type': 'spot'})

            # Добавим отладочную информацию для удобства отслеживания
            logging.debug(f"{self.name} Fetch balance response: {balance}")

            # Убедимся, что у нас есть информация о доступных и заблокированных балансах
            if 'free' in balance and 'used' in balance:
                free_balance = balance['free'].get(symbol, 0.0)
                locked_balance = balance['used'].get(symbol, 0.0)

                return float(free_balance), float(locked_balance)
            else:
                logging.error(f"{self.name} Balance data does not contain 'free' or 'used' fields.")
        except ccxt.BaseError as e:
            logging.error(f"{self.name} Error getting balance: {e}")
            raise BybitError(f"{self.name} Error getting balance: {e}")
        return None

    def close(self):
        del self.session

    def __del__(self):
        self.close()

import time
import json
from pybit import usdt_perpetual
from pprint import pprint
import datetime
from decimal import *

# 수수료: 테이커: 0.06%, 메이커: 0.01%

# 대략 미니멈: 분당 60회


class BybitApi:
    def __init__(self,  api_key: str = '', secret_key: str = ''):
        self.api = usdt_perpetual.HTTP(
            endpoint='https://api.bybit.com',
            api_key=api_key,
            api_secret=secret_key,
        )
        self.symbol_info = dict()
        for v in self.api.query_symbol()['result']:
            self.symbol_info[v['alias']] = {
                'order_min_size': Decimal(str(v['lot_size_filter']['qty_step'])),
                'price_min_size': Decimal(str(v['price_filter']['tick_size'])),
                'symbol_amount_min': Decimal(str(v['lot_size_filter']['min_trading_qty']))
            }

    def get_orderbook(self, symbol="BTCUSDT") -> dict:
        data = self.api.orderbook(symbol=symbol)["result"]
        bids = []
        asks = []
        for v in data:
            if v['side'] == "Buy":
                bids.append([v['price'], v['size']])
            if v['side'] == "Sell":
                asks.append([v['price'], v['size']])
        bids = sorted(bids, key=lambda x: x[0], reverse=True)
        asks = sorted(asks, key=lambda x: x[0], reverse=True)
        return {
            'bids': bids,
            'asks': asks,
        }

    def get_best_bid_ask(self, symbol='BTCUSDT') -> dict:
        orderbook = self.get_orderbook(symbol)
        best_bid = Decimal(orderbook['bids'][0][0])
        best_2_bid = Decimal(orderbook['bids'][1][0])
        best_ask = Decimal(orderbook['asks'][-1][0])
        best_2_ask = Decimal(orderbook['asks'][-2][0])
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'best_2_bid': best_2_bid,
            'best_2_ask': best_2_ask,
        }

    # return post order id
    def post_order(self, symbol='BTCUSDT', side='buy', price='100.0', volume='0.01',
                   ord_type='limit', is_reduce=False, is_post_only=False):
        if side == 'buy':
            side = 'Buy'
        elif side == 'sell':
            side = 'Sell'
        if ord_type == 'limit':
            ord_type = 'Limit'
        elif ord_type == 'market':
            ord_type = 'Market'

        if is_post_only:
            time_in_force = "PostOnly"
        else:
            time_in_force = "GoodTillCancel"

        order = {
            "symbol": symbol,
            "order_type": ord_type,
            "side": side,
            "price": price,
            "qty": volume,
            "time_in_force": time_in_force,
            "reduce_only": is_reduce,
            "close_on_trigger": is_reduce,
        }
        result = self.api.place_active_order(**order)["result"]
        order_id = result["order_id"]
        return order_id

    # return {'symbol': 'BTCUSDT', 'long': 0, 'short': 0.001, 'unrealised_pnl': -0.0192, 'short_leverage': 2.2,
    # 'long_leverage': 0}
    def get_position(self, symbol="BTCUSDT") -> dict:
        result = self.api.my_position(symbol=symbol)["result"]
        position = {"symbol": symbol, "long": Decimal(0), "short": Decimal(0), "unrealised_pnl": Decimal(0)}
        for v in result:
            pprint(v)
            if v["side"] == "Buy":
                position["long"] += abs(Decimal(str(v["size"])))
                position["unrealised_pnl"] += Decimal(str(v["unrealised_pnl"]))
                if v["position_margin"] != Decimal(0):
                    position["long_leverage"] = Decimal(str(v["position_value"])) / \
                                                (Decimal(str(v["position_margin"])) + Decimal(str(v["unrealised_pnl"])))
                else:
                    position["long_leverage"] = Decimal(0)
            if v["side"] == "Sell":
                position["short"] += abs(Decimal(str(v["size"])))
                position["unrealised_pnl"] += Decimal(str(v["unrealised_pnl"]))
                if v["position_margin"] != Decimal(0):
                    position["short_leverage"] = Decimal(str(v["position_value"])) / \
                                                (Decimal(str(v["position_margin"])) + Decimal(str(v["unrealised_pnl"])))
                else:
                    position["short_leverage"] = Decimal(0)

        return position

    # return current price
    def get_current_price(self, symbol='BTCUSDT') -> float:
        data = self.get_best_bid_ask(symbol)
        mid_price = (data['best_bid'] + data['best_ask']) / 2
        return mid_price

    # return canceled order count
    def cancel_all_orders(self, symbol='BTCUSDT') -> int:
        result = self.api.cancel_all_active_orders(symbol=symbol)['result']
        if not result:
            return 0
        canceled_order_count = len(result)
        return canceled_order_count

    # get_history_price last candle is recent candle
    # timeframe: 1 3 5 15 30 60 120 240 360 720 "D" "M" "W"
    # limit: max: 200
    def get_history_price(self, symbol='BTCUSDT', timeframe="1m", limit=3) -> list:
        if timeframe == '1m':
            timeframe = 1
        elif timeframe == '3m':
            timeframe = 3
        elif timeframe == '5m':
            timeframe = 5
        elif timeframe == '15m':
            timeframe = 15
        elif timeframe == '30m':
            timeframe = 30
        elif timeframe == '1h':
            timeframe = 60
        elif timeframe == '2h':
            timeframe = 120
        elif timeframe == '4h':
            timeframe = 240
        elif timeframe == '6h':
            timeframe = 360
        elif timeframe == '12h':
            timeframe = 720
        elif timeframe == '1d':
            timeframe = 1440

        from_time = int(time.time())
        pprint(from_time)
        from_time = from_time - timeframe * (limit * 100)
        pprint(from_time)

        if timeframe == 1440:
            timeframe = "D"

        data = self.api.query_kline(symbol=symbol, interval=timeframe, limit=limit + 1, from_time=from_time)
        result = data["result"]
        candle_list = list()
        for v in result:
            candle_list.append({
                'date': datetime.datetime.fromtimestamp(int(v['open_time'])),
                'open': Decimal(v['open']),
                'high': Decimal(v['high']),
                'low': Decimal(v['low']),
                'close': Decimal(v['close']),
                'volume': Decimal(v['volume'])
            })
        return candle_list

    # return {'BTC': 1.129e-05, 'USDT': 313.6890709, 'XRP': 0.006363}
    def get_balance(self) -> dict:
        balance = self.api.get_wallet_balance()['result']
        balance_dict = dict()
        for v in balance:
            wallet_balance = Decimal(str(balance[v]['wallet_balance']))
            if wallet_balance == Decimal(0):
                continue
            balance_dict[v] = wallet_balance
        return balance_dict


if __name__ == "__main__":
    with open("./mybit.json", 'r') as f:
        apis = json.load(f)
        f.close()
    k = apis["KEY"]
    sr = k = apis["SECRET"]
    bybit = BybitApi(k, sr)
    print(bybit.get_current_price())
    
    
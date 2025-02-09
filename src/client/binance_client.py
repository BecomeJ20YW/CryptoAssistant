import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode

class BinanceClient:
    def __init__(self, api_key, api_secret, testnet=False):
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.BASE_URL = 'https://testnet.binancefuture.com' if testnet else 'https://fapi.binance.com'
        self.testnet = testnet

    def _get_timestamp(self):
        return int(time.time() * 1000)

    def _generate_signature(self, params):
        query_string = urlencode(params)
        try:
            signature = hmac.new(
                self.API_SECRET.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
            raise ValueError(f"签名生成失败: {str(e)}, 请检查API密钥格式是否正确")

    def _send_request(self, method, endpoint, params=None, signed=True):
        url = f"{self.BASE_URL}{endpoint}"
        headers = {'X-MBX-APIKEY': self.API_KEY}
        
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = self._get_timestamp()
            params['signature'] = self._generate_signature(params)
        
        try:
            response = requests.request(method, url, headers=headers, params=params)
            
            # 检查响应状态码
            if response.status_code != 200:
                error_msg = response.json().get('msg', '未知错误')
                raise ValueError(f"API请求失败 (状态码: {response.status_code}): {error_msg}")
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"网络请求失败: {str(e)}")

    def get_exchange_info(self):
        """获取交易规则"""
        endpoint = '/fapi/v1/exchangeInfo'
        return self._send_request('GET', endpoint, signed=False)

    def get_futures_account(self):
        """获取账户信息"""
        endpoint = '/fapi/v2/account'
        return self._send_request('GET', endpoint)

    def get_mark_price(self, symbol):
        """获取标记价格"""
        endpoint = '/fapi/v1/premiumIndex'
        params = {'symbol': symbol}
        return self._send_request('GET', endpoint, params, signed=False)

    def place_order(self, symbol, side, order_type, quantity, price=None, reduce_only=False):
        """
        下单函数
        :param symbol: 交易对
        :param side: 方向 ("BUY" 或 "SELL")
        :param order_type: 订单类型 ("LIMIT" 或 "MARKET")
        :param quantity: 数量
        :param price: 价格 (限价单必需)
        :param reduce_only: 是否只减仓
        """
        endpoint = '/fapi/v1/order'
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'reduceOnly': 'true' if reduce_only else 'false'
        }

        if order_type == 'LIMIT':
            if not price:
                raise ValueError("限价单必须指定价格")
            params['price'] = price
            params['timeInForce'] = 'GTC'  # 有效直到取消

        return self._send_request('POST', endpoint, params)

    def change_leverage(self, symbol, leverage):
        """
        修改杠杆倍数
        :param symbol: 交易对
        :param leverage: 杠杆倍数 (1-125)
        """
        endpoint = '/fapi/v1/leverage'
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._send_request('POST', endpoint, params) 
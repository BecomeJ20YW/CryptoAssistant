import requests
import time
import hmac
import hashlib
import sys
import json
from urllib.parse import urlencode
from config import API_KEY, API_SECRET
from tabulate import tabulate

class BinanceClient:
    def __init__(self, api_key, api_secret):
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.BASE_URL = 'https://fapi.binance.com'

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

    def _send_request(self, method, endpoint, params=None):
        url = f"{self.BASE_URL}{endpoint}"
        headers = {'X-MBX-APIKEY': self.API_KEY}
        
        if params is None:
            params = {}
            
        params['timestamp'] = self._get_timestamp()
        
        try:
            params['signature'] = self._generate_signature(params)
            response = requests.request(method, url, headers=headers, params=params)
            
            # 检查响应状态码
            if response.status_code != 200:
                error_msg = response.json().get('msg', '未知错误')
                raise ValueError(f"API请求失败 (状态码: {response.status_code}): {error_msg}")
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"网络请求失败: {str(e)}")

    def get_futures_account(self):
        endpoint = '/fapi/v2/account'
        return self._send_request('GET', endpoint)

    def get_mark_price(self, symbol):
        endpoint = '/fapi/v1/premiumIndex'
        params = {'symbol': symbol}
        return self._send_request('GET', endpoint, params)

def format_number(number, decimals=2):
    """格式化数字，添加千位分隔符"""
    try:
        return f"{float(number):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(number)

def get_futures_account_info():
    try:
        # 初始化客户端
        client = BinanceClient(API_KEY, API_SECRET)
        
        # 获取账户信息
        futures_account = client.get_futures_account()
        positions = futures_account['positions']
        
        # 过滤出有持仓的合约
        active_positions = [p for p in positions if float(p['positionAmt']) != 0]
        
        # 打印账户总览
        total_wallet_balance = float(futures_account['totalWalletBalance'])
        total_unrealized_profit = float(futures_account['totalUnrealizedProfit'])
        
        print("\n=== 账户总览 ===")
        print(f"钱包余额: {format_number(total_wallet_balance)} USDT")
        print(f"未实现盈亏: {format_number(total_unrealized_profit)} USDT")
        print(f"总资产: {format_number(total_wallet_balance + total_unrealized_profit)} USDT")
        
        # 打印持仓信息
        if active_positions:
            print("\n=== 当前持仓 ===")
            position_data = []
            for position in active_positions:
                symbol = position['symbol']
                position_amt = float(position['positionAmt'])
                entry_price = float(position['entryPrice'])
                unrealized_profit = float(position['unrealizedProfit'])
                leverage = float(position['leverage'])
                
                # 获取当前市价
                mark_price_info = client.get_mark_price(symbol)
                mark_price = float(mark_price_info['markPrice'])
                
                # 计算收益率
                if position_amt != 0:
                    roi = (unrealized_profit / (abs(position_amt) * entry_price / leverage)) * 100
                else:
                    roi = 0
                
                position_data.append([
                    symbol,
                    "多" if position_amt > 0 else "空",
                    format_number(abs(position_amt), 4),
                    format_number(entry_price, 4),
                    format_number(mark_price, 4),
                    f"{leverage}x",
                    format_number(unrealized_profit),
                    f"{format_number(roi)}%"
                ])
            
            headers = ["交易对", "方向", "数量", "开仓价", "标记价", "杠杆", "未实现盈亏", "收益率"]
            print(tabulate(position_data, headers=headers, tablefmt="grid", disable_numparse=True))
        else:
            print("\n当前没有持仓")
            
    except ValueError as e:
        print(f"错误: {str(e)}")
    except Exception as e:
        print(f"发生未知错误: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            print("\n详细错误信息:")
            traceback.print_tb(e.__traceback__)

if __name__ == "__main__":
    # 设置标准输出编码
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            # Python 3.7及以下版本
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    
    get_futures_account_info() 
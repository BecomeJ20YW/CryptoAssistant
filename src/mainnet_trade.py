import sys
from tabulate import tabulate
from src.client.binance_client import BinanceClient
from src.utils.formatter import format_number, format_position_info
from src.utils.trading import TradingUtils

def display_account_info(client):
    """显示账户信息"""
    try:
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
                # 获取当前市价
                mark_price_info = client.get_mark_price(position['symbol'])
                mark_price = float(mark_price_info['markPrice'])
                
                # 格式化持仓信息
                position_data.append(format_position_info(position, mark_price))
            
            headers = ["交易对", "方向", "数量", "开仓价", "标记价", "杠杆", "未实现盈亏", "收益率"]
            print(tabulate(position_data, headers=headers, tablefmt="grid", disable_numparse=True))
        else:
            print("\n当前没有持仓")
            
    except Exception as e:
        print(f"获取账户信息失败: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            print("\n详细错误信息:")
            traceback.print_tb(e.__traceback__)

def run_mainnet(api_key, api_secret):
    """运行主网程序"""
    try:
        client = BinanceClient(api_key, api_secret, testnet=False)
        trading_utils = TradingUtils(client)
        trading_utils.display_account_info(is_testnet=False)
    except Exception as e:
        print(f"程序运行错误: {str(e)}")
        sys.exit(1) 
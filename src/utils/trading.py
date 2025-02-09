from tabulate import tabulate
from src.utils.formatter import format_number, format_position_info

class TradingUtils:
    def __init__(self, client):
        self.client = client
        self.exchange_info = None
        self._load_exchange_info()
        
        # 常用交易对列表
        self.common_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT',
            'ADAUSDT', 'SOLUSDT', 'MATICUSDT', 'DOTUSDT', 'LTCUSDT'
        ]
    
    def _load_exchange_info(self):
        """加载交易规则信息"""
        try:
            self.exchange_info = self.client.get_exchange_info()
        except Exception as e:
            print(f"获取交易规则失败: {str(e)}")
            self.exchange_info = {'symbols': []}
    
    def get_symbol_filters(self, symbol):
        """获取交易对的规则过滤器"""
        if not self.exchange_info:
            return None
        
        for sym_info in self.exchange_info['symbols']:
            if sym_info['symbol'] == symbol:
                return {f['filterType']: f for f in sym_info['filters']}
        return None
    
    def get_available_symbols(self):
        """获取可交易的币对列表"""
        if not self.exchange_info:
            return self.common_symbols
            
        # 获取所有可交易的币对
        all_symbols = [sym['symbol'] for sym in self.exchange_info['symbols'] 
                      if sym['status'] == 'TRADING']
        
        # 将常用币对排在前面
        available_symbols = []
        for symbol in self.common_symbols:
            if symbol in all_symbols:
                available_symbols.append(symbol)
                all_symbols.remove(symbol)
        
        # 添加其他币对
        available_symbols.extend(sorted(all_symbols))
        return available_symbols
    
    def get_symbol_info(self, symbol):
        """获取币对的详细信息"""
        mark_price_info = self.client.get_mark_price(symbol)
        mark_price = float(mark_price_info['markPrice'])
        
        filters = self.get_symbol_filters(symbol)
        if not filters:
            return {
                'price': mark_price,
                'min_qty': 0.001,
                'step_size': 0.001,
                'min_notional': 5.0,
                'price_precision': 4,
                'quantity_precision': 3
            }
            
        lot_size = filters.get('LOT_SIZE', {})
        min_notional = filters.get('MIN_NOTIONAL', {})
        price_filter = filters.get('PRICE_FILTER', {})
        
        # 计算价格精度
        tick_size = float(price_filter.get('tickSize', '0.0001'))
        price_precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0
        
        # 计算数量精度
        step_size = float(lot_size.get('stepSize', '0.001'))
        quantity_precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0
        
        return {
            'price': mark_price,
            'min_qty': float(lot_size.get('minQty', 0.001)),
            'step_size': step_size,
            'min_notional': float(min_notional.get('notional', 5.0)),
            'price_precision': price_precision,
            'quantity_precision': quantity_precision
        }
    
    def calculate_quantity(self, symbol, quantity, price):
        """根据交易规则计算有效的下单数量"""
        filters = self.get_symbol_filters(symbol)
        if not filters:
            return quantity
            
        lot_size = filters.get('LOT_SIZE', {})
        min_qty = float(lot_size.get('minQty', 0))
        max_qty = float(lot_size.get('maxQty', float('inf')))
        step_size = float(lot_size.get('stepSize', 0))
        
        # 确保数量在最小和最大范围内
        quantity = max(min_qty, min(max_qty, quantity))
        
        # 根据步长调整数量
        if step_size > 0:
            quantity = round(quantity / step_size) * step_size
            
        # 处理精度
        precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0
        return round(quantity, precision)
    
    def check_price_filter(self, symbol, price):
        """检查价格是否符合规则"""
        filters = self.get_symbol_filters(symbol)
        if not filters:
            return True
            
        price_filter = filters.get('PRICE_FILTER', {})
        min_price = float(price_filter.get('minPrice', 0))
        max_price = float(price_filter.get('maxPrice', float('inf')))
        tick_size = float(price_filter.get('tickSize', 0))
        
        if price < min_price or price > max_price:
            raise ValueError(f"价格必须在 {min_price} 和 {max_price} 之间")
            
        if tick_size > 0:
            valid_price = round(price / tick_size) * tick_size
            if abs(valid_price - price) > 1e-8:  # 允许小误差
                raise ValueError(f"价格必须是 {tick_size} 的整数倍")
        
        return True
    
    def validate_order(self, symbol, side, quantity, price=None):
        """验证订单参数"""
        filters = self.get_symbol_filters(symbol)
        if not filters:
            return quantity
            
        # 检查最小名义价值
        min_notional = filters.get('MIN_NOTIONAL', {})
        min_value = float(min_notional.get('notional', 5.0))  # 默认5 USDT
        
        order_value = quantity * price if price else quantity * float(self.client.get_mark_price(symbol)['markPrice'])
        if order_value < min_value:
            raise ValueError(f"订单价值必须大于 {min_value} USDT")
            
        # 检查价格偏差限制
        percent_filter = filters.get('PERCENT_PRICE', {})
        if percent_filter:
            multiplier_up = float(percent_filter.get('multiplierUp', 1.1))
            multiplier_down = float(percent_filter.get('multiplierDown', 0.9))
            
            # 获取最新价格
            mark_price = float(self.client.get_mark_price(symbol)['markPrice'])
            
            # 计算允许的价格范围
            max_price = mark_price * multiplier_up
            min_price = mark_price * multiplier_down
            
            # 如果是限价单，检查价格是否在允许范围内
            if price and (price < min_price or price > max_price):
                raise ValueError(f"价格超出允许范围 ({format_number(min_price, 4)} - {format_number(max_price, 4)})")
            
        # 调整数量精度
        return self.calculate_quantity(symbol, quantity, price)
    
    def display_account_info(self, is_testnet=False):
        """显示账户信息"""
        try:
            # 获取账户信息
            futures_account = self.client.get_futures_account()
            positions = futures_account['positions']
            
            # 过滤出有持仓的合约
            active_positions = [p for p in positions if float(p['positionAmt']) != 0]
            
            # 打印账户总览
            total_wallet_balance = float(futures_account['totalWalletBalance'])
            total_unrealized_profit = float(futures_account['totalUnrealizedProfit'])
            
            print("\n=== 账户总览 ===")
            if is_testnet:
                print("当前为测试网环境")
            print(f"钱包余额: {format_number(total_wallet_balance)} USDT")
            print(f"未实现盈亏: {format_number(total_unrealized_profit)} USDT")
            print(f"总资产: {format_number(total_wallet_balance + total_unrealized_profit)} USDT")
            
            # 打印持仓信息
            if active_positions:
                print("\n=== 当前持仓 ===")
                position_data = []
                for position in active_positions:
                    # 获取当前市价
                    mark_price_info = self.client.get_mark_price(position['symbol'])
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

    def format_price(self, symbol, price):
        """格式化价格，确保符合精度要求"""
        info = self.get_symbol_info(symbol)
        return round(price, info['price_precision'])

    def format_quantity(self, symbol, quantity):
        """格式化数量，确保符合精度要求"""
        info = self.get_symbol_info(symbol)
        return round(quantity, info['quantity_precision']) 
import sys
from src.client.binance_client import BinanceClient
from src.utils.formatter import format_number
from src.utils.trading import TradingUtils

def place_test_order(client, trading_utils, symbol, side, quantity, use_market_order=False):
    """
    模拟下单函数
    :param use_market_order: 是否使用市价单
    """
    try:
        # 先设置杠杆
        leverage = 20  # 默认使用20倍杠杆
        client.change_leverage(symbol, leverage)
        print(f"\n已设置杠杆倍数: {leverage}x")
        
        # 获取当前市价和币对信息
        info = trading_utils.get_symbol_info(symbol)
        mark_price = info['price']
        
        # 验证并调整订单参数
        adjusted_quantity = trading_utils.validate_order(symbol, side, quantity, mark_price)
        formatted_quantity = trading_utils.format_quantity(symbol, adjusted_quantity)
        
        if use_market_order:
            # 下市价单
            order = client.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=formatted_quantity
            )
        else:
            # 计算限价单价格（买单略高于市价，卖单略低于市价，确保成交）
            price_offset = 0.001  # 0.1% 的价格偏移
            if side == 'BUY':
                price = mark_price * (1 + price_offset)
            else:
                price = mark_price * (1 - price_offset)
                
            # 格式化价格和数量，确保符合精度要求
            formatted_price = trading_utils.format_price(symbol, price)
            
            print(f"价格精度: {info['price_precision']}")
            print(f"数量精度: {info['quantity_precision']}")
            print(f"调整后价格: {formatted_price}")
            print(f"调整后数量: {formatted_quantity}")
                
            # 下限价单
            order = client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=formatted_quantity,
                price=formatted_price
            )
        
        print(f"\n=== 订单执行成功 ===")
        print(f"交易对: {order['symbol']}")
        print(f"方向: {'做多' if side == 'BUY' else '做空'}")
        print(f"数量: {order['origQty']}")
        if 'avgPrice' in order and order['avgPrice']:
            print(f"成交价: {format_number(float(order['avgPrice']), 4)}")
        elif 'price' in order and order['price']:
            print(f"价格: {format_number(float(order['price']), 4)}")
        print(f"订单状态: {order['status']}")
        
    except Exception as e:
        print(f"下单失败: {str(e)}")
        print("\n尝试使用替代方案...")
        try:
            # 如果市价单失败，尝试使用带有较大价格偏移的限价单
            price_offset = 0.05  # 5% 的价格偏移
            if side == 'BUY':
                price = mark_price * (1 + price_offset)
            else:
                price = mark_price * (1 - price_offset)
                
            formatted_price = trading_utils.format_price(symbol, price)
            
            print(f"使用限价单 - 价格: {formatted_price}")
            
            order = client.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=formatted_quantity,
                price=formatted_price
            )
            
            print(f"\n=== 订单执行成功 ===")
            print(f"交易对: {order['symbol']}")
            print(f"方向: {'做多' if side == 'BUY' else '做空'}")
            print(f"数量: {order['origQty']}")
            print(f"价格: {format_number(float(order['price']), 4)}")
            print(f"订单状态: {order['status']}")
            
        except Exception as e2:
            print(f"替代方案也失败了: {str(e2)}")

def select_trading_pair(trading_utils):
    """选择交易对"""
    available_symbols = trading_utils.get_available_symbols()
    
    print("\n=== 可选择的交易对 ===")
    print("常用交易对:")
    for i, symbol in enumerate(trading_utils.common_symbols, 1):
        if symbol in available_symbols:
            info = trading_utils.get_symbol_info(symbol)
            print(f"{i}. {symbol:<10} 当前价格: {format_number(info['price'], 4)} USDT")
    
    print("\n其他交易对示例:")
    for i, symbol in enumerate(available_symbols[len(trading_utils.common_symbols):], len(trading_utils.common_symbols)+1):
        if i > len(trading_utils.common_symbols) + 5:  # 只显示额外的5个
            break
        info = trading_utils.get_symbol_info(symbol)
        print(f"{i}. {symbol:<10} 当前价格: {format_number(info['price'], 4)} USDT")
    
    while True:
        choice = input("\n请选择交易对编号或直接输入交易对名称 (例如 BTCUSDT): ").strip().upper()
        try:
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(available_symbols):
                    return available_symbols[index]
            elif choice in available_symbols:
                return choice
            print("无效的选择，请重试")
        except ValueError:
            print("无效的输入，请重试")

def quick_test_trade(client, trading_utils):
    """快速测试交易功能"""
    try:
        # 默认配置
        symbol = 'XRPUSDT'
        side = 'BUY'
        quantity = 10  # 增加默认数量，确保满足最小订单价值
        
        # 获取币对信息
        info = trading_utils.get_symbol_info(symbol)
        print(f"\n=== 快速测试交易 ===")
        print(f"交易对: {symbol}")
        print(f"方向: 做多")
        print(f"数量: {quantity}")
        print(f"当前价格: {format_number(info['price'], 4)} USDT")
        print(f"订单价值: {format_number(info['price'] * quantity, 2)} USDT")
        print(f"最小下单数量: {info['min_qty']}")
        print(f"最小订单价值: {info['min_notional']} USDT")
        print(f"订单类型: 市价单")
        
        confirm = input("\n确认下单? (y/n): ").strip().lower()
        if confirm == 'y':
            place_test_order(client, trading_utils, symbol, side, quantity, use_market_order=True)
        else:
            print("已取消下单")
            
    except Exception as e:
        print(f"快速测试失败: {str(e)}")

def interactive_test_trade(client, trading_utils):
    """交互式测试交易功能"""
    while True:
        print("\n=== 测试交易菜单 ===")
        print("1. 开多单 (限价单)")
        print("2. 开空单 (限价单)")
        print("3. 修改杠杆")
        print("4. 查看账户状态")
        print("5. 快速测试 (XRPUSDT 多单 - 市价单)")
        print("6. 退出")
        
        choice = input("\n请选择操作 (1-6): ").strip()
        
        if choice == '1' or choice == '2':
            try:
                # 选择交易对
                symbol = select_trading_pair(trading_utils)
                if not symbol:
                    continue
                
                # 获取币对信息
                info = trading_utils.get_symbol_info(symbol)
                print(f"\n当前 {symbol} 价格: {format_number(info['price'], 4)} USDT")
                print(f"最小下单数量: {info['min_qty']}")
                print(f"最小订单价值: {info['min_notional']} USDT")
                
                quantity = input("请输入数量: ").strip()
                quantity = float(quantity)
                
                # 计算订单价值
                order_value = info['price'] * quantity
                print(f"订单价值: {format_number(order_value, 2)} USDT")
                
                confirm = input("\n确认下单? (y/n): ").strip().lower()
                if confirm == 'y':
                    side = 'BUY' if choice == '1' else 'SELL'
                    place_test_order(client, trading_utils, symbol, side, quantity, use_market_order=False)
                else:
                    print("已取消下单")
                    
            except ValueError as e:
                print(f"输入错误: {str(e)}")
            except Exception as e:
                print(f"操作失败: {str(e)}")
                
        elif choice == '3':
            try:
                symbol = select_trading_pair(trading_utils)
                if not symbol:
                    continue
                    
                leverage = input("请输入杠杆倍数 (1-125): ").strip()
                leverage = int(leverage)
                if 1 <= leverage <= 125:
                    result = client.change_leverage(symbol, leverage)
                    print(f"杠杆修改成功: {result['leverage']}x")
                else:
                    print("杠杆倍数必须在1-125之间")
            except ValueError:
                print("杠杆倍数格式不正确")
                
        elif choice == '4':
            trading_utils.display_account_info(is_testnet=True)
            
        elif choice == '5':
            quick_test_trade(client, trading_utils)
            
        elif choice == '6':
            print("退出测试程序")
            break
            
        else:
            print("无效的选择，请重试")

def run_testnet(api_key, api_secret):
    """运行测试网程序"""
    try:
        client = BinanceClient(api_key, api_secret, testnet=True)
        trading_utils = TradingUtils(client)
        trading_utils.display_account_info(is_testnet=True)
        interactive_test_trade(client, trading_utils)
    except Exception as e:
        print(f"程序运行错误: {str(e)}")
        sys.exit(1) 
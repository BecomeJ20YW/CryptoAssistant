import sys
import argparse
import questionary
from config import load_api_config
from src.mainnet_trade import run_mainnet
from src.testnet_trade import run_testnet

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='币安合约账户监控工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行测试网环境
  python main.py test
  
  # 运行主网环境
  python main.py main
  
  # 直接开始测试交易（测试网）
  python main.py trade
  
  # 只查看账户状态（主网）
  python main.py status
  
  # 修改杠杆倍数（测试网）
  python main.py leverage BTCUSDT 20
  
  # 启动交互式菜单
  python main.py
"""
    )
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # test 命令 - 运行测试网
    subparsers.add_parser('test', help='运行测试网环境')
    
    # main 命令 - 运行主网
    subparsers.add_parser('main', help='运行主网环境')
    
    # trade 命令 - 直接进入测试交易模式
    subparsers.add_parser('trade', help='直接进入测试交易模式（测试网）')
    
    # status 命令 - 查看账户状态
    status_parser = subparsers.add_parser('status', help='查看账户状态')
    status_parser.add_argument('--env', choices=['main', 'test'], 
                             default='main', help='选择环境 (main 或 test)')
    
    # leverage 命令 - 修改杠杆倍数
    leverage_parser = subparsers.add_parser('leverage', help='修改杠杆倍数')
    leverage_parser.add_argument('symbol', help='交易对，例如 BTCUSDT')
    leverage_parser.add_argument('leverage', type=int, help='杠杆倍数 (1-125)')
    leverage_parser.add_argument('--env', choices=['main', 'test'], 
                               default='test', help='选择环境 (main 或 test)')
    
    return parser

def handle_leverage_command(args, api_key, api_secret):
    """处理修改杠杆的命令"""
    from src.client.binance_client import BinanceClient
    
    try:
        client = BinanceClient(api_key, api_secret, testnet=(args.env == 'test'))
        result = client.change_leverage(args.symbol.upper(), args.leverage)
        print(f"\n杠杆修改成功: {result['leverage']}x")
    except Exception as e:
        print(f"修改杠杆失败: {str(e)}")
        sys.exit(1)

def interactive_menu():
    """交互式菜单"""
    while True:
        # 主菜单选项
        action = questionary.select(
            "请选择操作:",
            choices=[
                questionary.Choice("1. 运行测试网环境", "test"),
                questionary.Choice("2. 运行主网环境", "main"),
                questionary.Choice("3. 查看账户状态", "status"),
                questionary.Choice("4. 修改杠杆倍数", "leverage"),
                questionary.Choice("5. 退出程序", "exit"),
                questionary.Choice("6. 显示帮助信息", "help")
            ]
        ).ask()
        
        if action == "exit":
            print("退出程序")
            sys.exit(0)
        elif action == "help":
            create_parser().print_help()
            input("\n按回车键继续...")
            continue
            
        try:
            # 根据命令选择环境
            api_env = {
                'test': 'testnet',
                'main': 'mainnet'
            }.get(action)
            
            # 对于需要选择环境的操作
            if action in ["status", "leverage"]:
                env_choice = questionary.select(
                    "请选择环境:",
                    choices=[
                        questionary.Choice("主网环境", "main"),
                        questionary.Choice("测试网环境", "test")
                    ]
                ).ask()
                api_env = 'mainnet' if env_choice == 'main' else 'testnet'
            
            # 处理特殊命令
            if action == "leverage":
                symbol = questionary.text("请输入交易对 (例如 BTCUSDT):").ask()
                leverage = questionary.text("请输入杠杆倍数 (1-125):").ask()
                
                try:
                    leverage = int(leverage)
                    if not (1 <= leverage <= 125):
                        print("杠杆倍数必须在1-125之间")
                        continue
                        
                    args = type('Args', (), {
                        'command': 'leverage',
                        'symbol': symbol,
                        'leverage': leverage,
                        'env': env_choice
                    })()
                    
                    api_key, api_secret, _ = load_api_config(api_env)
                    handle_leverage_command(args, api_key, api_secret)
                    
                except ValueError:
                    print("杠杆倍数必须是整数")
                    continue
                    
            else:
                # 处理其他命令
                api_key, api_secret, is_testnet = load_api_config(api_env)
                
                if action == "test" or (action == "status" and env_choice == "test"):
                    run_testnet(api_key, api_secret)
                elif action == "main" or (action == "status" and env_choice == "main"):
                    run_mainnet(api_key, api_secret)
                        
        except Exception as e:
            print(f"错误: {str(e)}")
                
        # 操作完成后暂停
        input("\n按回车键继续...")

def main():
    """主程序入口"""
    # 设置标准输出编码
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            # Python 3.7及以下版本
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    
    # 创建命令行解析器
    parser = create_parser()
    args = parser.parse_args()
    
    # 如果没有提供命令，启动交互式菜单
    if not args.command:
        try:
            interactive_menu()
            return
        except KeyboardInterrupt:
            print("\n程序已退出")
            sys.exit(0)
    
    try:
        # 根据命令选择环境
        env = {
            'test': 'testnet',
            'main': 'mainnet',
            'trade': 'testnet',
            'status': 'mainnet' if args.env == 'main' else 'testnet',
            'leverage': 'mainnet' if args.env == 'main' else 'testnet'
        }[args.command]
        
        # 加载API配置
        api_key, api_secret = load_api_config(env)
        
        # 处理不同的命令
        if args.command == 'leverage':
            handle_leverage_command(args, api_key, api_secret)
        elif args.command in ['test', 'trade']:
            run_testnet(api_key, api_secret)
        elif args.command == 'status':
            if args.env == 'main':
                run_mainnet(api_key, api_secret)
            else:
                run_testnet(api_key, api_secret)
        else:  # main
            run_mainnet(api_key, api_secret)
            
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
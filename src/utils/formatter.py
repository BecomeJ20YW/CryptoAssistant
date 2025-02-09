def format_number(number, decimals=2):
    """
    格式化数字，添加千位分隔符
    :param number: 要格式化的数字
    :param decimals: 小数位数
    :return: 格式化后的字符串
    """
    try:
        return f"{float(number):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(number)

def format_position_info(position, mark_price):
    """
    格式化持仓信息
    :param position: 持仓信息字典
    :param mark_price: 标记价格
    :return: 格式化后的持仓信息列表
    """
    position_amt = float(position['positionAmt'])
    entry_price = float(position['entryPrice'])
    unrealized_profit = float(position['unrealizedProfit'])
    leverage = float(position['leverage'])
    
    # 计算收益率
    if position_amt != 0:
        roi = (unrealized_profit / (abs(position_amt) * entry_price / leverage)) * 100
    else:
        roi = 0
    
    return [
        position['symbol'],
        "多" if position_amt > 0 else "空",
        format_number(abs(position_amt), 4),
        format_number(entry_price, 4),
        format_number(mark_price, 4),
        f"{leverage}x",
        format_number(unrealized_profit),
        f"{format_number(roi)}%"
    ] 
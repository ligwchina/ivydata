"""
股票和基金代码转换工具
功能：将纯数字代码转换为带交易所后缀的格式
作者：元宝
日期：2026年3月22日
"""

def convert_code(code):
    """
    将股票/基金代码转换为带后缀的格式
    
    参数:
        code: 字符串或整数类型的代码，如"600519"、"159995"
    
    返回:
        字符串: 带后缀的代码，如"600519.SH"、"159995.SZ"
    
    异常:
        ValueError: 当输入格式不正确时抛出
    """
    # 转换为字符串并处理可能的空格
    code_str = str(code).strip()
    
    # 如果已经包含后缀，直接返回
    if '.' in code_str:
        return code_str
    
    # 检查是否为纯数字
    if not code_str.isdigit():
        raise ValueError(f"代码 '{code_str}' 必须为纯数字")
    
    # 获取代码长度和前几位数字
    code_len = len(code_str)
    
    # 对于6位代码，判断是股票还是基金
    if code_len == 6:
        # 提取前2位或前3位用于判断
        prefix2 = code_str[:2]
        prefix3 = code_str[:3]
        
        # 1. 先判断是否为基金
        if prefix2 in ["15", "16", "18"]:  # 深交所基金
            return f"{code_str}.SZ"
        elif prefix2 in ["50", "51", "52", "53", "55", "56", "58"]:  # 上交所基金(包含新ETF)
            return f"{code_str}.SH"
        elif prefix2 in ["11", "12", "13"]:  # 沪市债券/可转债
            return f"{code_str}.SH"
        elif prefix2 in ["10", "11"]:  # 深市债券/可转债
            return f"{code_str}.SZ"
        
        # 2. 判断是否为股票
        first_char = code_str[0]
        
        if first_char in "6":  # 上交所股票
            return f"{code_str}.SH"
        elif first_char in "03":  # 深交所股票(主板、创业板)
            return f"{code_str}.SZ"
        elif first_char in "48":  # 北交所股票
            return f"{code_str}.BJ"
        elif first_char in "9":  # 沪市B股
            return f"{code_str}.SH"
        elif first_char in "2":  # 深市B股
            return f"{code_str}.SZ"
        else:
            # 未知类型，返回原代码
            return code_str
    
    # 对于非6位代码的处理
    elif code_len == 4:
        # 4位代码可能是可转债等
        return f"{code_str}.SH"  # 默认为上交所
    else:
        # 其他长度，无法确定，返回原代码
        return code_str


def convert_batch(code_list):
    """
    批量转换代码列表
    
    参数:
        code_list: 字符串/整数列表，如["600519", 159995, "000001"]
    
    返回:
        列表: 带后缀的代码列表
    
    异常:
        无，单个错误会被捕获并返回原值
    """
    result = []
    for code in code_list:
        try:
            converted = convert_code(code)
            result.append(converted)
        except Exception as e:
            # 如果转换失败，保留原值
            result.append(str(code))
    return result


def get_exchange(code):
    """
    获取代码对应的交易所标识
    
    参数:
        code: 字符串或整数类型的代码
    
    返回:
        字符串: 交易所标识，如"SH"、"SZ"、"BJ"、"OF"(场外基金)或"未知"
    """
    try:
        converted = convert_code(str(code))
        if '.' in converted:
            return converted.split('.')[-1]
        else:
            return "未知"
    except:
        return "未知"


def is_a_stock(code):
    """
    判断是否为A股股票代码
    
    参数:
        code: 字符串或整数类型的代码
    
    返回:
        bool: 是否为A股股票
    """
    code_str = str(code)
    if len(code_str) == 6 and code_str.isdigit():
        first_char = code_str[0]
        return first_char in "603"  # 6或0或3开头
    return False


def is_fund(code):
    """
    判断是否为基金代码
    
    参数:
        code: 字符串或整数类型的代码
    
    返回:
        bool: 是否为基金
    """
    code_str = str(code)
    if len(code_str) == 6 and code_str.isdigit():
        prefix2 = code_str[:2]
        return prefix2 in ["15", "16", "18", "50", "51", "52", "53", "55", "56", "58"]
    return False


def remove_suffix(code):
    """
    移除代码的后缀
    
    参数:
        code: 字符串，可能带后缀的代码
    
    返回:
        字符串: 纯数字代码
    """
    if isinstance(code, str) and '.' in code:
        return code.split('.')[0]
    return str(code)


# 使用示例
if __name__ == "__main__":
    # 测试示例
    test_cases = [
        "600519",  # 股票-上交所
        688981,    # 股票-科创板
        "000001",  # 股票-深交所
        "300313",  # 股票-创业板
        "830799",  # 股票-北交所
        "159995",  # 基金-深交所ETF
        "161725",  # 基金-深交所LOF
        "510300",  # 基金-上交所ETF
        "000300",  # 指数
        "110022",  # 可转债
    ]
    
    print("代码转换测试:")
    print("-" * 40)
    
    for test in test_cases:
        try:
            converted = convert_code(test)
            exchange = get_exchange(test)
            print(f"{test:>10} -> {converted:<15} 交易所: {exchange}")
        except Exception as e:
            print(f"{test:>10} -> 转换失败: {e}")
    
    print("\n批量转换测试:")
    print("-" * 40)
    
    batch_result = convert_batch(["600519", "000001", "159995", "abc"])
    for original, converted in zip(["600519", "000001", "159995", "abc"], batch_result):
        print(f"{original} -> {converted}")
    
    print("\n工具函数测试:")
    print("-" * 40)
    print(f"600519 是A股股票: {is_a_stock('600519')}")
    print(f"159995 是基金: {is_fund('159995')}")
    print(f"600519.SH 移除后缀: {remove_suffix('600519.SH')}")
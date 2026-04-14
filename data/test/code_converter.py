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
    code_str = str(code).strip()

    if '.' in code_str:
        return code_str

    if not code_str.isdigit():
        raise ValueError(f"代码 '{code_str}' 必须为纯数字")

    code_len = len(code_str)

    if code_len == 6:
        prefix2 = code_str[:2]
        prefix3 = code_str[:3]

        if prefix2 in ["15", "16", "18"]:
            return f"{code_str}.SZ"
        elif prefix2 in ["50", "51", "52", "53", "55", "56", "58"]:
            return f"{code_str}.SH"
        elif prefix2 in ["11", "12", "13"]:
            return f"{code_str}.SH"
        elif prefix2 in ["10", "11"]:
            return f"{code_str}.SZ"

        first_char = code_str[0]

        if first_char in "6":
            return f"{code_str}.SH"
        elif first_char in "03":
            return f"{code_str}.SZ"
        elif first_char in "48":
            return f"{code_str}.BJ"
        elif first_char in "4":
            return f"{code_str}.BJ"
        elif first_char in "8":
            return f"{code_str}.BJ"
        elif first_char in "9":
            return f"{code_str}.BJ"
        elif first_char in "2":
            return f"{code_str}.SZ"
        else:
            return code_str

    elif code_len == 4:
        return f"{code_str}.SH"
    else:
        return code_str


def convert_batch(code_list):
    """
    批量转换代码列表
    """
    result = []
    for code in code_list:
        try:
            converted = convert_code(code)
            result.append(converted)
        except Exception as e:
            result.append(str(code))
    return result


def get_exchange(code):
    """
    获取代码对应的交易所标识
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
    """
    code_str = str(code)
    if len(code_str) == 6 and code_str.isdigit():
        first_char = code_str[0]
        return first_char in "603"
    return False


def is_fund(code):
    """
    判断是否为基金代码
    """
    code_str = str(code)
    if len(code_str) == 6 and code_str.isdigit():
        prefix2 = code_str[:2]
        return prefix2 in ["15", "16", "18", "50", "51", "52", "53", "55", "56", "58"]
    return False


def remove_suffix(code):
    """
    移除代码的后缀
    """
    if isinstance(code, str) and '.' in code:
        return code.split('.')[0]
    return str(code)

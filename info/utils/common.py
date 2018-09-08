# 公用的工具类
def index_class(index):
    """自定义过滤器"""
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    return ""

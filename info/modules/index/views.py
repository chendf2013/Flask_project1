#
from flask import Blueprint, render_template, current_app, session, request
from flask.json import jsonify

from info import redis_store, constants

# 创建蓝图像
from info.models import User, News, Category
from info.utils.response_code import RET

index_blu = Blueprint("index", __name__)


@index_blu.route("/news_list")
def news_list():
    """处理请求新闻"""
    # 分析：get请求，有参数（cid,page,per_page）
    # 1、获取参数
    cid = request.args.get("cid", "1")
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page","10")

    # 2、校验参数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as ret:
        current_app.error.logger(ret)
        return jsonify(errno=RET.DATAERR, errmsg="参数错误")

    # 3、 按新闻分类查询数据
    filters = []
    news = None
    if cid != 1:
        filters.append(News.category_id == cid)
    try:
        news = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as ret:
        current_app.error.logger(ret)
        return jsonify(errno=RET.DATAERR,errmsg="数据查询错误")

    # 4、 取得当前页得数据
    news_list2 = news.items
    current_page = news.page
    total_page = news.pages

    # 5、将模型对象列表转化为字典
    news_list_dict = list()
    for new in news_list2:
        news_list_dict.append(new.to_basic_dict())
    data = {
        "news_list_dict": news_list_dict,
        "current_page": current_page,
        "total_page": total_page
    }
    # 6、返回数据
    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@index_blu.route("/")
def index():
    # 查询登陆状态
    user = None
    user_dict = None
    user_id = session.get("user_id", None)
    if user_id:
        try:
            user = User.query.filter(User.id == user_id).first()
        except Exception as ret:
            current_app.logger.error(ret)
        if user:
            user_dict = user.to_dict()
        else:
            user_dict = None


    # 查询新闻列表
    # 1、查询新闻内容
    news_list = list()
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS).all()
    except Exception as ret:
        current_app.error.logger(ret)
    # 2、 加载至列表中
    news_list_all = list()
    # 3、将对象的字典添加到字典列表中
    for news in news_list:
        news_list_all.append(news.to_basic_dict())

    # 查询新闻分类
    categories = list()
    try:
        categories = Category.query.all()
    except Exception as ret:
        current_app.error.logger(ret)
    category_list = list()
    for category in categories:
        category_list.append(category.to_dict())
    data = {
        "user_id": user_dict,
        "news_list_all": news_list_all,
        "category_list": category_list
    }
    return render_template("news/index.html", data=data)


@index_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")


# @index_blu.route("/favicon.ico")
# def favicon():
#     return render_template("static/news/favicon.ico")
#
from flask import Blueprint, render_template, current_app, session
from flask.json import jsonify

from info import redis_store, constants

# 创建蓝图像
from info.models import User, News
from info.utils.response_code import RET

index_blu = Blueprint("index", __name__)


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

    return render_template("news/index.html", data={"user_id": user_dict,"news_list_all": news_list_all})


@index_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")


# @index_blu.route("/favicon.ico")
# def favicon():
#     return render_template("static/news/favicon.ico")
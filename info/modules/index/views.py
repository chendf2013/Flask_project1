#
from flask import Blueprint, render_template, current_app, session
from flask.json import jsonify

from info import redis_store


# 创建蓝图像
from info.models import User

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
    return render_template("news/index.html", data={"user_id": user_dict})


@index_blu.route("/favicon.ico")
def favicon():
    return current_app.send_static_file("news/favicon.ico")


# @index_blu.route("/favicon.ico")
# def favicon():
#     return render_template("static/news/favicon.ico")
#
from flask import Blueprint
from info import redis_store


# 创建蓝图像
index_blu = Blueprint("index", __name__)


@index_blu.route("/")
def index():
    redis_store.set("name", "chendf")
    return "5555"

import os

from flask import Flask,session
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
# 指定session的保存位置
from flask_session import Session
import base64


class Config(object):
    """配置信息"""
    DEBUG = True

    # 数据库的配置
    # 配置数据库连接地址
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:mysql@127.0.0.1:3306/git"
    # 是否追踪数据库的修改
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis 的配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # session保存配置
    SESSION_TYPE = "redis"
    # 开启session签名
    SESSION_USE_SIGNER = True
    # 设置需要过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2
    # 指定 session 保存的redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 指定secrect_key
    SECRET_KEY = base64.b64encode(os.urandom(48))


app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
# SQLAchemy 是关系型数据库框架,需要导入flask-mysql和 flask-sqlalchemy
db = SQLAlchemy(app)

# 初始化 redis 对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# 开启当前项目csrf保护
CSRFProtect(app)

# 设置seddion指定保存位置
Session(app)


@app.route("/")
def index():
    session["name"] = "chendf"
    return "index"


if __name__ == "__main__":
    app.run()
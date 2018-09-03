from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis


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


app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
# SQLAchemy 是关系型数据库框架,需要导入flask-mysql和 flask-sqlalchemy
db = SQLAlchemy(app)

# 初始化 redis 对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# 开启当前项目csrf保护
CSRFProtect(app)


@app.route("/")
def index():
    return "index"


if __name__ == "__main__":
    app.run()
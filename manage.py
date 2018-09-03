from flask_script import Manager
from flask import Flask, session
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_session import Session
from config import Config


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
manager = Manager(app)


@app.route("/")
def index():
    session["name"] = "chendf"
    return "5555"


if __name__ == "__main__":
    manager.run()
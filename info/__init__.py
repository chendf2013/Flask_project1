import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_session import Session
from config import config


# 初始化数据库
# SQLAchemy 是关系型数据库框架,需要导入flask-mysql和 flask-sqlalchemy

db = SQLAlchemy()
redis_store = None  # type: StrictRedis
# redis_store: StrictRedis = None


def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].DEBUG)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    # 在 当前文件路径下创建文件logs
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    setup_log(config_name)
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 可以先创建数据库 然后调用init_app方法绑定app
    db.init_app(app)

    # 初始化 redis 对象
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT, decode_responses=True)

    # 开启当前项目csrf保护
    # CSRFProtect(app)

    # 设置seddion指定保存位置
    Session(app)

    # 注册蓝图
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    return app
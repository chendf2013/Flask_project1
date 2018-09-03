import base64
import os
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


class DevelopmentConfig(Config):
    """开发环境下的配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境下的配置"""
    DEBUG = False


class TestingConfig(Config):
    """单元测试环境下的配置"""
    DEBUG = True
    TESTING = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
        }
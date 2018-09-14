import logging
import pymysql

from flask_script import Manager
from flask import session
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models

# 类似于工厂方法
from info.models import User

app = create_app('development')
manager = Manager(app)
# 将app与db关联
Migrate(app, db)
# 将迁移命令添加到manager中
manager.add_command("db", MigrateCommand)


# 添加flask-script创建管理员用户扩展
# -n 是 -name的缩写
@manager.option( "-n","-name",dest="name")
@manager.option("-p","-password",dest="password")
def c_super(name,password):
    if not all([name,password]):
        print("请按照如下格式输入：python manager.py name password")
        return

    print("进入函数")

    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
        print("创建管理员%s成功" % user.nick_name)
    except Exception as ret:
        db.session.rollback()
        print(ret)
        print("创建管理员%s失败" % user.nick_name)


if __name__ == "__main__":
    # print(app.url_map)
    manager.run()
from flask import Blueprint, render_template, redirect, g, request, current_app, jsonify
# from qiniu.services import storage

from info import constants
from info.utils.common import user_login_data
from info.utils.response_code import RET

profile_blu = Blueprint("profile",__name__,url_prefix="/user")

@profile_blu.route('/collection')
@user_login_data
def user_collection():

    # 获取参数
    page = request.args.get("p", 1)

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 查询用户指定页数的收藏的新闻
    user = g.user

    news_list = []
    total_page = 1
    current_page = 1
    try:
        # 懒加载，是query对象，可以直接  .paginate
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        # 是一个对象列表
        news_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = []
    for news in news_list:
        # 需要转换为字典列表，因为不需要展示新闻内容，只需要返回基本的字典信息
        news_dict_li.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collections": news_dict_li
    }
    # print(news_dict_li)

    return render_template('news/user_collection.html', data=data)


@profile_blu.route('/pass_info', methods=["GET", "POST"])
@user_login_data
def pass_info():
    if request.method == "GET":
        return render_template('news/user_pass_info.html')

    # 1. 获取参数
    old_password = request.json.get("old_password")
    news_password = request.json.get("new_password")

    # 2. 校验参数
    if not all([old_password, news_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误a")

    # TODO 新旧密码是否一致判断

    # 3. 判断旧密码是否正确
    user = g.user
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="原密码错误")

    # 4. 设置新密码
    user.password = news_password

    return jsonify(errno=RET.OK, errmsg="保存成功")


@profile_blu.route('/pic_info', methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == "GET":
        return render_template('news/user_pic_info.html', data={"user": user.to_dict()})

    # 如果是POST表示修改头像
    # 1. 取到上传的图片
    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 2. 上传头像
    try:
        # print("上传图片")
        # 使用自已封装的storage方法去进行图片上传
        from info.utils.image_storage import storage
        key = storage(avatar)
    except Exception as e:
        print(e)
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传头像失败")

    # 3. 保存头像地址
    # 储存的是相对路径，方便后期修改
    user.avatar_url = key
    data = {"avatar_url": constants.QINIU_DOMIN_PREFIX +user.avatar_url}
    return jsonify(errno=RET.OK, errmsg="OK", data=data)



@profile_blu.route('/base_info', methods=["GET", "POST"])
@user_login_data
def base_info():
    """不同的请求方式做不同的事情"""
    # print("进入函数")
    # 不同的请求方式，做不同的事情
    if request.method == "GET":
        return render_template('news/user_base_info.html', data={"user": g.user.to_dict()})

    # 表单提交
    # 1. 取到传入的参数
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    # 2. 校验参数
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误a")
    if gender not in ("WOMAN", "MAN"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误b")

    # （数据库更新应改先查询，再保存）user已经使用g.user从数据库中查询出来的，并且不用cimmit,后端自动保存。
    user = g.user
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg="OK")



@profile_blu.route('/info')
@user_login_data
def user_info():
    # print("进入函数")
    user = g.user
    if not user:
        # 代表没有登录，重定向到首页
        return redirect("/")
    data = {"user_id": user.to_dict()}
    return render_template('news/user.html', data=data)

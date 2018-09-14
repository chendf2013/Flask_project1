from datetime import datetime

from flask import Blueprint, render_template, redirect, g, request, current_app, jsonify, abort
# from qiniu.services import storage

from info import constants, db
from info.models import News, Category, User
from info.utils.common import user_login_data
from info.utils.response_code import RET
from info.utils.image_storage import storage

profile_blu = Blueprint("profile",__name__,url_prefix="/user")


@profile_blu.route('/other_news_list')
@user_login_data
def other_news_list():
    """获取新闻列表"""
    print("进入新闻列表显示界面")

    # 1. 取参数
    other_id = request.args.get("user_id")
    page = request.args.get("p", 1)

    # 2. 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not other:
        return jsonify(errno=RET.NODATA, errmsg="当前用户不存在")

    try:
        paginate = other.news_list.paginate(page, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    news_dict_li = []
    for news_item in news_li:
        news_dict_li.append(news_item.to_basic_dict())

    data = {
        "news_list": news_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)


@profile_blu.route('/other_info')
@user_login_data
def other_info():
    """其他用户页面展示"""
    user = g.user
    other_id = request.args.get("user_id")
    if not other_id:
        abort(404)
    other = None
    try:
        other = User.query.get(other_id )
    except Exception as ret:
        current_app.logger.error(ret)

    # 判断当前的用户是否关注新闻作者
    is_followed = False
    # if 当前新闻有作者，并且 当前登录用户已关注过这个用户
    if other and user:
        # if user 是否关注过 news.user
        if other in user.followed:
            is_followed = True



    data = {
        "other_info":other.to_dict()if other else None,
        "user": g.user.to_dict() if g.user else None,
        "is_followed":is_followed
    }

    return render_template("./news/other.html",data=data)


@profile_blu.route('/my_followed')
@user_login_data
def my_followed():
    """我的关注"""
    user = g.user

    # 获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 获取当前页数据
        follows = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    user_dict_li = []

    for follow_user in follows:
        user_dict_li.append(follow_user.to_dict())

    data = {
        "users": user_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return render_template("./news/user_follow.html",data=data)


@profile_blu.route('/news_list')
@user_login_data
def news_lists():

    page = request.args.get("p")
    if not page:
        page = 1
    user = g.user
    # TODO 为什么要这么获取？？
    news = News.query.filter(News.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
    news_list = news.items
    current_page = news.page
    total_page = news.pages

    news_list_dict = []
    for news in news_list:
        news_list_dict .append(news.to_review_dict())


    data = {
        "news_list":news_list_dict,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("news/user_news_list.html",data=data)



@profile_blu.route('/news_release', methods=["GET", "POST"])
@user_login_data
def news_release():
    """新闻发布"""
# 双请求，get请求获取html,post请求为表单提交
# 获取参数
# 创建新闻模型
# 数据库保存
# 模板返回
    # get请求获取html
    if request.method == "GET":

        category_list = []
        categories = None
        try:
            categories = Category.query.all()
        except Exception as ret:
            current_app.logger.error(ret)
        # print(categories)

        for category in categories:
            category_list.append(category.to_dict())
        # 移除最新分类
        category_list.pop(0)
        data = {
            "categories":category_list
        }
        return render_template('news/user_news_release.html', data=data)

        # return render_template("news/user_news_release.html", data=data)

    # post请求提交数据
    # user = g.user

    # 获取参数
    # form 表单提交 要求html 中的input标签 和 select标签必须有name属性
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    # 摘要
    digest = request.form.get("digest")
    # 图片内容必须是byte类型，因此获取到后必须read()
    index_image = request.files.get("index_image").read()
    print(type(index_image))
    content = request.form.get("content")
    # 校验参数
    if not all([title,category_id,digest,index_image,content]):
        return jsonify(errno=RET.DATAERR, errmsg="提交参数不全")
    try:
        category_id = int(category_id)
    except Exception as ret:
        return jsonify(errno = RET.DATAERR,errmsg="新闻分类参数错误")
    # 数据保存

    # 上传图片信息
    try:
        key = storage(index_image)
        key = constants.QINIU_DOMIN_PREFIX+key
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传头像失败")
    # 初始化数据模型
    news= News()
    news.create_time = datetime.now()
    news.category_id = category_id
    news.title = title
    news.digest =digest
    news.index_image_url = key
    news.content = content
    news.user_id = g.user.id
    # 必须写上新闻来源
    news.source = "个人发布"
    # 审核状态
    # 首页中添加新闻审核状态的查询条件
    news.status = 1
    print(news)

    # 上传数据
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as ret:
        current_app.logger.error(ret)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR,errmsg="数据保存至数据库失败")

    return jsonify(errno=RET.OK,errmsg="新闻提交成功，等待审核")


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

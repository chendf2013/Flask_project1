# import datetime
# from datetime import time
# import datetime
import time
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, g, current_app

from info import constants, db
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET

admin_blu = Blueprint("admin",__name__,url_prefix="/admin")


@admin_blu.route('/news_type',methods = ["get","post"])
def news_type():
    if request.method == "GET":

        # categories = Category.query.all()
        categories = Category.query.all()

        category_list = []

        for category in categories:
            category_list.append(category.to_dict())

        data = {
                "categories":category_list
                }
        return render_template("./admin/news_type.html",data=data)
    name = request.json.get("name")
    id = request.json.get("id",None)
    # 只有一个参数就是增加分类
    if id:
        category = Category.query.get(id)
        category.name = name
    # 有两个参数就是修改分类
    else:
        category = Category()
        category.name = name
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as ret:
            current_app.error.logger(ret)
            print(ret)
    return jsonify(errno=RET.OK,errmsg = "OK")


@admin_blu.route('/version_audit_detail',methods=["get","post"])
def version_audit_detail():
    """版式编辑"""
    if request.method=="GET":
        # 获取参数
        news_id = request.args.get("news_id")
        # 获取新闻信息
        news = News.query.get(news_id)
        # 获取分类信息
        categories = Category.query.all()
        # 将query对象转化为字典模型
        category_list = []
        for category in categories:
            # 如果是当前新闻的分类，就添加判断是否为当前新闻分类标志的键值对
            if news.category_id == category.id:
                # category_dict = category.to_dict
                category_dict = category.to_dict()
                category_dict["is_selected"]=True
            else:
                category_dict = category.to_dict()

            category_list.append(category_dict)

            # 移除最新分类
            # category_list.pop(0)
        category_list.pop(0)
            # category_list.remove(0)

        # 将数据组装成字典传递
        data = {
            "news":news.to_dict(),
            "categories":category_list
        }
        # print(data["news"][0].get("title"))
        # print(data["news"])
        return render_template("./admin/news_edit_detail.html",data = data)

    # print("进入版式编辑")

    # 修改内容提交
    # 取到Post进来的数据
    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")

    # 查询新闻信息
    news = News.query.get(news_id)

    # 将图片上传至七牛云
    if index_image:
        try:
            # print("上传图片")
            # 使用自已封装的storage方法去进行图片上传
            from info.utils.image_storage import storage
            key = storage(index_image)
        except Exception as e:
            print(e)
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传头像失败")

        # 保存头像地址
        news.index_image_url = constants.QINIU_DOMIN_PREFIX+key

    # 更新新闻信息
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id
    print("进入版式编辑2")


    # 返回保存信息
    return jsonify(errno=RET.OK,errmsg = "OK")


@admin_blu.route('/version_audit')
def version_audit():
    """版式编辑页面展示"""

# 获取参数
    page = request.args.get("p",1)
    page = int(page)
# 查询也是get请求，需要有关键字
    keywords = request.args.get("keywords",None)
    # print(keywords)
# 查询条件
    filters = [News.status==0]
    if keywords:
        filters.append(News.title.contains(keywords))
# 执行查询
    paginate = News.query.filter(*filters) \
        .order_by(News.create_time.desc()) \
        .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

    current_page = paginate.page
    total_page = paginate.pages
    news = paginate.items
# 将新闻模板转换问字典模型
    news_list = []
    for new in news:
        news_list.append(new.to_basic_dict())
# 组装成字典数据
    data = {
        "news_list":news_list,
        "current_page":current_page,
        "total_page":total_page
    }
# 将数据渲染进模板
    return render_template("./admin/news_edit.html",data=data)


@admin_blu.route('/news_audit',methods=["post"])
def news_audit():
    """新闻审核"""

    # 获取参数
    # form表单获取内容
    # action = request.form.get("action")

    action = request.json.get("action")
    news_id = request.json.get("news_id")
    reason = request.json.get("reason")

    # 校验参数
    # print("进入审核函数了哈")
    # 查询新闻
    news = News.query.get(news_id)

    # 新闻年数据操作
    if action == "reject":
        news.reason = reason
        news.status = -1
    else:
        news.status = 0
    # 保存数据
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")
    # print("审核成功")

    return jsonify(errno=RET.OK, errmsg="OK")



@admin_blu.route('/news_review_edit/<int:news_id>')
# def news_review_edit():
def news_review_edit(news_id):
    """新闻审核按钮点击"""
    if request.method == "GET":
        # print("进入审核函数")
        # 获取参数
        # news_id = request.args.get("news_id")
        # 获取新闻内容
        # news = News.query.get(News.id == news_id)
        news = News.query.get(news_id)
        data = {
            "news":news.to_dict()
        }
        # 返回数据
        # print(data)
        return render_template("./admin/news_review_detail.html",data=data)



@admin_blu.route('/news_review_detail/<int:news_id>')
def news_review_detail(news_id):
    # keywords = request.args.get("keywords",None)
    # 通过id查询新闻
    news = None

    # if not keywords:
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    # else:
        # try:
        #     news = News.query.get(news_id)
        # except Exception as e:
        #     current_app.logger.error(e)

    if not news:
        return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

    # 返回数据
    data = {"news": news.to_dict()}
    # print("打印的字典是》》》》》》》")
    # print(data["news"]["id"])
    return render_template('admin/news_review_detail.html', data=data)


@admin_blu.route('/news_review')
def news_review():
    """新闻审核"""
    # print("进入新闻审核")
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    filters = [News.status != 0]
    # 如果关键字存在，那么就添加关键字搜索
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_review_dict())

    context = {"total_page": total_page, "current_page": current_page, "news_list": news_dict_list}

    return render_template('admin/news_review.html', data=context)


@admin_blu.route('/user_list')
def user_list():
    # print("进入user_list函数")
    # 获取当前页
    page = request.args.get("p",1)
    page=int(page)

    # 查询新闻
    # paginates = User.query.filter(User.is_admin==False).order_by(User.create_time.desc()).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
    paginates = User.query.filter(User.is_admin == False).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)

    # 形成数据
    users = paginates.items
    total_page = paginates.pages
    current_page = paginates.page


    # 将模型转换成字典
    user_list = []
    for user in users:
        user_list.append(user.to_admin_dict())

    data = {
        "total_page":total_page,
        "current_page":current_page,
        "users":user_list
    }
    # print(data["users"])
    return render_template("admin/user_list.html",data = data)


@admin_blu.route("/user_count")
def user_count():
    # 总人数
    total_count = User.query.filter(User.is_admin==False).count()

    # 查询月新增数
    mon_count = 0
    try:
        now = time.localtime()
        mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)
        mon_begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询日新增
    day_count = 0
    try:
        day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 查询图表信息
    # 获取到当天00:00:00时间

    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    # 定义空数组，保存数据
    active_date = []
    active_count = []

    # 依次添加数据，再反转
    for i in range(0, 31):
        begin_date = now_date - timedelta(days=i)
        end_date = now_date - timedelta(days=(i - 1))
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        count = 0
        try:
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        active_count.append(count)

    active_date.reverse()
    active_count.reverse()


    data = {
        "total_count":total_count,
        "mon_count":mon_count,
        "day_count":day_count,
        "active_date":active_date,
        "active_count":active_count
    }

    return render_template("admin/user_count.html",data = data)


@admin_blu.route("/logout")
@user_login_data
def logout():
    user = g.user
    # session.pop("")
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)
    session.pop('mobile', None)

    # print("退出成功")

    return redirect(url_for("index.index"))


@admin_blu.route("/index")
@user_login_data
def index():
    """渲染整体的页面"""
    # 查询登陆用户
    user = g.user
    if user:
        # 能取到就是已经登陆过
        data = {
            "user":user.to_dict()
        }

        return render_template("admin/index.html",data=data)
    else:
        # 直接路径访问，并且没有登陆过
        return redirect(url_for("admin.login"))




@admin_blu.route("/login",methods=["get","post"])
def login():
    """登陆页访问"""
    # if request.method == "GET":
    #     return render_template("admin/index.html")
    # if request.method == "GET":
    #     # 判断当前是否有登录，如果有登录直接重定向到管理员后台主页
    #     user_id = session.get("user_id", None)
    #     is_admin = session.get("is_admin", False)
    #     if user_id and is_admin:
    #         return redirect(url_for('admin.index'))
    if request.method == "GET":
    # 如果直接输入网址登陆，那么就先判断是否是管理员并且已经登陆过（get）
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)
        if user_id and is_admin:
            return redirect(url_for('admin.index'))

        return render_template('admin/login.html')
    # 如果是从登陆页面登陆(post)
    # 获取参数
    user_name = request.form.get("username")
    password = request.form.get("password")

    # 校验参数（只要不对就重新登陆）
    if not all([user_name, password]):
        return render_template('admin/login.html', errmsg="参数错误")

    # 查询当前用户
    try:
        user = User.query.filter(User.mobile == user_name, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="用户信息查询失败")

    if not user:
        return render_template('admin/login.html', errmsg="未查询到用户信息")

    # 校验密码
    if not user.check_password(password):
        return render_template('admin/login.html', errmsg="用户名或者密码错误")




    # 保存登陆状态
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = True

    # 登陆成功跳转页面
    # 跳转页面是在admin蓝图下
    # print("验证通过")

    return redirect(url_for("admin.index"))





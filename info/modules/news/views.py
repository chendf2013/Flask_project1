from flask import Blueprint, render_template, session, current_app, g

from info.models import User
from info.utils.common import user_login_data

news_blu = Blueprint("news",__name__,url_prefix="/news")


from flask import abort, jsonify
from flask import current_app
from flask import g
from flask import request
from flask import session

from info import constants, db
from info.models import News, User, Comment, CommentLike
from flask import render_template

from info.utils.common import user_login_data
from info.utils.response_code import RET





@news_blu.route('/followed_user', methods=["POST"])
@user_login_data
def followed_user():
    """作者关注"""
    # 获取参数
    action = request.json.get("action")
    user_id = request.json.get("user_id")
    # 参数校验
    if not all([action,user_id]):
        return jsonify(errno=RET.DATAERR,errmsg="参数不足")

    if action not in ("follow","unfollow"):
        return jsonify(errno=RET.DATAERR,errmsg="参数错误")

    user=None
    try:
        user = g.user
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.SESSIONERR,errmsg="请登陆")


    try:
        user_author = User.query.get(user_id)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DATAERR, errmsg="数据库查询错误")

    if not user_author:
        return jsonify(errno=RET.DATAERR, errmsg="没有查询到当前作者")

    if action=="follow":
        # 当前登陆用户关注新闻作者请求
        # 将用户添加到用户新闻列表中即可
        if user not in user_author.followers:
            user_author.followers.append(user)
        else:
            return jsonify(errno=RET.DATAERR,errmsg="已关注作者，请勿重复关注")
    elif action == "unfollow":
        # 当前登陆用户取消关注新闻作者
        if user in user_author.followers:
            user_author.followers.remove(user)
        else:
            return jsonify(errno=RET.DATAERR,errmsg="没有关注作者")
    return jsonify(errno=RET.OK,errmsg="操作成功")


@news_blu.route('/comment_like', methods=["POST"])
@user_login_data
def comment_like():
    """ 评论与点赞"""
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 1. 取到请求参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    if action == "add":
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment.id).first()
        # 判断评论是否存在
        if not comment_like_model:
            # 点赞评论
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment.id
            db.session.add(comment_like_model)
            # 更新点赞次数
            comment.like_count += 1

    else:
        # 取消点赞评论
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                      CommentLike.comment_id == comment.id).first()
        # 判断评论是否存在
        if comment_like_model:
            db.session.delete(comment_like_model)
            # 更新点赞次数
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库操作失败")

    return jsonify(errno=RET.OK, errmsg="OK")


@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def comment_news():
    """评论新闻或者回复某条新闻下指定的评论"""

    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 1. 取到请求参数
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    # 2. 判断参数
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # 查询新闻，并判断新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 3. 初始化一个评论模型，并且赋值
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id

    # 添加到数据库
    # 为什么要自己去commit()?，因为在return的时候需要用到 comment 的 id，也就是必须手动提交后才会在数据库更新，然后返回时才能获取到
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())


@news_blu.route('/news_collect', methods=["POST"])
@user_login_data
def collect_news():
    """收藏新闻"""
    # 1. 接受参数
    # 2. 判断参数
    # 3. 查询新闻，并判断新闻是否存在
    # 4. 收藏逻辑实现


    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 1. 接受参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 2. 判断参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 查询新闻，并判断新闻是否存在(谨防postman请求)
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询错误")
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 4. 收藏以及取消收藏
    if action == "cancel_collect":
        # 取消收藏
        if news in user.collection_news:
            user.collection_news.remove(news)
    else:
        # 收藏
        if news not in user.collection_news:
            user.collection_news.append(news)

    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blu.route('/<int:news_id>')
@user_login_data # news_detail = user_login_data(news_detail)
def news_detail(news_id):
    """新闻详情"""

    # 用户登录信息
    user = g.user

    # 右侧的新闻排行
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    news_dict_li = []
    for news in news_list:
        news_dict_li.append(news.to_basic_dict())

    # 查询新闻详细数据(通过news_id查询)
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        # 报404错误，404错误统一显示页面后续再处理
        abort(404)
    # 更新新闻的点击次数
    news.clicks += 1

    # 是否是收藏　
    is_collected = False
    if user:
        # 判断用户是否收藏当前新闻，如果收藏：
        # collection_news是一个query对象 后面可以不用加all，因为sqlalchemy会在使用的时候去自动加载，形成列表
        if news in user.collection_news:
            is_collected = True

    # 去查询评论数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    # 查询当前用户在当前的新闻里面都点赞了哪些评论
    comment_like_ids = []
    # comment_likes = []
    if g.user:
        try:
            # 查询当前新闻的所有评论id
            comment_ids = [comment.id for comment in comments]
            # 当前的新闻评论中 & 被当前用户点赞的 对象列表
            comment_likes = CommentLike.query .filter(CommentLike.comment_id.in_(comment_ids), CommentLike.user_id == g.user.id).all()
            # 将上面生成的表中的id取出来
            comment_like_ids = [comment_lik.comment_id for comment_lik in comment_likes]
        except Exception as ret:
            current_app.logger.error(ret)

    comment_dict_li = []
    for comment in comments:
        comment_dict = comment.to_dict()
        # 在字典中添加代表点赞的标识符，先默认为没有
        comment_dict["is_like"] = False
        # 看看是否真的是点赞的评论
        if comment.id in comment_like_ids:
            comment_dict["is_like"] = True
        comment_dict_li.append(comment_dict)

    # 关注详情
    is_followed = False
    # 从当前的登陆用户中判断其关注是否有新闻作者

    if news.user and user:
        # if user 是否关注过 news.user
        # if news.user in user.followed:
        #     is_followed = True
        #
        if user in news.user.followers:
            is_followed = True


    data = {
        "user_id": user.to_dict() if user else None,
        "news_list_all": news_dict_li,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "comments": comment_dict_li,
        "is_followed":is_followed
    }

    return render_template("news/detail.html", data=data)

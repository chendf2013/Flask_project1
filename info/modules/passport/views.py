import random
import re
from datetime import datetime

from flask import Blueprint, current_app, request, abort, make_response, json, jsonify, session
from info import redis_store, constants, db

# 创建蓝图像
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.response_code import RET

passport_blu = Blueprint("get_image_code", __name__, url_prefix="/passport")


@passport_blu.route("/logout")
def logout():
    """注销账号"""
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)

    return jsonify(errno=RET.OK, errmsg="OK")


@passport_blu.route("/login", methods=["POST"])
def login():
    """登陆"""
    print("进入登陆函数")
    data = request.json
    mobile = data.get("mobile")
    password = data.get("password")
    if not all([mobile, password]):
        return jsonify(errno=RET.DATAERR, errrmsg="参数错误")
    if not re.match(r"1[35678][0-9]{9}", mobile):
        return jsonify(errno=RET.ROLEERR, errmsg="请输入正确的手机号码")
    # 2 、从数据库查询出指定用户
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.ROLEERR, errmsg="查找数据库过程崩了")
    if not user:
        current_app(errno=RET.ROLEERR, errmsg="没有查到用户")
    # 3、 校对登陆密码
    if not user.check_password(password):
        return jsonify(errno=RET.ROLEERR, errmsg="密码不正确")
    # 4、保存用户状态
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # 5、记录用户的最后登陆时间,同时进行了自动保存
    user.last_login = datetime.now()
     # 6、返回结果
    return jsonify(errno=RET.OK, errmsg="OK")


@passport_blu.route("/register", methods=["POST"])
def register():
    """注册功能实现"""
    # 1、获取数据（手机号，手机验证码，密码）
    data = request.json
    mobile = data.get("mobile")
    smscode = data.get("smscode")
    password = data.get("password")
    print(data, mobile, smscode, password)
    # 2、校验数据是否合乎规范
    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.DATAERR, errmsg="参数错误")
    if not re.match(r"1[35678][0-9]{9}", mobile):
        return jsonify(errno=RET.ROLEERR, errmsg="请输入正确的手机号码")
    # 3、手机验证码验证
    smscode_server = redis_store.get("sms_"+mobile)
    if not smscode_server:
        return jsonify(errno=RET.NODATA, errmsg="验证码超时")
    if smscode_server != smscode:
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")
    # 4、保存到用户信息mysql数据库中
    user =User()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = password
    user.last_login = datetime.now()

    # @property
    # def password(self):
    #     raise AttributeError("当前属性不允许读取")
    #
    # @password.setter
    # def password(self, value):
    #     # self.password_hash = 对value加密
    #     self.password_hash = generate_password_hash(value)
    #
    # def check_password(self, password):
    #     """校验密码"""
    #     return check_password_hash(self.password_hash, password)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as ret:
        db.session.rollback()
        current_app.logger.error(ret)
        return jsonify(errno=RET.DATAERR, errmsg="数据库保存用户注册信息错误")
    # 5、保存用户状态到redis的session中，供下次登陆验证使用
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # session["passsword"] = user.password

    # 6、返回注册结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@passport_blu.route("/sms_code", methods=["POST"])
def send_mobile_message():
    """校验图片验证码并发送手机验证码"""
    # return jsonify(error=RET.PARAMERR, errmg="参数有误")
    # 1、 获取参数（验证码图片内容，验证码编号，手机号）
    # 2、 图片验证码校验
    # 3、 将图片验证码信息从redis数据库中删除
    # 4、 向手机发送验证码
    # 5、 向客户端通知验证码发送状态

    # 当点击获取验证码后，不是form表单提交，而是ajax请求，并且发送的数据是json字符串。
    # data = request.json
    # 或者使用
    data = json.loads(request.data)

    image_code = data.get("image_code")
    mobile = data.get("mobile")
    image_code_id = data.get("image_code_id")

    # 数据判断是否为空(查看接口文档，需要返回什么类型数据以及类型参数)
    if not all([image_code, mobile, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmg="参数有误")
    # 手机号码验证
    if not re.match(r"1[35678]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmg="手机号码错误")

    # 图片验证码验证
    try:
        image_code_server = redis_store.get("ImageCodeId"+image_code_id)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DBERR, errmg="数据库查询错误")
    if not image_code_server:
        return jsonify(errno=RET.NODATA, errmg="图片验证码已过期")
    if image_code.upper() != image_code_server.upper():
        return jsonify(errno=RET.DATAERR, errmg="图片验证码已过期")

    # 生成手机验证码并保存到本地（以session的形式保存）
    sms_code = "%06d" % random.randint(0, 999999)
    current_app.logger.error("当前的验证码是%s" % sms_code)
    # 发送验证码
    # result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], "1")
    # # result = CCP().send_template_sms(mobile, [sms_code_str, constants.SMS_CODE_REDIS_EXPIRES / 5], "1")
    #
    # # 回送验证码发送状态
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR, errmg="发送短信失败")
    # # 保存短信验证码
    try:
        redis_store.set("sms_"+mobile, sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as ret:
        current_app.logger.error(ret)
        return jsonify(errno=RET.DATAERR, errmg="数据保存错误")
    return jsonify(errno=RET.OK, errmg="发送短信成功")


@passport_blu.route("/image_code")
def get_image_code():
    """图片验证码的生成、保存、发送"""
    # 取到参数
    # 1、args取url?后的参数
    image_code_id = request.args.get("imageCodeId", None)
    # 2、判断是否有值
    if not image_code_id:
        return abort(403)

    # 3、生成图片验证码
    from info.utils.captcha.captcha import captcha
    #
    name, text, image = captcha.generate_captcha()
    print("图片验证码是%s"% text)

    # 4、保存到redis
    try:
        redis_store.set("ImageCodeId"+image_code_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as ret:
        current_app.logger.error(ret)
        return abort(500)
    # 5、返回（设置返回类型,供浏览器识别）
    response = make_response(image)
    response.headers["Content-Type"] = "image/jpg"
    # 6、返回数据
    return image


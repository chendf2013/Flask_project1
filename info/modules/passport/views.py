#
from flask import Blueprint, render_template, current_app, request, abort, make_response
from info import redis_store, constants

# 创建蓝图像

passport_blu = Blueprint("get_image_code", __name__, url_prefix="/passport")


@passport_blu.route("")
def send_mobile_message():
    """校验图片验证码并发送手机验证码"""


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


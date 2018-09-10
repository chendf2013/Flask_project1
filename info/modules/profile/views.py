from flask import Blueprint, render_template

profile_blu = Blueprint("profile",__name__,url_prefix="/profile")


@profile_blu.route('/info')
def comment_like():
    data = {}
    return render_template("/news/user.html",data=data)
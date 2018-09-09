from flask import Blueprint, render_template

news_blue = Blueprint("news",__name__,url_prefix="/news")


@news_blue.route("/<int:news_id>")
def news(news_id):
    data = {
    }
    return render_template("/news/detail.html", data=data)
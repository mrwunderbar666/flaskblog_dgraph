from flask import Blueprint, render_template, request, abort
from flaskblog import dgraph

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts, total, pages = dgraph.list_posts(page=page, per_page=5)
    pages = range(1, pages+1)
    return render_template('home.html', posts=posts, pages=pages, current_page=page)


@main.route('/about')
def about():
    return render_template('home.html', title="About Page")


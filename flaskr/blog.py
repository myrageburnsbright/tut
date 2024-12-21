from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
import sys
import json
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        '''SELECT p.id, title, body, created, author_id, username
        FROM post p JOIN user u ON p.author_id = u.id
        ORDER BY created DESC
        LIMIT 2'''
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/getposts')
def getposts():

    page = request.args.get('page')

    pagesize = 2 # in index.html have hard coded value which should be equal
    db = get_db()
    offset = int(page) * pagesize

    posts = db.execute(
        '''SELECT p.id, title, body, created, author_id, username
        FROM post p JOIN user u ON p.author_id = u.id
        ORDER BY created DESC
        LIMIT {}
        OFFSET {}'''.format(pagesize, offset)
    ).fetchall()

    l = [] # dont know exactly how json works with sqlite rows
        
    for post in posts:
        l.append({'username' : post['username'], 
                  'title' : post['title'], 
                  'id' : post['id'], 
                  'body' : post['body'], 
                  'created' : str(post['created']), 
                  'author_id' : post['author_id'],
                  'by_author' : "true" if post['author_id'] == g.user['id']  else "false"
                  })
    
    return json.dumps(l)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

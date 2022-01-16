
from flask import Flask, render_template, request, session, flash, Markup
from flask.helpers import url_for
from werkzeug.utils import redirect
import mysql.connector
import bcrypt
import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'

def dbConnect():
    db = mysql.connector.connect(
    host = 'localhost',
    user = 'name',
    passwd = 'password_goes_here',
    database = 'database_name'
    )
    return db

# tuple with query and sql parameters
def select(query, args):
    db = dbConnect()
    with db.cursor() as cursor:
        if args == None:
            cursor.execute(query)
        else:
            cursor.execute(query, args)
        row = cursor.fetchone()
    db.close()
    return row

def checkLogin(username, password):
    query = """SELECT password, username FROM User WHERE username=%s"""
    info = select(query, (username, ))
    if bcrypt.checkpw(password.encode('utf-8'), info[0].encode('utf-8')):
        return True, info[1]
    else:
        return False, 0

# check if post exists
def existingID(id):
    query = """SELECT * FROM BlogPost ORDER BY postID DESC LIMIT 1"""
    row = select(query, None)
    if row[0] >= int(id) and  int(id) >= 1:
        return True
    else:
        return False

# called to determine what navigation arrows are needed
def checkNeighborPosts(id):
    id = int(id)
    if existingID(id+1) and existingID(id-1):
        return 'both'
    elif existingID(id+1):
        return 'next'
    elif existingID(id-1):
        return 'previous'
    else:
        return 'none'

def getNewID():
    query = """SELECT * FROM BlogPost ORDER BY postID DESC LIMIT 1"""
    row = select(query, None)
    return row[0]+1

def getPosts():
    db = dbConnect()
    with db.cursor() as cursor:
        cursor.execute("""SELECT postID, date_format(time, '%M %D, %Y'), title, subtitle, body, image, time FROM BlogPost ORDER BY time DESC""")
        rows = cursor.fetchall()
    db.close()
    return rows


def getPost(id):
    query = """SELECT date_format(time, '%M %D, %Y'), title, subtitle, body, image, date_format(editedTime, '%M %D, %Y') FROM BlogPost WHERE postID = %s"""
    row = select(query, (id,))
    return row

def addPost(time, title, subtitle, body, imageURL, postid, edittime=datetime.datetime.now()):
    db = dbConnect()
    with db.cursor() as cursor:
        #check id, if new, insert, if existing, update
        if existingID(postid):
            query = """UPDATE BlogPost SET editedTime=%s, title=%s, subtitle=%s, body=%s, image=%s WHERE postID=%s"""
            cursor.execute(query, (edittime, title, subtitle, body, imageURL, postid))
        else:
            query = """INSERT INTO BlogPost(time, title, subtitle, body, image) VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (time, title, subtitle, body, imageURL))
    db.commit()

# landing page; list of all blog posts
@app.route('/')
def blog():
    posts = getPosts()
    return render_template('blog.html', posts = posts, len = len(posts))


# login page, checks if user is logged into session(if so, direct to new post)
@app.route('/login', methods=['POST', 'GET'])
def login():
    if session.get('loggedIn') is not None and session.get('loggedIn') == True:
        id = getNewID()
        return redirect(url_for('editNewPost', id=id))
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            a = checkLogin(username, password)
            if a[0]:
                session['loggedIn'] = True
                session['username'] = username
                flash('login successful')
                id = getNewID()
                return redirect(url_for('editNewPost', id=id))
            else:
                    flash('incorrect password')
                    return render_template('login.html')
        else:
            return render_template('login.html')

# new blog post page
@app.route('/post/new/<id>', methods=['POST', 'GET'])
def editNewPost(id):
    if session.get('loggedIn') is None or session.get('loggedIn') == False:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            title = request.form['title']
            subtitle = request.form['subtitle']
            body = request.form['body']
            time = datetime.datetime.now()
            imageURL = request.form['imageurl']
            addPost(time, title, subtitle, body, imageURL, id)
            flash('added post')
            return redirect(url_for('blog'))
        else:
            date = datetime.datetime.now()
            fDate = date.strftime('%B %d, %Y')
            return render_template('newPost.html', id=id, date=fDate)

# page for viewing entire blog post
@app.route('/post/<int:id>')
def blogPost(id):
    if session.get('loggedIn') is None or session.get('loggedIn') == False:
        login=False
    else:
        login=True
    post = getPost(id)
    markup = Markup(post[3])
    arrowDisplay=checkNeighborPosts(id)
    return render_template('blogPost.html', id=id, time=post[0], title=post[1], subtitle=post[2],
    body=markup, imageURL=post[4], editedtime=post[5], login=login, arrow=arrowDisplay)

# url to log user out of session
@app.route('/logout')
def logout():
    session.pop('loggedIn')
    session.pop('username')
    return redirect(url_for('about'))

# edit page for existing blog post
@app.route('/post/edit/<id>', methods=['POST', 'GET'])
def editPost(id):
    if session.get('loggedIn') is None or session.get('loggedIn') == False:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            title = request.form['title']
            subtitle = request.form['subtitle']
            body = request.form['editordata']
            imageURL = request.form['previewImageURL']
            addPost(0, title, subtitle, body, imageURL, id)
            flash('edited post')
            return redirect(url_for('blog'))
        else:
            post = getPost(id)
            date = datetime.datetime.now()
            fDate = date.strftime('%B %-d, %Y')
            return render_template('editPost.html', id=id, date=post[0], newdate=fDate, title=post[1],
             subtitle=post[2], body=post[3], image=post[4])

if __name__ == '__main__':
    app.run(debug=True)

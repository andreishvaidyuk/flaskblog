from flask import Flask, render_template, flash, session, request, redirect
from flask_bootstrap import Bootstrap
import pypyodbc
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
import uvicorn


# creating connection Object which will contain SQL Server Connection
connection = pypyodbc.connect('Driver={SQL Server};Server=localhost;Database=FLASK_BLOG_DB;pwd=')


app = Flask(__name__)
Bootstrap(app)
CKEditor(app)

# секретный ключ для управления сессиями
app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/')
def index():
    cursor = connection.cursor()
    result_value = cursor.execute("Select * FROM [blog]")
    if result_value is not None:
        blogs = cursor.fetchall()
        cursor.close()
        return render_template('index.html', blogs=blogs)
    return render_template('index.html', blogs=None)


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/blogs/<int:id>/')
def blogs(id):
    cursor = connection.cursor()
    result_value = cursor.execute("SELECT * FROM [blog] WHERE BlogId={}".format(id))
    if result_value is not None:
        blog = cursor.fetchone()
        return render_template('blogs.html', blog=blog)
    return "Blog is not founded."


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_details = request.form
        if user_details['Password'] != user_details['ConfirmPassword']:
            flash('Passwords do not match. Try again', 'danger')
            return render_template('register.html')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO [user](FirstName, LastName, Username, Email, Password) "
                       "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(
                       user_details["FirstName"],
                       user_details["LastName"],
                       user_details["Username"],
                       user_details["Email"],
                       generate_password_hash(user_details["Password"]))
        )
        connection.commit()
        cursor.close()
        flash("Registration successful. Please login", 'success')
        return redirect('/login')

    return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user_details = request.form
        username = user_details['Username']
        cursor = connection.cursor()
        result_value = cursor.execute("SELECT * FROM [user] WHERE Username = '{0}'".format(username))
        if result_value is not None:
            user = cursor.fetchone()
            if check_password_hash(user['password'], user_details['Password']):
                session['login'] = True
                session['FirstName'] = user['firstname']
                session['LastName'] = user['lastname']
                author = session['FirstName'] + ' ' + session['LastName']
                flash('Welcome ' + author + '! You have been successfully logged in!', 'success')
            else:
                cursor.close()
                flash('Password is incorrect!', 'danger')
                return render_template('login.html')
        else:
            cursor.close()
            flash('User is not exist!', 'danger')
            return render_template('login.html')
        cursor.close()
        return redirect('/')
    return render_template('login.html')


@app.route('/write-blog/', methods=['GET', 'POST'])
def write_blog():
    if request.method == 'POST':
        blogpost = request.form
        title = blogpost["Title"]
        body = blogpost["Body"]
        author = session["FirstName"] + " " + session["LastName"]
        cursor = connection.cursor()
        cursor.execute("INSERT INTO [blog](Title, Body, Author) VALUES ('{0}', '{1}', '{2}')".format(
                        title,
                        body,
                        author
                        )
        )
        connection.commit()
        cursor.close()
        flash('Your post is successfully posted!', 'success')
        return redirect('/')
    return render_template('write_blog.html')


@app.route('/my-blogs/', methods=['GET'])
def my_blogs():
    author = session["FirstName"] + " " + session["LastName"]
    cursor = connection.cursor()
    result_value = cursor.execute("SELECT * FROM [blog] WHERE Author='{0}'".format(author))
    if result_value is not None:
        my_blogs = cursor.fetchall()
        return render_template('my_blogs.html', my_blogs=my_blogs)
    else:
        return render_template('my_blogs.html', my_blogs=None)


@app.route('/edit-blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == 'POST':
        cursor = connection.cursor()
        blogpost = request.form
        title = blogpost["Title"]
        body = blogpost["Body"]
        cursor.execute("UPDATE [blog] SET Title='{0}', Body = '{1}' WHERE BlogId='{2}'".format(title, body, id))
        connection.commit()
        cursor.close()
        flash("Blog is updated successfully", "success")
        return redirect('/blogs/{0}'.format(id))
    cursor = connection.cursor()
    result_value = cursor.execute("SELECT * FROM [blog] WHERE BlogId={0}".format(id))
    if result_value is not None:
        blog = cursor.fetchone()
        blog_form = {}
        blog_form['title'] = blog['title']
        blog_form['body'] = blog['body']
        return render_template('edit_blog.html', blog_form=blog_form)


@app.route('/delete-blog/<int:id>/')
def delete_blog(id):
    cursor = connection.cursor()
    cursor.execute("DELETE from [blog] WHERE BlogId='{0}'".format(id))
    connection.commit()
    flash("Your blog has been deleted", "success")
    return redirect('/my-blogs')


@app.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out', "info")
    return redirect('/')


# if __name__ == "__main__":
#     app.run()

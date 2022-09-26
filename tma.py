from flask import Flask
from flask_session import Session
from flask_pymongo import PyMongo, ObjectId
from flask import Flask, render_template, request, Response, json, flash, redirect, url_for, session
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb://localhost:27017/TMA"
app.config['SECRET_KEY'] = "@123rest$%^"

bcrypt = Bcrypt(app)
mongo = PyMongo(app)

db = mongo.db.task
progress = mongo.db.on_progress
completed = mongo.db.completed
retrieveall = mongo.db.retrieveall

events = [
    {
        'title': 'TestEvent',
        'start': '2022-09-22',
        'end': '',
        'url': 'https://youtube.com'
    },
    {
        'title': 'Another TestEvent',
        'start': '2022-09-24',
        'end': '2022-09-26',
        'url': 'https://google.com'
    }
]


@app.route("/")
def homepage():
    return render_template("homepage.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        Full_name = request.form['Full_name']
        Email = request.form['Email']
        Password = request.form['Password']
        hashed_password = bcrypt.generate_password_hash(
            Password).decode('utf-8')
        if ((db.count_documents({'email': Email})) != 0):
            flash(f'Email Id already exists!!!', 'danger')
        else:
            user = {
                'name': Full_name,
                'email': Email,
                'Password': hashed_password
            }
            db.insert_one(user)
            flash(f'User {Full_name} is successfully created', 'success')
            return redirect(url_for('login'))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["Email"]
        password = request.form["Password"]
        email_pass = db.find_one({'email': email}, {'_id': 0, 'Password': 1})
        if bcrypt.check_password_hash(email_pass['Password'], password):
            session['email'] = email
            flash(f'Log in successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'Invalid credentials', 'danger')
    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        task1 = request.form["task"]
        create_task = {
            'on_progress': task1,
            'email': session['email']
        }
        progress.insert_one(create_task)
        create_rtask = {
            'retrieved_tasks': task1,
            'email': session['email']
        }
        retrieveall.insert_one(create_rtask)

        c_task = completed.find({'email': session['email']})
        return render_template('dashboard.html', comp_v=c_task, task=progress.find({"email": session['email']}))
    return render_template("dashboard.html", comp_v=completed.find({'email': session['email']}), task=progress.find({"email": session['email']}))


@app.route("/on_progress/<id>", methods=["GET", "POST"])
def progr(id):
    if request.method == "GET":
        s = list(progress.find({"_id": ObjectId(id)}, {"on_progress": 1}))
        s1 = progress.find({"_id": ObjectId(id)}, {"on_progress": 1})
        # retrieveall.insert_one({"retrieved_tasks":s[0]['on_progress'],"email":session['email']})
        completed.insert_one(
            {"completed": s[0]['on_progress'], "email": session['email']})
        comp_task = list(completed.find({}, {"completed": 1}))

        progress.delete_one({"_id": ObjectId(id)})
        return render_template("dashboard.html", comp_v=comp_task, task=progress.find({"email": session['email']}))
    return render_template("dashboard.html", comp_v=comp_task, task=progress.find({"email": session['email']}))


@app.route("/update/<id>", methods=["GET", "POST"])
def update(id):
    if request.method == 'GET':
        emp = []
        updata = progress.find({'_id': ObjectId(id)}, {})
        print(updata)
        for i in updata:
            emp.append(i)
            print(emp)

    if request.method == "POST":
        task = request.form.get("task")
        progress.update_one({"_id": ObjectId(id)}, {
                            "$set": {'on_progress': task}})
        comp_task = list(completed.find({}, {"completed": 1}))
        return render_template('dashboard.html', comp_v=comp_task, task=progress.find({"email": session['email']}))

    return render_template("update.html", emps=emp)


@app.route("/retrieveall", methods=["GET", "POST"])
def retrieve():
    r_task = list(retrieveall.find(
        {"email": session["email"]}, {"retrieved_tasks": 1}))
    return render_template("retrieveall.html", task=r_task)


@app.route("/profile", methods=["GET", "POST"])
def profile():

    details = list(db.find({"email": session["email"]}, {}))
    c_task = completed.count_documents(
        {'email': session['email']})
    p_task = progress.count_documents(
        {'email': session['email']})
    percent = int((c_task/(p_task + c_task))*100)
    # except ZeroDivisionError:
    # percent = 70
    return render_template("profile.html", percent=percent, details=details, c_task=c_task, p_task=p_task)


@app.route("/delete/<id>", methods=["GET", "POST"])
def delete(id):
    delete_task = list(progress.find(
        {"_id": ObjectId(id)}, {"on_progress": 1}))
    task = delete_task[0]["on_progress"]
    progress.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('dashboard'))


@app.route("/clearall", methods=["GET", "POST"])
def clearall():
    completed.delete_many({})
    return redirect(url_for('dashboard'))


@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    return render_template("calendar.html", events=events)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form['title']
        start = request.form['start']
        end = request.form['end']
        url = request.form['url']
        if end == '':
            end = start
        events.append({
            'title': title,
            'start': start,
            'end': end,
            'url': url
        },
        )
    return render_template('add.html')


@app.route("/remove", methods=["GET", "POST"])
def remove():
    progress.delete_one({"email": session["email"]})
    completed.delete_one({"email": session["email"]})
    db.delete_one({"email": session["email"]})
    return redirect(url_for('homepage'))


@app.route("/signout", methods=["GET", "POST"])
def signout():
    session['email'] = None
    return redirect(url_for('homepage'))


if __name__ == "__main__":
    app.run(debug=True)

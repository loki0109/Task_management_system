from flask import Flask
from flask_session import Session
from flask_pymongo import PyMongo
from flask import Flask,render_template,request,Response,json,flash,redirect,url_for,session
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['MONGO_URI']="mongodb://localhost:27017/TMA"
app.config['SECRET_KEY'] = "@123rest$%^"

bcrypt = Bcrypt(app)

mongo = PyMongo(app)

db = mongo.db.task
progress = mongo.db.on_progress
completed=mongo.db.completed

@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        Full_name = request.form['Full_name']
        Email = request.form['Email']
        Password = request.form['Password']
        hashed_password = bcrypt.generate_password_hash(Password).decode('utf-8')
        if((db.count_documents({'email':Email}))!=0):
            flash(f'Email Id already exists!!!','danger')
        else:
            user = {
                'name': Full_name,
                'email':Email,
                'Password': hashed_password
            }
            db.insert_one(user)
            flash(f'User {Full_name} is successfully created','success')
            return redirect(url_for('login'))
    return render_template("register.html")

@app.route("/login", methods = ["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["Email"]
        password = request.form["Password"]
        email_pass = db.find_one({'email':email},{'_id':0,'Password':1})
        if bcrypt.check_password_hash(email_pass['Password'],password):
            session['email']=email
            flash(f'Log in successful','success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'Invalid credentials','danger')
    return render_template("login.html")

@app.route("/dashboard",methods=["GET","POST"])
def dashboard():
    if request.method == "POST":
        global task1
        task1 = request.form["task"]
        print(task1)
        print(session['email'])
        create_task = {
            'on_progress' : task1,
            'email' : session['email']
        }
        progress.insert_one(create_task) 
        return render_template('dashboard.html',task=task1)
    return render_template("dashboard.html")

def on_progress():
    if request.method == "GET":
        print(task1)
        show_task = progress.find({on_progress:1},{"email":session['email']})
        print(show_task)
    return render_template("dashboard.html")

if __name__=="__main__":
    app.run(debug=True)

from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
import email_validator
from passlib.hash import sha256_crypt
from functools import wraps



#user entry decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page","danger")
            return redirect(url_for("login"))
    return decorated_function

#register forms are here

class RegisterForm(Form):
    name = StringField("Name/Last name:",validators=[validators.Length(min = 3 , max = 30)])
    username = StringField("Username:",validators=[validators.Length(min = 3 , max = 35),validators.DataRequired(message="Required")])
    email = StringField("E-mail:",validators=[validators.Email(message="Please enter a valid e-mail address") ,validators.DataRequired(message="Required")])
    password = PasswordField("Password:",validators=[validators.EqualTo(fieldname="confirm",message="Your password does not match"),validators.DataRequired(message="Enter a stong password")])
    confirm = PasswordField("Confirm password")

# Login form here
class LoginForm(Form):
    
    username = StringField("Username:")
    password = PasswordField("Password")

# recipe form here
class RecipeForm(Form):
    
    title = StringField("Title:")
    recipe = TextAreaField(" Your Recipe:", validators= [validators.Length(min = 20)])

app = Flask(__name__)
app.secret_key = "recipers496"

app.config["MYSQL_HOST"] = "melihwho.mysql.pythonanywhere-services.com"
app.config["MYSQL_USER"] = "melihwho"
app.config["MYSQL_PASSWORD"] = "mysql4963db"
app.config["MYSQL_DB"] = "reciper"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():

    
    return render_template("index.html")

# adding recipes
@app.route("/addrecipe", methods = ["GET","POST"])
def addrecipe():
    form = RecipeForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        recipe = form.recipe.data

        cursor = mysql.connection.cursor()
        query = "Insert into recipes(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(query,(title,session["username"],recipe))
        mysql.connection.commit()

        cursor.close()

        flash("Your recipe has been added successfully","success")

        return redirect(url_for("dashboard"))
    return render_template("addrecipe.html", form = form)


# updating recipes

@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):

    if request.method == "GET":

        cursor = mysql.connection.cursor()

        query = "Select * From recipes where id = %s and author = %s"

        result = cursor.execute(query,(id,session["username"]))

        if result == 0:
            flash("There is no such recipe or you don't have the authority to acces this recipe","danger")
            return redirect(url_for("index"))
            
        else:
            recipes = cursor.fetchone()
            form = RecipeForm()

            form.title.data = recipes["title"]
            form.recipe.data = recipes["content"]

            return render_template("update.html",form = form)

    else:
        # post request

        form = RecipeForm(request.form)

        newtitle = form.title.data
        newcontent = form.recipe.data 

        query2 = "Update recipes Set title = %s ,content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(query2,(newtitle,newcontent,id))

        mysql.connection.commit()
        
        flash("Your recipe has been updated successfully", "success")
        
        return redirect(url_for("dashboard"))


    


# Deleting recipes

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "Select * from recipes where author = %s and id = %s"
    result = cursor.execute(query,(session["username"],id))

    if result > 0:
        query2 = "Delete from recipes where id = %s"
        cursor.execute(query2,(id,))
        mysql.connection.commit()
        
        return redirect(url_for("dashboard"))

    else:
        flash("There is no such a recipe or you don't have the authority to delete this recipe","danger")
        return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "Select * from recipes where author = %s"
    result = cursor.execute(query,(session["username"],))

    if result > 0 :
        recipes = cursor.fetchall()
        return render_template("dashboard.html",recipes = recipes)

    else:
        return render_template("dashboard.html" )



@app.route("/recipe/<string:id>")
def details(id):
    cursor = mysql.connection.cursor()
    query = "Select * from recipes where id = %s"

    result = cursor.execute(query,(id,))
    
    if result > 0 :
        recipe = cursor.fetchone()
        return render_template("recipe.html",recipe = recipe) 
    else:
        return render_template("recipe.html")

#Register place
@app.route("/sign-up",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()
        

        send = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(send,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash("You have registered successfully!","success")


        return redirect(url_for("index"))

    else:
        return render_template("signup.html", form = form)

# search url
@app.route("/search",methods = ["GET","POST"])
def search():

    if request.method == "GET":
        return redirect(url_for("index"))

    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        query = "Select * From recipes where title like '%" + keyword + "%' "
        result = cursor.execute(query)

        if result == 0 :
            flash("No matches","danger")
            return redirect(url_for("recipes"))
    
        else:
            recipes = cursor.fetchall()
            
            return render_template("writtenrecipes.html",recipes = recipes)

# log in page

@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        query = "Select * From users where username = %s "

        result = cursor.execute(query,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("You have logged in successfully","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))

            else:
                flash("Wrong password","danger")
                return redirect(url_for("login"))
        else:
            flash("User not found!","danger")
            


    return render_template("login.html",form = form)     
    

@app.route("/recipes")
def recipes():
    cursor = mysql.connection.cursor()
    query = "Select * From recipes"
    result = cursor.execute(query)

    if result > 0:
        recipes = cursor.fetchall()
        return render_template("writtenrecipes.html",recipes = recipes)

    else:
        return render_template("writtenrecipes.html")

    return render_template("writtenrecipes.html")

#log out 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
    
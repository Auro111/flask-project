import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from models import db, Annuncio, Utente, SavedCat, SavedDog

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
# Updated to point to the database file in the instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)

with app.app_context():
    db.drop_all()
    db.create_all()

@app.route("/", endpoint='index')
def index():
    annunci = Annuncio.query.all()
    return render_template("index.html", annunci=annunci)

@app.route("/index")
def home():
    return render_template("index.html")

@app.route("/Login.html", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Utente.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Logged in successfully.")
            return redirect(url_for("utente"))
        else:
            flash("Invalid credentials.")
    return render_template("login.html")  # filename in lowercase for consistency

@app.route("/register.html", methods=["GET", "POST"], endpoint="register")
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        if Utente.query.filter_by(username=username).first():
            flash("Username already exists.")
        else:
            new_user = Utente(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registered successfully. Please log in.")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/Annuncio.html", methods=["GET"], endpoint="annuncio")
def annuncio_form():
    return render_template("Annuncio.html")

@app.route("/add_listing", methods=["POST"])
def add_listing():
    if "user_id" not in session:
        flash("Please log in to post an item.")
        return redirect(url_for("login"))
        
    title = request.form.get("title")
    desc = request.form.get("desc")
    is_cat = request.form.get("is_cat") == "1"  # checkbox returns '1' when checked
    is_dog = request.form.get("is_dog") == "1"  # new processing for dog checkbox
    image = request.files.get("image")
    
    filename = None
    if image and image.filename:
        filename = secure_filename(image.filename)
        upload_folder = app.config["UPLOAD_FOLDER"]
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        image.save(os.path.join(upload_folder, filename))
    
    new_annuncio = Annuncio(
        title=title,
        desc=desc,
        image_filename=filename,
        is_cat=1 if is_cat else 0,
        is_dog=1 if is_dog else 0,
        user_id=session.get("user_id")
    )
    db.session.add(new_annuncio)
    db.session.commit()
    flash("Listing added successfully.")
    return redirect(url_for("index"))

# Updated dogs route to filter using is_dog flag and pass variable as 'annunci'
@app.route("/dogs", endpoint="dogs")
def dogs():
    dogs_annunci = Annuncio.query.filter_by(is_dog=1).all()
    return render_template("dogs.html", annunci=dogs_annunci)

# Updated cats route to filter using is_cat flag and pass variable as 'annunci'
@app.route("/cats", endpoint="cats")
def cats():
    cats_annunci = Annuncio.query.filter_by(is_cat=1).all()
    return render_template("cats.html", annunci=cats_annunci)

@app.route("/utente", endpoint="utente")
def utente():
    if "user_id" not in session:
        flash("Please log in to view your profile.")
        return redirect(url_for("login"))
        
    user = Utente.query.get(session["user_id"])
    if not user:
        flash("User not found.")
        return redirect(url_for("login"))
        
    return render_template("utente.html", user=user)

# New route to log out the user
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully.")
    return redirect(url_for("index"))

# New route to save a listing to favorites
@app.route("/save/<int:annuncio_id>")
def save_listing(annuncio_id):
    if "user_id" not in session:
        flash("Please log in to save a listing.")
        return redirect(url_for("login"))
        
    annuncio = Annuncio.query.get(annuncio_id)
    if not annuncio:
        flash("Listing not found.")
        return redirect(url_for("index"))
        
    user_id = session["user_id"]
    # Depending on the type, save in the appropriate table
    if annuncio.is_cat:
        # Check if already saved
        if not any(s.annuncio_id == annuncio_id for s in Utente.query.get(user_id).saved_cats):
            saved = SavedCat(utente_id=user_id, annuncio_id=annuncio_id)
            db.session.add(saved)
            db.session.commit()
            flash("Cat listing saved.")
        else:
            flash("Already saved.")
    elif annuncio.is_dog:
        if not any(s.annuncio_id == annuncio_id for s in Utente.query.get(user_id).saved_dogs):
            saved = SavedDog(utente_id=user_id, annuncio_id=annuncio_id)
            db.session.add(saved)
            db.session.commit()
            flash("Dog listing saved.")
        else:
            flash("Already saved.")
    else:
        flash("Listing type not recognized.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)

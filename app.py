from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import mysql.connector
import hashlib

app = Flask(__name__)
CORS(app)

# 🔐 REQUIRED FOR SESSION
app.secret_key = "nature_explorer_secret_key"

# ---------------- DATABASE ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="nature_explorer"
)

cursor = db.cursor(dictionary=True)

# ---------------- PASSWORD HASH ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- HOME PAGE (SHOW POSTS) ----------------
@app.route("/")
def index():
    cursor.execute("""
        SELECT posts.*, user.name
        FROM posts
        JOIN user ON posts.user_id = user.id
        ORDER BY posts.created_at DESC
    """)
    posts = cursor.fetchall()
    return render_template("index.html", posts=posts)


# ---------------- ABOUT PAGE ----------------
@app.route("/about")
def about():
    if "user_id" not in session:
        return redirect("/")
    return render_template("about.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = hash_password(data.get("password"))

    cursor.execute("SELECT * FROM user WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "Email already exists ❌"}), 400

    cursor.execute(
        "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)",
        (name, email, password)
    )
    db.commit()

    return jsonify({"success": True, "message": "Signup successful ✅"})

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = hash_password(data.get("password"))

    cursor.execute(
        "SELECT * FROM user WHERE email=%s AND password=%s",
        (email, password)
    )
    user = cursor.fetchone()

    if user:
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return jsonify({"success": True, "redirect": url_for("about")})

    return jsonify({"success": False, "message": "Invalid email or password ❌"}), 401

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- ADD POST PAGE ----------------
@app.route("/add-post", methods=["GET", "POST"])
def add_post():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO posts (title, content, user_id) VALUES (%s, %s, %s)",
            (title, content, session["user_id"])
        )
        db.commit()

        # 🔁 redirect to HOME PAGE
        return redirect("/")

    return render_template("add_post.html")


# ---------------- SAVE POST ----------------
@app.route("/save-post", methods=["POST"])
def save_post():
    if "user_id" not in session:
        return redirect("/")

    title = request.form.get("title")
    content = request.form.get("content")

    cursor.execute(
        "INSERT INTO posts (title, content, user_id) VALUES (%s, %s, %s)",
        (title, content, session["user_id"])
    )
    db.commit()

    return redirect("/")   # redirect to homepage to view post

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run()



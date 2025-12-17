from flask import Flask, request, jsonify, send_from_directory
import csv, os, uuid, hashlib
from datetime import datetime, timezone, timedelta
from flask_cors import CORS
import webview  
import threading

html_file = os.path.join(os.path.dirname(__file__), "index.html")
app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Data")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
BOOKS_FILE = os.path.join(DATA_DIR, "books.csv")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")
DASH_FILE = os.path.join("dashboard.html")
INDEX_FILE = os.path.join(html_file)
APP_FILE = os.path.join("app.js")
STYLES_FILE = os.path.join("styles.css")
SESSIONS = {}

def load_books():
    books = []
    with open(BOOKS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            books.append(row)
    return books

def load_users():
    users = []
    with open(USERS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            users.append(row)
    return users

def books_id_count ():
    global books_id
    books_id = 0
    with open (BOOKS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for _ in r:
            books_id += 1
    return books_id + 1

def orders_id_count ():
    global orders_id
    orders_id = 0
    with open (ORDERS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for _ in r:
            orders_id += 1
    return orders_id + 1

def sales_id_count ():
    global sales_id
    sales_id = 0
    with open (SALES_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for _ in r:
            sales_id += 1
    return sales_id + 1

def users_id_count():
    global users_id
    users_id = 0
    with open(USERS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for _ in r:
            users_id += 1
    return users_id + 1


    
os.makedirs(DATA_DIR, exist_ok=True)

#hachage de mot de passe
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

#création des fichiers CSV s'ils n'existent pas
def init_csv_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "email", "password"])
    if not os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "name", "author", "genre", "price", "stock"])
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "user_id", "book_id", "quantity", "date"])
    if not os.path.exists(SALES_FILE):
        with open(SALES_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "book_id", "quantity", "total_price", "date"])

init_csv_files()

def get_user_by_email(email):
    users = load_users()
    for row in users:
        if row["email"] == email:
            return row
    return None

def get_book_by_name(name):
    name_normalized = name.lower().strip()
    books = load_books()
    for row in books:
        if row["name"].lower().strip() == name_normalized:
            return row
    return None


def auth_required(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token not in SESSIONS:
            return jsonify({"error": "Non autorisé"}), 401
        if SESSIONS[token]["expires"] < datetime.now(timezone.utc):
            del SESSIONS[token]
            return jsonify({"error": "Session expirée"}), 401
        request.user_id = SESSIONS[token]["user_id"]
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if not email or not password:
        return jsonify({"error": "Champs manquants"}), 400
    if get_user_by_email(email):
        return jsonify({"error": "Email déjà utilisé"}), 400
    user_id = users_id_count()  
    with open(USERS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([user_id, email, hash_password(password)])
    return jsonify({"message": "Inscription réussie"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    user = get_user_by_email(email)
    if not user or user["password"] != hash_password(password):
        print("LOGIN ÉCHEC : mauvais identifiants")
        return jsonify({"error": "Identifiants invalides"}), 401
    token = str(uuid.uuid4())
    SESSIONS[token] = {
        "user_id": user["id"],
        "email": user["email"],
        "expires": datetime.now(timezone.utc) + timedelta(hours=2)
    }
    return jsonify({"token": token}), 200

@app.route("/api/me", methods=["GET"])
@auth_required
def get_current_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_email = SESSIONS[token]["email"]
    return jsonify({"email": user_email}), 200


@app.route("/api/books", methods=["GET"])
@auth_required
def list_books():
    books = []
    with open(BOOKS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            books.append(row)
    return jsonify(books), 200


@app.route("/api/books", methods=["POST"])
@auth_required
def add_book():
    data = request.get_json()
    name = data.get("name", "").strip()
    author = data.get("author", "").strip()
    genre = data.get("genre", "").strip()
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))
    if not name or not author or not genre or price < 0 or stock < 0:
        return jsonify({"error": "Tous les champs sont requis et valides"}), 400
    if get_book_by_name(name):
        return jsonify({"error": "Un livre avec ce nom existe déjà"}), 400
    book_id = books_id_count()
    with open(BOOKS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([book_id, name, author, genre, price, stock])
    return jsonify({"message": "Livre ajouté avec succès", "id": book_id}), 201


@app.route("/api/orders", methods=["POST"])
@auth_required
def create_order():
    data = request.get_json()
    book_id = data.get("book_id")
    quantity = int(data.get("quantity", 1))
    books = []
    with open(BOOKS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            books.append(row)
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        return jsonify({"error": "Livre introuvable"}), 404
    if int(book["stock"]) < quantity:
        return jsonify({"error": "Stock insuffisant"}), 400
    for b in books:
        if b["id"] == book_id:
            b["stock"] = str(int(b["stock"]) - quantity)
    with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "author", "genre", "price", "stock"])
        w.writeheader()
        w.writerows(books)
    order_id = orders_id_count()
    date_str = datetime.now(timezone.utc).isoformat()
    with open(ORDERS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([order_id, request.user_id, book_id, quantity, date_str])
    total_price = float(book["price"]) * quantity
    with open(SALES_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([order_id, book_id, quantity, total_price, date_str])
    return jsonify({"message": "Commande enregistrée"}), 201

@app.route("/api/addbooks", methods=["POST"])
@auth_required
def add_books():
    data = request.get_json()
    book_id = str(data.get("book_id"))
    quantity = int(data.get("quantity", 1))
    books = []
    with open(BOOKS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            books.append(row)
    book = next((b for b in books if str(b["id"]) == book_id), None)
    if not book:
        return jsonify({"error": "Livre introuvable"}), 404
    # maj stock
    for b in books:
        if str(b["id"]) == book_id:
            b["stock"] = str(int(b["stock"]) + quantity)
    with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "author", "genre", "price", "stock"])
        w.writeheader()
        w.writerows(books)
    return jsonify({"message": "Stock mis à jour"}), 201


@app.route("/api/stats", methods=["GET"])
@auth_required
def stats():
    total_revenue = 0.0
    total_items = 0
    with open(SALES_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            total_revenue += float(row["total_price"])
            total_items += int(row["quantity"])
    return jsonify({
        "total_revenue": total_revenue,
        "total_items": total_items
    }), 200
    
@app.route("/", methods=["GET"])
def home():
    return send_from_directory(os.path.dirname(html_file), os.path.basename(html_file))
@app.route("/dashboard.html", methods=["GET"])
def dashboard():
    return send_from_directory(os.path.dirname(__file__), "dashboard.html")
@app.route("/styles.css")
def styles():
    return send_from_directory(os.path.dirname(__file__), "styles.css")
@app.route("/app.js")
def app_js():
    return send_from_directory(os.path.dirname(__file__), "app.js")
@app.route("/auth.js")
def auth_js():
    return send_from_directory(os.path.dirname(__file__), "auth.js")

def run_flask():
    app.run(port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    window = webview.create_window('Librairie App', 'http://127.0.0.1:5000')
    webview.start()
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timezone, timedelta
import csv, os, uuid, hashlib, binascii
from flask_cors import CORS
import threading
import requests
import webview  



html_file = os.path.join(os.path.dirname(__file__), "index.html")
app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Data")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
BOOKS_FILE = os.path.join(DATA_DIR, "books.csv")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.csv")
CART_FILE = os.path.join(DATA_DIR, "cart.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")
DASH_FILE = os.path.join("dashboard.html")
INDEX_FILE = os.path.join(html_file)
APP_FILE = os.path.join("app.js")
STYLES_FILE = os.path.join("styles.css")
LOG_FILE = os.path.join(DATA_DIR, "log.csv")
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

def cart_id_count():
    global cart_id
    cart_id = 0
    if not os.path.exists(CART_FILE):
        return 1
    with open(CART_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for _ in r:
            cart_id += 1
    return cart_id + 1

    
os.makedirs(DATA_DIR, exist_ok=True)


#hachage de mot de passe
def hash_password(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    )
    return binascii.hexlify(dk).decode("utf-8")

def generate_salt(length: int = 16) -> str:
    return binascii.hexlify(os.urandom(length)).decode("utf-8")


#création des fichiers CSV s'ils n'existent pas
def init_csv_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "email", "salt", "password"])
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
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "level", "user_id", "endpoint", "action", "details"])
    if not os.path.exists(CART_FILE):
        with open(CART_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "user_id", "book_id", "quantity", "date"])

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


def write_log(level, endpoint, action, details="", user_id=None):
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([timestamp, level, user_id or "", endpoint, action, details])


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

ADMIN_EMAIL = "admin@admin.com"

def admin_required(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        session = SESSIONS.get(token)
        endpoint = request.path
        if not session or session["email"] != ADMIN_EMAIL:
            uid = session["user_id"] if session else None
            write_log("WARNING", endpoint, "admin_forbidden", "accès non admin", user_id=uid)
            return jsonify({"error": "Accès réservé aux admins"}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


#Inscription
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    sha_password = hashlib.sha1(password.encode()).hexdigest()
    sha_prefix = sha_password[0:5]
    sha_postfix = sha_password[5:].upper()

    url = "https://api.pwnedpasswords.com/range/" + sha_prefix

    payload={}
    headers={}

    response = requests.request("GET", url, headers=headers, data=payload)
    pwnd_dict = {}

    pwnd_list = response.text.split("\r\n")
    for pwnd_pass in pwnd_list:
        pwnd_hash = pwnd_pass.split(":")
        pwnd_dict[pwnd_hash[0]] = pwnd_hash[1]

    if not email or not password:
        return jsonify({"error": "Champs manquants"}), 400
    if get_user_by_email(email):
        return jsonify({"error": "Email déjà utilisé"}), 400
    user_id = users_id_count()
    salt = generate_salt()
    password_hash = hash_password(password, salt)
    if sha_postfix in pwnd_dict.keys():
        return jsonify({"error": "Mot de passe compromis"}), 400
    else:
        with open(USERS_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([user_id, email, salt, password_hash])
        return jsonify({"message": "Inscription réussie"}), 201


#Connexion
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    user = get_user_by_email(email)
    if not user:
        write_log("WARNING", "/api/login", "login_failed", f"email={email}")
        return jsonify({"error": "Identifiants invalides"}), 401
    salt = user["salt"]
    expected_hash = user["password"]
    if hash_password(password, salt) != expected_hash:
        write_log("WARNING", "/api/login", "login_failed", f"email={email}")
        return jsonify({"error": "Identifiants invalides"}), 401
    token = str(uuid.uuid4())
    SESSIONS[token] = {
        "user_id": user["id"],
        "email": user["email"],
        "expires": datetime.now(timezone.utc) + timedelta(hours=2)
    }
    write_log("INFO", "/api/login", "login_success", f"email={email}", user_id=user["id"])
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

#Ajout de livre
@app.route("/api/books", methods=["POST"])
@auth_required
@admin_required
def add_book():
    data = request.get_json()
    name = data.get("name", "").strip()
    author = data.get("author", "").strip()
    genre = data.get("genre", "").strip()
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))
    if not name or not author or not genre or price <= 0 or stock <= 0:
        write_log("WARNING", "/api/books", "add_book_invalid", "champs manquants/invalides", user_id=request.user_id)
        return jsonify({"error": "Tous les champs sont requis et valides"}), 400
    if get_book_by_name(name):
        write_log("WARNING", "/api/books", "add_book_duplicate", f"name={name}", user_id=request.user_id)
        return jsonify({"error": "Un livre avec ce nom existe déjà"}), 400
    book_id = books_id_count()
    with open(BOOKS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([book_id, name, author, genre, price, stock])
    write_log("INFO", "/api/books", "add_book_success", f"id={book_id},name={name}", user_id=request.user_id)
    return jsonify({"message": "Livre ajouté avec succès", "id": book_id}), 201

#Suppression de livre
@app.route("/api/deletebooks", methods=["POST"])
@auth_required
@admin_required
def delete_books():
    data = request.get_json()
    book_id = str(data.get("book_id"))
    name = str(data.get("book_name")).strip()
    with open("./data/books.csv", "r", newline="") as infile:
        reader = csv.reader(infile)
        rows = [row for row in reader if row[0] != book_id]
    with open("./data/books.csv", "w", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)
        write_log("INFO", "/api/deletebooks", "Item_Deleted", f"book_id={book_id}, name={name}", user_id=request.user_id)


    return jsonify({"message": "Article supprimé"}), 201

#Passer une commande
@app.route("/api/orders", methods=["POST"])
@auth_required
def create_order():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    data = request.get_json()
    email = SESSIONS[token]["email"]
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
    write_log("INFO", "/api/orders", "order_successfully_registered","" f"email={email }," f"id={order_id},quantity={quantity}", user_id=request.user_id)
    return jsonify({"message": "Commande enregistrée"}), 201

@app.route("/api/cart", methods=["GET"])
@auth_required  
def get_cart():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = SESSIONS[token]["user_id"]
    cart_items = []
    books = load_books()
    books_map = {b["id"]: b for b in books}
    with open(CART_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["user_id"] == user_id:
                book = books_map.get(str(row["book_id"]))
                row["book_name"] = book["name"] if book else "Livre introuvable"
                cart_items.append(row)
    return jsonify(cart_items), 200

@app.route("/api/cart", methods=["POST"])
@auth_required
def add_to_cart():
    data = request.get_json()
    book_id = str(data.get("book_id"))
    quantity = int(data.get("quantity", 1))
    if quantity <= 0:
        return jsonify({"error": "Quantité invalide"}), 400
    books = load_books()
    book = next((b for b in books if str(b["id"]) == str(book_id)), None)
    if not book:
        return jsonify({"error": "Livre introuvable"}), 404
    if int(book["stock"]) < quantity:
        return jsonify({"error": "Stock insuffisant"}), 400
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = SESSIONS[token]["user_id"]
    
    cart_items = []
    existing_item = None
    with open(CART_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["user_id"] == user_id and row["book_id"] == book_id:
                existing_item = row
                row["quantity"] = str(int(row["quantity"]) + quantity)
            cart_items.append(row)
    
    if existing_item:
        with open(CART_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "user_id", "book_id", "quantity", "date_added"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(cart_items)
        book["stock"] = str(int(book["stock"]) - quantity)
        with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "name", "author", "genre", "price", "stock"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(books)
        return jsonify({"message": "Quantité mise à jour dans le panier", "cart_id": existing_item["id"]}), 200
    else:
        cart_item_id = cart_id_count()
        date_added = datetime.now(timezone.utc).isoformat()
        with open(CART_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([cart_item_id, user_id, book_id, quantity, date_added])
        book["stock"] = str(int(book["stock"]) - quantity)
        with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "name", "author", "genre", "price", "stock"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(books)
        return jsonify({"message": "Article ajouté au panier", "cart_id": cart_item_id}), 201

@app.route("/api/cart/<cartid>", methods=["DELETE"])
@auth_required
def remove_from_cart(cartid):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = SESSIONS[token]["user_id"]
    cart_items = []
    removed_quantity = 0
    removed_book_id = None
    with open(CART_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["id"] == str(cartid) and row["user_id"] == user_id:
                removed_quantity = int(row["quantity"])
                removed_book_id = row["book_id"]
                continue
            cart_items.append(row)
    if not removed_book_id:
        return jsonify({"error": "Article introuvable dans le panier"}), 404
    with open(CART_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "user_id", "book_id", "quantity", "date_added"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(cart_items)
    books = load_books()
    book = next((b for b in books if str(b["id"]) == str(removed_book_id)), None)
    if book:
        book["stock"] = str(int(book["stock"]) + removed_quantity)
        with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "name", "author", "genre", "price", "stock"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(books)
    return jsonify({"message": "Article supprimé du panier"}), 200

@app.route("/api/cart/checkout", methods=["POST"])
@auth_required
def checkout_cart():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = SESSIONS[token]["user_id"]
    cart_items = []
    with open(CART_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["user_id"] == user_id:
                cart_items.append(row)
    if not cart_items:
        return jsonify({"error": "Panier vide"}), 400
    books = load_books()
    books_map = {b["id"]: b for b in books}
    for item in cart_items:
        b = books_map.get(str(item["book_id"]))
        if not b:
            return jsonify({"error": f"Livre {item['book_id']} introuvable"}), 404

    for item in cart_items:
        order_id = orders_id_count()
        date_str = datetime.now(timezone.utc).isoformat()
        with open(ORDERS_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([order_id, user_id, item["book_id"], item["quantity"], date_str])
        total_price = float(books_map[item["book_id"]]["price"]) * int(item["quantity"])
        with open(SALES_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([order_id, item["book_id"], item["quantity"], total_price, date_str])
    remaining = []
    with open(CART_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["user_id"] != user_id:
                remaining.append(row)
    with open(CART_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "user_id", "book_id", "quantity", "date_added"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(remaining)
    write_log("INFO", "/api/cart/checkout", "checkout_success", f"items={len(cart_items)}", user_id=user_id)
    return jsonify({"message": "Achat finalisé", "items": len(cart_items)}), 200

@app.route("/api/orders", methods=["GET"])
@auth_required
def get_orders():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_id = SESSIONS[token]["user_id"]
    orders = []
    books = load_books()
    books_map = {b["id"]: b for b in books}
    with open(ORDERS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["user_id"] == user_id:
                book = books_map.get(str(row["book_id"]))
                row["book_name"] = book["name"] if book else "Livre introuvable"
                orders.append(row)
    # Retourner les 10 derniers achats
    return jsonify(orders[-10:]), 200

#Renouveler le stock
@app.route("/api/addbooks", methods=["POST"])
@auth_required
@admin_required
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
    for b in books:
        if str(b["id"]) == book_id:
            b["stock"] = str(int(b["stock"]) + quantity)
    with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "author", "genre", "price", "stock"])
        w.writeheader()
        w.writerows(books)
    write_log("INFO", "/api/addbooks", "Stock_renewed", f"book_id={book_id},quantity={quantity}", user_id=request.user_id)
    return jsonify({"message": "Stock mis à jour"}), 201

#Modifier le prix
@app.route("/api/books/<bookid>/price", methods=["PUT"])
@auth_required
@admin_required
def modifyPrice(bookid):
    data = request.get_json()
    try:
        new_price = float(data.get("price", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Prix invalide"}), 400
    if new_price <= 0:
        return jsonify({"error": "Le prix doit être positif"}), 400
    books = []
    with open(BOOKS_FILE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            books.append(row)
    book = next((b for b in books if str(b["id"]) == str(bookid)), None)
    if not book:
        return jsonify({"error": "Livre introuvable"}), 404
    old_price = book["price"]
    for b in books:
        if str(b["id"]) == str(bookid):
            b["price"] = str(new_price)
    with open(BOOKS_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "name", "author", "genre", "price", "stock"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(books)
    write_log("INFO",f"/api/books/{bookid}/price","update_price_success",f"old={old_price}, new={new_price}",user_id=request.user_id,)
    return jsonify({"message": "Prix mis à jour", "old_price": old_price, "new_price": new_price}), 200

#Statistiques
@app.route("/api/stats", methods=["GET"])
@auth_required
@admin_required
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
    window = webview.create_window("Amazin'", 'http://127.0.0.1:5000')
    webview.start()
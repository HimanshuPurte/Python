from flask import Flask, render_template, request, redirect, url_for, g
from flask_prometheus_metrics import register_metrics
from prometheus_client import Counter, generate_latest
import sqlite3

# Define a counter metric
products_added = Counter('products_added_total', 'Total Products Added')

app = Flask(__name__)

# SQLite Database configuration
DATABASE = 'database.db'

# Database connection helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/metrics')
def metrics():
    return generate_latest()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        
        db = get_db()
        c = db.cursor()
        c.execute("INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)", (name, description, price, stock))
        db.commit()
        # Increment the counter
        products_added.inc()
        return redirect(url_for('add_product_success'))
    return render_template('add_product.html')

@app.route('/add_product_success')
def add_product_success():
    return render_template('add_product_success.html')

@app.route('/list_products')
def list_products():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    return render_template('list_products.html', products=products)

@app.route('/reset_products', methods=['POST'])
def reset_products():
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM products")
    db.commit()
    return redirect(url_for('list_products'))

@app.route('/delete_product', methods=['POST'])
def delete_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        db = get_db()
        c = db.cursor()
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        return redirect(url_for('list_products'))

if __name__ == '__main__':
    register_metrics(app, app_version="v0.1.2", app_config="staging")
    # Run the Flask application
    app.run(debug=True, host="0.0.0.0",port=5500)

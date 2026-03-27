import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///spendsync.db")

# Categories for expenses
CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Housing & Rent",
    "Utilities",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Education",
    "Travel",
    "Subscriptions",
    "Personal Care",
    "Gifts & Donations",
    "Other"
]


@app.after_request
def after_request(response):
    """Ensure responses aren't cached."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def init_db():
    """Initialize database tables."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, category)
        )
    """)


# Initialize database on startup
init_db()


@app.route("/")
@login_required
def index():
    """Show dashboard with expense summary."""
    user_id = session["user_id"]

    # Get current month/year
    now = datetime.now()
    current_month = now.strftime("%Y-%m")

    # Get all expenses for current month
    expenses = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND date LIKE ? ORDER BY date DESC",
        user_id, current_month + "%"
    )

    # Calculate totals
    total_spent = sum(e["amount"] for e in expenses)

    # Spending by category
    category_totals = {}
    for e in expenses:
        cat = e["category"]
        category_totals[cat] = category_totals.get(cat, 0) + e["amount"]

    # Get budgets
    budgets = db.execute("SELECT * FROM budgets WHERE user_id = ?", user_id)
    budget_map = {b["category"]: b["monthly_limit"] for b in budgets}

    # Recent expenses (last 10)
    recent = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10",
        user_id
    )

    # Monthly totals for the last 6 months for chart
    monthly_data = []
    for i in range(5, -1, -1):
        month_num = now.month - i
        year = now.year
        while month_num <= 0:
            month_num += 12
            year -= 1
        month_str = f"{year}-{month_num:02d}"
        month_total = db.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? AND date LIKE ?",
            user_id, month_str + "%"
        )
        month_name = datetime(year, month_num, 1).strftime("%b %Y")
        monthly_data.append({"month": month_name, "total": month_total[0]["total"]})

    return render_template(
        "index.html",
        expenses=recent,
        total_spent=total_spent,
        category_totals=category_totals,
        budget_map=budget_map,
        monthly_data=monthly_data,
        current_month=now.strftime("%B %Y"),
        categories=CATEGORIES
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            flash("Must provide username.", "danger")
            return render_template("register.html")

        if not password:
            flash("Must provide password.", "danger")
            return render_template("register.html")

        if password != confirmation:
            flash("Passwords don't match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        # Check if username exists
        existing = db.execute("SELECT id FROM users WHERE username = ?", username)
        if existing:
            flash("Username already taken.", "danger")
            return render_template("register.html")

        # Insert user
        user_id = db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username, generate_password_hash(password)
        )

        # Log user in
        session["user_id"] = user_id
        session["username"] = username
        flash("Registered successfully! Welcome to BingSpendSync.", "success")
        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Must provide username and password.", "danger")
            return render_template("login.html")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username and/or password.", "danger")
            return render_template("login.html")

        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        flash("Welcome back!", "success")
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""
    session.clear()
    return redirect("/login")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add a new expense."""
    if request.method == "POST":
        amount = request.form.get("amount")
        category = request.form.get("category")
        description = request.form.get("description")
        date = request.form.get("date")

        if not amount or not category or not date:
            flash("Amount, category, and date are required.", "danger")
            return render_template("add.html", categories=CATEGORIES)

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Amount must be a positive number.", "danger")
            return render_template("add.html", categories=CATEGORIES)

        if category not in CATEGORIES:
            flash("Invalid category.", "danger")
            return render_template("add.html", categories=CATEGORIES)

        db.execute(
            "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
            session["user_id"], amount, category, description, date
        )

        flash("Expense added!", "success")
        return redirect("/")

    return render_template("add.html", categories=CATEGORIES)


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit(expense_id):
    """Edit an existing expense."""
    expense = db.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        expense_id, session["user_id"]
    )

    if not expense:
        flash("Expense not found.", "danger")
        return redirect("/")

    if request.method == "POST":
        amount = request.form.get("amount")
        category = request.form.get("category")
        description = request.form.get("description")
        date = request.form.get("date")

        if not amount or not category or not date:
            flash("Amount, category, and date are required.", "danger")
            return render_template("edit.html", expense=expense[0], categories=CATEGORIES)

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Amount must be a positive number.", "danger")
            return render_template("edit.html", expense=expense[0], categories=CATEGORIES)

        db.execute(
            "UPDATE expenses SET amount = ?, category = ?, description = ?, date = ? WHERE id = ? AND user_id = ?",
            amount, category, description, date, expense_id, session["user_id"]
        )

        flash("Expense updated!", "success")
        return redirect("/")

    return render_template("edit.html", expense=expense[0], categories=CATEGORIES)


@app.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete(expense_id):
    """Delete an expense."""
    db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        expense_id, session["user_id"]
    )
    flash("Expense deleted.", "info")
    return redirect("/history")


@app.route("/history")
@login_required
def history():
    """Show full expense history with filters."""
    user_id = session["user_id"]
    category_filter = request.args.get("category", "")
    month_filter = request.args.get("month", "")

    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    if month_filter:
        query += " AND date LIKE ?"
        params.append(month_filter + "%")

    query += " ORDER BY date DESC"
    expenses = db.execute(query, *params)

    total = sum(e["amount"] for e in expenses)

    return render_template(
        "history.html",
        expenses=expenses,
        categories=CATEGORIES,
        total=total,
        category_filter=category_filter,
        month_filter=month_filter
    )


@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    """Manage monthly budgets per category."""
    user_id = session["user_id"]

    if request.method == "POST":
        category = request.form.get("category")
        limit_amount = request.form.get("limit")

        if not category or not limit_amount:
            flash("Category and limit are required.", "danger")
            return redirect("/budgets")

        try:
            limit_amount = float(limit_amount)
            if limit_amount <= 0:
                raise ValueError
        except ValueError:
            flash("Limit must be a positive number.", "danger")
            return redirect("/budgets")

        # Upsert budget
        existing = db.execute(
            "SELECT id FROM budgets WHERE user_id = ? AND category = ?",
            user_id, category
        )
        if existing:
            db.execute(
                "UPDATE budgets SET monthly_limit = ? WHERE user_id = ? AND category = ?",
                limit_amount, user_id, category
            )
        else:
            db.execute(
                "INSERT INTO budgets (user_id, category, monthly_limit) VALUES (?, ?, ?)",
                user_id, category, limit_amount
            )

        flash(f"Budget for {category} set to {usd(limit_amount)}/month.", "success")
        return redirect("/budgets")

    # Get budgets with current month spending
    budget_list = db.execute("SELECT * FROM budgets WHERE user_id = ?", user_id)
    now = datetime.now()
    current_month = now.strftime("%Y-%m")

    for b in budget_list:
        spent = db.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? AND category = ? AND date LIKE ?",
            user_id, b["category"], current_month + "%"
        )
        b["spent"] = spent[0]["total"]
        b["percentage"] = min(round((b["spent"] / b["monthly_limit"]) * 100), 100) if b["monthly_limit"] > 0 else 0

    return render_template(
        "budgets.html",
        budgets=budget_list,
        categories=CATEGORIES,
        current_month=now.strftime("%B %Y")
    )


@app.route("/delete-budget/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    """Delete a budget."""
    db.execute(
        "DELETE FROM budgets WHERE id = ? AND user_id = ?",
        budget_id, session["user_id"]
    )
    flash("Budget removed.", "info")
    return redirect("/budgets")


@app.route("/api/chart-data")
@login_required
def chart_data():
    """Return chart data as JSON for AJAX requests."""
    user_id = session["user_id"]
    now = datetime.now()
    current_month = now.strftime("%Y-%m")

    # Category breakdown for current month
    expenses = db.execute(
        "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ? AND date LIKE ? GROUP BY category",
        user_id, current_month + "%"
    )

    return jsonify({
        "categories": [e["category"] for e in expenses],
        "amounts": [e["total"] for e in expenses]
    })

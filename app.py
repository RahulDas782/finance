import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    transactions_db = db.execute("SELECT symbol, SUM(shares) AS shares, price, name, SUM(shares_price) AS shares_price FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id) # HAVING SUM(shares) > 0
    cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    # return jsonify(cash_db)

    if not cash_db:
        return redirect("/login")
    else:
        cash = round(cash_db[0]["cash"], 2)

    shares_total = 0
    symbols = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)
    # return jsonify(symbols)
    for symbol in symbols:
        stock = lookup(symbol["symbol"])
        share_db = db.execute("SELECT SUM(shares) as shares FROM transactions WHERE user_id = ? AND symbol = ?", user_id, symbol["symbol"])
        share_price = share_db[0]["shares"]
        shares_total = shares_total + round(share_price * stock["price"], 2)

    user_total_cash = round(cash + shares_total, 2)

    return render_template("index.html", transactions = transactions_db, cash = cash, total = user_total_cash)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    else:
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not symbol:
            return apology("Enter symbol")

        stock = lookup(symbol.upper())

        if not stock:
            return apology("symbol not exits!")

        transactions_value = round(shares * stock["price"], 2)
        user_id = session["user_id"]
        user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        user_cash = user_cash_db[0]["cash"]

        if user_cash < transactions_value:
            return apology("not enough money")

        update_cash = round(user_cash - transactions_value, 2)
        # return jsonify(update_cash)
        
        db.execute("UPDATE users SET cash = ? WHERE id = ?", update_cash, user_id)

        date = datetime.datetime.now()

        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date, name, shares_price) VALUES (?, ?, ?, ?, ?, ?, ?)", user_id, stock["symbol"], shares, round(stock["price"], 2), date, stock["name"], transactions_value)
        flash("Bought!")

        return redirect("/")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions_db = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)
    return render_template("history.html", transactions = transactions_db)


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """User add cash"""
    if request.method == "GET":
        return render_template("cash.html")
    else:
        cash = int(request.form.get("cash"))

        user_id = session["user_id"]
        user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        user_cash = user_cash_db[0]["cash"]
        # return jsonify(user_cash_db)

        update_cash = round(user_cash + cash, 2)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", update_cash, user_id)
        flash("Cash Added!")
        return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    else:
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("Enter symbol")

        stock = lookup(symbol)

        if stock == None:
            return apology("Entered wrong symbol!")

        return render_template("quoted.html", name = stock["name"], price = stock["price"], symbol = stock["symbol"])


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Enter username")
        if not password:
            return apology("Enter password")
        if not confirmation:
            return apology("Enter confirmation")
        if password != confirmation:
            return apology("Password entered is incorrect!")

        #storing password
        hash = generate_password_hash(password)
        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
            return apology("Username already exits!")

        #No need to login again after register
        session["user_id"] = new_user
        return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        user_id = session["user_id"]
        user_symbol_db = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)
        return render_template("sell.html", symbols = [row["symbol"] for row in user_symbol_db])

    else:
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not symbol:
            return apology("Enter symbol")

        stock = lookup(symbol.upper())

        if not stock:
            return apology("symbol not exits!")

        transactions_value = round(shares * stock["price"], 2)
        # return jsonify(transactions_value)

        user_id = session["user_id"]
        user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        user_cash = user_cash_db[0]["cash"]
        # return jsonify(user_cash)

        user_share_db = db.execute("SELECT SUM(shares) AS shares FROM transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol", user_id, symbol)
        user_shares = user_share_db[0]["shares"]
        # return jsonify(user_shares)

        if shares > user_shares:
            return apology("you don't have these much of shares!")

        update_cash = round(user_cash + transactions_value, 2)
        # return jsonify(update_cash)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", update_cash, user_id)

        date = datetime.datetime.now()

        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date, name, shares_price) VALUES (?, ?, ?, ?, ?, ?, ?)", user_id, stock["symbol"], (-1) * shares, round(stock["price"], 2), date, stock["name"], (-1) * transactions_value)
        flash("Sold!")

        return redirect("/")
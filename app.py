import os
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
import database as db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

def get_current_user_id():
    """Return session user_id or None."""
    return session.get("user_id")

@app.before_request
def ensure_db():
    """Ensure database tables exist and demo user is seeded (idempotent)."""
    db.init_db()
    db.add_payment_columns()  # Add payment columns if missing
    if not getattr(ensure_db, "_seeded", False):
        seed_demo_user()
        ensure_db._seeded = True

@app.route("/")
def index():
    if get_current_user_id() is not None:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page: authenticate with username and password."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("login.html")
        user = db.get_user_by_username(username)
        if user is None:
            flash("Invalid username or password.", "error")
            return render_template("login.html")
        _id, _username, password_hash, _email, _last_payment_date, _expiry_date = user
        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            flash("Invalid username or password.", "error")
            return render_template("login.html")
        session["user_id"] = _id
        session["username"] = _username
        flash(f"Welcome back, {_username}!", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Logout and redirect to login."""
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard showing the user's gym attendance progress and payment info."""
    user_id = get_current_user_id()
    username = session.get("username", "")
    
    # Fetch workout and payment data
    rows = db.get_workouts_by_user(user_id)
    user_data = db.get_user_by_username(username)  # Fetch user data with payment details
    
    # Extract last payment and expiry date
    last_payment_date = user_data[4]  # last_payment_date is at index 4
    expiry_date = user_data[5]  # expiry_date is at index 5

    now = datetime.now()
    this_month = [
        r for r in rows
        if _parse_date(r[1]).month == now.month and _parse_date(r[1]).year == now.year
    ]
    
    return render_template(
        "dashboard.html",
        username=username,
        total_workouts=len(rows),
        this_month_count=len(this_month),
        last_payment_date=last_payment_date,  # Pass last payment date to the template
        expiry_date=expiry_date  # Pass expiry date to the template
    )

@app.route("/progress")
@login_required
def progress():
    """Show how many gym visits the user has made this month."""
    user_id = get_current_user_id()
    username = session.get("username", "")
    rows = db.get_workouts_by_user(user_id)
    now = datetime.now()
    this_month = [
        (r[0], r[1]) for r in rows
        if _parse_date(r[1]).month == now.month and _parse_date(r[1]).year == now.year
    ]
    dates = [str(d[1])[:10] for d in this_month]
    return render_template(
        "progress.html",
        username=username,
        count=len(this_month),
        dates=sorted(set(dates)),
        month=now.strftime("%B %Y"),
    )

@app.route("/update_payment", methods=["GET", "POST"])
@login_required
def update_payment():
    """Handle updating the payment date and expiry date."""
    user_id = get_current_user_id()
    user_data = db.get_user_by_username(session.get("username", ""))
    last_payment_date = user_data[4]  # Existing payment date from DB
    expiry_date = user_data[5]  # Existing expiry date from DB

    if request.method == "POST":
        payment_date = request.form.get("payment_date")
        if payment_date:
            # Set the payment date
            expiry_date = (datetime.strptime(payment_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
            # Update the payment in the database
            db.update_payment(user_id, payment_date, expiry_date)
            flash("Payment updated successfully!", "success")
            return redirect(url_for("dashboard"))
    
    return render_template("update_payment.html", last_payment_date=last_payment_date, expiry_date=expiry_date)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle user signup and create a new user."""
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        email = request.form.get("email").strip()

        # Ensure username, password, and email are not empty
        if not username or not password or not email:
            flash("Please fill in all fields.", "error")
            return render_template("signup.html")
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        
        # Create the user in the database
        user_id = db.create_user(username, hashed_password, email)

        if user_id:
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))
        else:
            flash("Username already taken, try another.", "error")
            return render_template("signup.html")

    return render_template("signup.html")

@app.route("/log_workout", methods=["GET", "POST"])
@login_required
def log_workout():
    """Log the date and time of a user's gym visit into the workouts table."""
    user_id = get_current_user_id()
    today = datetime.now().strftime("%Y-%m-%d")
    now_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if request.method == "POST":
        date_str = request.form.get("workout_date", today).strip()
        time_str = request.form.get("workout_time", datetime.now().strftime("%H:%M")).strip()
        if not date_str:
            flash("Please select a date.", "error")
            return redirect(url_for("log_workout"))
        # Store as single datetime string
        if time_str:
            visited_at = f"{date_str} {time_str}:00" if ":" in time_str and time_str.count(":") == 1 else f"{date_str} {time_str}"
        else:
            visited_at = f"{date_str} 00:00:00"
        if db.workout_exists_on_date(user_id, date_str):
            flash("You already logged a workout for that date.", "info")
        else:
            if db.add_workout(user_id, visited_at):
                flash("Workout logged successfully!", "success")
            else:
                flash("Could not save workout. Try again.", "error")
        return redirect(url_for("dashboard"))
    return render_template("log_workout.html", today=today, default_time=datetime.now().strftime("%H:%M"))


def _parse_date(value):
    """Parse date from DB (string or datetime)."""
    if hasattr(value, "month"):
        return value
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(str(value)[:19], fmt)
        except ValueError:
            continue
    return datetime.min

def seed_demo_user():
    """Create demo user if not already present."""
    if db.get_user_by_username("user1") is not None:
        return
    hashed = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Set demo user's payment date and expiry date
    last_payment_date = datetime.now().strftime("%Y-%m-%d")
    expiry_date = (datetime.now().replace(year=datetime.now().year + 1)).strftime("%Y-%m-%d")
    db.create_user("user1", hashed, "user1@example.com", last_payment_date, expiry_date)


if __name__ == "__main__":
    db.init_db()
    db.add_payment_columns()  # Ensure payment columns are added
    seed_demo_user()
    app.run(debug=True, port=5000)

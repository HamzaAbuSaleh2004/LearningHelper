# 🚀 Feature Implementation Guide

Here is your comprehensive, copy-paste-ready guide to adding PostgreSQL-based Authentication, the Referral (Share with a Friend) system, and Friend Tracking to your Flask application. We are keeping this highly modular to fit cleanly on top of your existing code.

## 1. Step-by-Step Plan
1. **Database Setup**: Open pgAdmin, create a database, and run the provided SQL scripts to create tables.
2. **Install Dependencies**: Install PostgreSQL adapter (`psycopg2-binary`) and `bcrypt`.
3. **Database Connector**: Add the `get_db_connection` function to `app.py`.
4. **Templates**: Update `onboarding.html`, create `login.html`, and update `base.html` & `course_detail.html`.
5. **Backend Logic**: Add routes for `/login`, `/logout`, `/ref/<code_str>`, and replace the `/onboard` logic to use PostgreSQL + `bcrypt`. Add a `/friends` route. 
6. **Test**: Use the test steps at the bottom to verify the full flow.

---

## 2. PostgreSQL SQL (Full Schema)

> [!IMPORTANT]  
> Open **pgAdmin**. Create a new database named `course_rec` (or similar). Open the **Query Tool** for that database and run the following exact SQL:

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    level VARCHAR(50) DEFAULT 'Beginner',
    referral_code VARCHAR(50) UNIQUE NOT NULL,
    referred_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Referrals Table (To track who invited who specifically and when)
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referred_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Friendships Table
CREATE TABLE friendships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    friend_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, friend_id) -- Prevent duplicate friends
);
```

---

## 3. Backend Code (`app.py` Modifications)

Add these new imports at the top of your `app.py`:
```python
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import string
import random
```

**Step 3.1: Add Database Connection Helper**
Paste this somewhere near your other `DATABASE HELPERS`:
```python
# ══════════════════════════════════════════════════════════════════
# POSTGRESQL CONNECTION HELPER
# ══════════════════════════════════════════════════════════════════
def get_db_connection():
    # Update with your pgAdmin username and password!
    conn = psycopg2.connect(
        host="localhost",
        database="course_rec",
        user="postgres",
        password="your_password_here"
    )
    return conn

# Helper to generate random referral code
def generate_referral_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
```

**Step 3.2: Update `get_current_user` method**
Modify `get_current_user` to leverage the new SQL logic so your whole app behaves smoothly:
```python
def get_current_user() -> dict | None:
    """Get the currently logged-in user from PostgreSQL."""
    email = session.get("user_email")
    if email:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_row = cur.fetchone()
        cur.close()
        conn.close()
        if user_row:
            return dict(user_row)
    return None
```

**Step 3.3: Authentication Routes (/onboard, /login, /logout)**
Replace your existing `/onboard` route and insert the other routes alongside it:
```python
# ── Authentication Routes ──────────────────────────────────────────
@app.route("/onboard", methods=["GET", "POST"])
def onboard():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        level = request.form.get("level", "Beginner")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("onboard"))

        conn = get_db_connection()
        cur = conn.cursor()

        # Check existing
        cur.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            flash("Profile already exists. Please log in!", "info")
            cur.close()
            conn.close()
            return redirect(url_for("login"))

        # Hash Password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        ref_code = generate_referral_code()
        referred_by = None
        
        # Check if user was referred (from session)
        session_ref_code = session.get("referred_by_code")
        if session_ref_code:
            cur.execute("SELECT id FROM users WHERE referral_code = %s", (session_ref_code,))
            ref_user = cur.fetchone()
            if ref_user:
                referred_by = ref_user[0]

        # Insert user
        cur.execute(
            """INSERT INTO users (name, email, password_hash, level, referral_code, referred_by)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (name, email, hashed, level, ref_code, referred_by)
        )
        new_user_id = cur.fetchone()[0]

        # If referred, track it and add friendship automatically!
        if referred_by:
            cur.execute(
                "INSERT INTO referrals (referrer_id, referred_user_id) VALUES (%s, %s)",
                (referred_by, new_user_id)
            )
            # Add to friendships bi-directionally
            cur.execute("INSERT INTO friendships (user_id, friend_id) VALUES (%s, %s), (%s, %s) ON CONFLICT DO NOTHING",
                        (referred_by, new_user_id, new_user_id, referred_by))

        conn.commit()
        cur.close()
        conn.close()

        session["user_email"] = email
        flash("Profile created successfully! Welcome aboard!", "success")
        return redirect(url_for("index"))

    return render_template("onboarding.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session["user_email"] = email
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
```

**Step 3.4: Referral & Friends Features**
Add the features to process clicks on referral URLs, and an endpoint to view friends.
```python
@app.route("/ref/<code>")
def handle_referral(code):
    """Saves the referred code in session and redirects to onboarding."""
    session["referred_by_code"] = code
    flash("Your friend invited you! Sign up below.", "success")
    return redirect(url_for("onboard"))

@app.route("/friends")
@require_user
def friends():
    """View friends and their mocked progress."""
    user = get_current_user()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all friends
    cur.execute("""
        SELECT u.name, u.email, u.level 
        FROM friendships f
        JOIN users u ON f.friend_id = u.id
        WHERE f.user_id = %s
    """, (user['id'],))
    
    friends_list = cur.fetchall()
    cur.close()
    conn.close()
    
    # Mocking progress for the UI
    for friend in friends_list:
        friend['mock_progress'] = random.randint(10, 95)
        
    return render_template("friends.html", friends=friends_list, referral_code=user['referral_code'])
```

---

## 4. New Templates & Edits

### Create `templates/login.html` (NEW FILE)
Create this file in your `templates` directory:
```html
{% extends "base.html" %}
{% block title %}Login — {{ t('app_name') }}{% endblock %}

{% block content %}
<div class="max-w-md mx-auto pt-12 animate-fade-in-up">
    <div class="glass-card-strong p-8">
        <h2 class="text-3xl font-bold mb-2 text-white">Welcome Back</h2>
        <p class="text-slate-400 text-sm mb-6">Login to your account to continue your journey.</p>
        
        <form method="POST" action="{{ url_for('login') }}" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Email</label>
                <input type="email" name="email" required 
                       class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-primary-500 transition-colors">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Password</label>
                <input type="password" name="password" required 
                       class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-primary-500 transition-colors">
            </div>
            <button type="submit" class="w-full py-3 mt-4 rounded-xl font-bold bg-gradient-to-r from-primary-600 to-primary-500 text-white hover:from-primary-500 hover:to-primary-400 shadow-lg shadow-primary-500/20 transition-all">
                Login
            </button>
        </form>
        <p class="mt-6 text-center text-sm text-slate-400">
            Don't have an account? <a href="{{ url_for('onboard') }}" class="text-primary-400 hover:text-primary-300 font-semibold">Sign up</a>
        </p>
    </div>
</div>
{% endblock %}
```

### Create `templates/friends.html` (NEW FILE)
```html
{% extends "base.html" %}
{% block title %}Friends Progress — {{ t('app_name') }}{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto pt-8 animate-fade-in-up">
    <div class="glass-card-strong p-8 mb-8">
        <h2 class="text-3xl font-bold text-white mb-2">🎁 Invite Friends</h2>
        <p class="text-slate-400 mb-4">Share this link directly with your friends. If they sign up, you'll instantly connect as friends!</p>
        <div class="flex items-center gap-4">
            <input type="text" readonly value="{{ request.host_url }}ref/{{ referral_code }}" 
                   class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none">
        </div>
    </div>

    <h2 class="text-2xl font-bold text-white mb-6"><i class="fa-solid fa-user-group me-2 text-primary-400"></i> Friend's Progress</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {% for f in friends %}
        <div class="glass-card p-6">
            <h3 class="font-bold text-lg text-white">{{ f.name }}</h3>
            <p class="text-sm text-slate-400 mb-4">{{ f.level }} Developer</p>
            
            <div class="relative w-full h-3 bg-white/10 rounded-full overflow-hidden">
                <div class="absolute top-0 left-0 h-full bg-gradient-to-r from-accent-400 to-accent-600 rounded-full transition-all" style="width: {{ f.mock_progress }}%"></div>
            </div>
            <p class="text-right text-xs mt-2 text-slate-400">{{ f.mock_progress }}% completed courses</p>
        </div>
        {% else %}
        <p class="text-slate-400 col-span-2">No friends yet. Invite someone using the link above!</p>
        {% endfor %}
    </div>
</div>
{% endblock %}
```


### Modifying `templates/onboarding.html`
In your `onboarding.html` file, add the **Password** field to the form (`<form method="POST">`):
```html
<!-- ADD THIS RIGHT BELOW THE EMAIL FIELD -->
<div>
    <label class="block text-sm font-medium text-slate-300 mb-2">Password</label>
    <div class="relative">
        <div class="absolute inset-y-0 start-0 pl-4 flex items-center pointer-events-none">
            <i class="fa-solid fa-lock text-slate-400"></i>
        </div>
        <input type="password" name="password" required placeholder="Choose a secure password"
               class="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-all shadow-inner">
    </div>
</div>
```

### Modifying `templates/base.html`
Look for `id="nav-onboard"` inside `<div class="desktop-nav ...">`. 
**Replace the current `{% else %} ... {% endif %}` block with this:**

```html
{% else %}
<a href="{{ url_for('login') }}" class="px-4 py-2 rounded-xl text-sm font-semibold bg-white/5 text-white hover:bg-white/10 transition-all border border-white/10">
    <i class="fa-solid fa-sign-in-alt me-1"></i>Login
</a>
<a href="{{ url_for('onboard') }}" class="px-4 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-primary-600 to-primary-500 text-white hover:from-primary-500 hover:to-primary-400 transition-all shadow-lg shadow-primary-500/20">
    <i class="fa-solid fa-rocket me-1"></i>{{ t('nav_onboard') }}
</a>
{% endif %}
```
Look for `d="nav-benefit"` inside the same block and **Add the Friends Tab** under the `{% if current_user %}` block:
```html
<a href="{{ url_for('friends') }}" class="px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-all">
    <i class="fa-solid fa-user-group me-1"></i>Friends
</a>
```
_Don't forget to add a tiny logout button in your User Avatar dropdown or simply:_
```html
<a href="{{ url_for('logout') }}" class="px-3 py-1.5 ms-2 rounded-full text-xs font-bold bg-red-500/20 text-red-300 hover:bg-red-500/40 transition-all">
    <i class="fa-solid fa-power-off"></i>
</a>
```

### Modifying `templates/course_detail.html`
Inside the sidebar code, right around the `<hr class="border-white/5">`, let's add the Share functionality:
```html
<!-- ADD "SHARE WITH FRIEND" RIGHT BELOW THE ENROLL CTA -->
<hr class="border-white/5 my-4">
<button onclick="navigator.clipboard.writeText('{{ request.host_url }}ref/{{ current_user.referral_code if current_user else '' }}'); alert('Link copied successfully!');"
   class="block w-full py-3 rounded-xl text-sm font-bold bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/40 transition-all text-center">
    <i class="fa-solid fa-share-nodes me-2"></i>Share with a Friend
</button>
```

---

## 6. How to run everything (Commands)

1. Open your terminal in VS Code (or Git Bash / PowerShell).
2. Install the new required dependencies directly (do it in your activated virtual environment if you have one):
   ```bash
   pip install psycopg2-binary bcrypt
   ```
3. Run your Flask app normally:
   ```bash
   python app.py
   # OR
   python course_rec/app.py 
   ```

## 7. How to test it (Step-by-step checklist)
1. **Database Connect**: Ensure `app.py` doesn't crash on start. It means PostgreSQL is running and credentials are good.
2. **Signup**: Go to `.localhost:5000/onboard`, create a profile with a password. You should see "Profile created successfully".
3. **Logout & Login**: Go hit the logout button, then try logging in `localhost:5000/login` with wrong password (should fail), then right password (should log in!).
4. **Friends Link**: From the navbar, click "Friends", grab your sharing link (e.g. `http://localhost:5000/ref/A1B2C3D4`).
5. **Incognito & Referral**: Open an Incognito Window, paste that `ref/...` link. It should redirect you to `/onboard` showing "Your friend invited you!".
6. **Connection Test**: Make a new account in incognito. Then go back to your main window > Friends page, and *boom* the new account should appear there with their Mock Progress! 🔥

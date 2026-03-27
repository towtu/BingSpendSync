# BingSpendSync

#### Video Demo: <URL HERE>

#### Description:

BingSpendSync is a personal expense tracking web application built with Flask and SQLite. It helps users take control of their finances by logging expenses, visualizing spending patterns, and setting category-based budgets — all through a clean, modern interface.

## Features

- **User Authentication** — Secure registration and login with hashed passwords (Werkzeug).
- **Expense Tracking** — Add, edit, and delete expenses with categories, descriptions, and dates.
- **Dashboard** — At-a-glance overview of monthly spending with interactive charts (Chart.js).
- **Category Breakdown** — Doughnut chart showing where your money goes each month.
- **Monthly Trends** — Bar chart displaying spending over the last 6 months.
- **Budget Management** — Set monthly spending limits per category with progress bars and alerts.
- **Expense History** — Full filterable history by category and month.
- **Responsive Design** — Works on desktop, tablet, and mobile.

## Project Structure

```
BingSpendSync/
├── app.py              # Main Flask application — routes, database init, all backend logic
├── helpers.py          # Helper functions: login_required decorator, USD formatting
├── requirements.txt    # Python dependencies
├── spendsync.db        # SQLite database (auto-created on first run)
├── static/
│   ├── css/
│   │   └── style.css   # Custom CSS — layout, cards, charts, responsive design
│   └── js/
│       └── app.js      # Client-side JavaScript — alert auto-dismiss, nav highlighting
├── templates/
│   ├── layout.html     # Base template — navbar, flash messages, footer, CDN imports
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── index.html      # Dashboard — stats, charts, budget status, recent transactions
│   ├── add.html        # Add new expense form
│   ├── edit.html       # Edit existing expense form
│   ├── history.html    # Full expense history with category/month filters
│   └── budgets.html    # Budget management — set limits, view progress
└── README.md
```

## Design Decisions

**Why Flask + SQLite?**
Flask is lightweight and ideal for a CS50 final project — it keeps things simple without sacrificing functionality. SQLite requires zero setup and stores everything in a single file, making it easy to develop and submit.

**Why a dashboard with charts?**
Numbers alone don't tell a story. The Chart.js-powered bar and doughnut charts give users an immediate visual sense of their spending habits without needing to scroll through tables. This was a deliberate choice to make the app feel useful, not just functional.

**Why category-based budgets?**
Most people don't overspend uniformly — they overspend in specific areas. Category budgets with color-coded progress bars (green → yellow → red) provide actionable feedback, not just data.

**Why this UI approach?**
I used Bootstrap 5 as the foundation but wrote extensive custom CSS to give the app a modern, polished feel with custom colors, card animations, gradient icons, and careful spacing. The goal was to make it look like a real product, not a homework assignment.

**Security considerations:**
- Passwords are hashed using Werkzeug's `generate_password_hash`
- All database queries use parameterized statements to prevent SQL injection
- Session-based authentication with `login_required` decorator
- Users can only access/modify their own data (user_id checks on every query)

## How to Run

```bash
pip install -r requirements.txt
flask run
```

Then open `http://127.0.0.1:5000` in your browser.

## Technologies Used

- **Python 3** / **Flask** — Backend framework
- **SQLite** (via CS50 library) — Database
- **HTML5** / **Jinja2** — Templating
- **CSS3** / **Bootstrap 5** — Styling and responsive layout
- **JavaScript** / **Chart.js** — Interactive charts and client-side behavior
- **Werkzeug** — Password hashing

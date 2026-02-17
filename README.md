# GymTracker

A Flask app to track gym attendance: login, dashboard, workout logging, and monthly progress. Uses SQLite (or Heroku Postgres), bcrypt for passwords, and a gym-themed UI.

## Routes

| Route | Description |
|-------|-------------|
| `/login` | Login with username and password (e.g. `user1` / `password123`) |
| `/dashboard` | Dashboard with total and monthly workout counts and motivational message |
| `/log_workout` | Log a gym visit (date and optional time), stored in `workouts` table |
| `/progress` | Number of gym visits this month and list of dates |

## Demo login

- **Username:** `user1`  
- **Password:** `password123`  

This user is created automatically on first run (SQLite or Postgres).

## Tech

- **Database:** SQLite by default; Heroku Postgres when `DATABASE_URL` is set.
- **Tables:** `users` (id, username, password, email), `workouts` (id, user_id, date).
- **Passwords:** Hashed with bcrypt before storage; login verifies with bcrypt.

## Local setup

1. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. Open http://127.0.0.1:5000 and log in with `user1` / `password123`.

## Deployment (Heroku)

See **[DEPLOY.md](DEPLOY.md)** for:

- Procfile and `gunicorn`
- Adding Heroku Postgres and using `DATABASE_URL`
- Setting `SECRET_KEY` and deploying with Git

## Security notes

- Set a strong `SECRET_KEY` in production (and on Heroku via `heroku config:set SECRET_KEY=...`).
- The demo user is for development; restrict or remove in production as needed.

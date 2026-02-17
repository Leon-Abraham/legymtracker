# Deploying GymTracker to Heroku

Follow these steps to deploy the Flask app on Heroku and connect it to Heroku Postgres.

## Prerequisites

- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed and logged in (`heroku login`)
- Git (app in a Git repo; Heroku deploys from Git)

## 1. Prepare the app

- **Procfile** (already in the project): tells Heroku how to run the app.
  ```
  web: gunicorn app:app
  ```
- **runtime.txt** (already in the project): pins the Python version, e.g. `python-3.11.7`.
- **requirements.txt**: must include `gunicorn` and `psycopg2-binary` for production and Postgres.

## 2. Create the Heroku app

From the project directory:

```bash
heroku create your-app-name
# or without a name: heroku create
```

## 3. Add Heroku Postgres

Attach the Heroku Postgres add-on (creates `DATABASE_URL` automatically):

```bash
heroku addons:create heroku-postgresql:mini
```

To see the database URL (optional):

```bash
heroku config:get DATABASE_URL
```

The app is already written to use `DATABASE_URL`: when it is set, it uses Postgres instead of SQLite.

## 4. Set a secret key

Set a strong secret key for Flask sessions:

```bash
heroku config:set SECRET_KEY="your-long-random-secret-key-here"
```

Generate a random key (example):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 5. Deploy from Git

If the project is not yet a Git repo:

```bash
git init
git add .
git commit -m "Initial commit"
```

Then deploy:

```bash
heroku git:remote -a your-app-name   # if you haven’t set the remote
git push heroku main
```

Use `git push heroku master` if your default branch is `master`.

## 6. Open the app and seed the demo user

- Open the app: `heroku open`
- On first request, the app creates the tables and seeds the demo user:
  - **Username:** `user1`
  - **Password:** `password123`

(You can change or remove this in production.)

## 7. Optional: run commands on Heroku

- One-off command (e.g. open a shell): `heroku run bash`
- Run the Flask app locally but using the Heroku Postgres DB:  
  `heroku run python app.py` (not recommended for production; use `gunicorn` via the Procfile instead)

## Summary

| Step | Action |
|------|--------|
| 1 | Procfile: `web: gunicorn app:app`; runtime.txt and requirements.txt in place |
| 2 | `heroku create` |
| 3 | `heroku addons:create heroku-postgresql:mini` (sets `DATABASE_URL`) |
| 4 | `heroku config:set SECRET_KEY="…"` |
| 5 | `git push heroku main` (or `master`) |
| 6 | Visit the app and log in with `user1` / `password123` |

The app uses **SQLite** when `DATABASE_URL` is not set (e.g. on your machine) and **Heroku Postgres** when `DATABASE_URL` is set on Heroku. No code change is required to switch.

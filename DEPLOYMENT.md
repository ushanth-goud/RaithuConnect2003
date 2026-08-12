# RaithuConnect deployment guide

## 1. GitHub
Create a new GitHub repository and upload this project. Do not upload `.env` or any real passwords.

## 2. Online MySQL
Create a MySQL database with your chosen provider. Run `mysql_commands.sql` against that database.

## 3. Render
Create a new Web Service from the GitHub repository. Render can use `render.yaml`, or enter:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app`

Set these environment variables in Render:

- `FLASK_SECRET_KEY` = a long random value (or let Render generate it)
- `MYSQL_HOST` = online MySQL host
- `MYSQL_PORT` = `3306` (unless your provider says otherwise)
- `MYSQL_USER` = online MySQL user
- `MYSQL_PASSWORD` = online MySQL password
- `MYSQL_DATABASE` = online MySQL database name

## 4. Important: image uploads
The included worker image upload currently stores files in `static/uploads`. This is fine for a basic demo, but Render web-service disks are not a permanent shared image store. For production, move uploaded images to object storage such as Cloudinary or S3.

## 5. Local testing
For XAMPP, copy `.env.example` to `.env` and set your local values, then run:

`pip install -r requirements.txt`

`python app.py`

The app will be available at `http://127.0.0.1:5000`.

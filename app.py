from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory
)

import mysql.connector
from mysql.connector import Error

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_babel import Babel, _

import os
import cloudinary
import cloudinary.uploader


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "change-this-secret-key"
)

app.config["BABEL_DEFAULT_LOCALE"] = "en"
app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"


# ============================================================
# LANGUAGE
# ============================================================

def get_locale():
    return (
        session.get("lang")
        or request.args.get("lang")
        or "en"
    )


babel = Babel(
    app,
    locale_selector=get_locale
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    5 * 1024 * 1024
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    """
    Create a fresh MySQL connection.

    Local development:
        MYSQL_HOST=localhost
        MYSQL_PORT=3306
        MYSQL_USER=root
        MYSQL_PASSWORD=
        MYSQL_DATABASE=rc_project

    Production:
        Set the same environment variables
        in your hosting platform.
    """

    return mysql.connector.connect(

        host=os.environ.get(
            "MYSQL_HOST",
            "localhost"
        ),

        port=int(
            os.environ.get(
                "MYSQL_PORT",
                "3306"
            )
        ),

        user=os.environ.get(
            "MYSQL_USER",
            "root"
        ),

        password=os.environ.get(
            "MYSQL_PASSWORD",
            ""
        ),

        database=os.environ.get(
            "MYSQL_DATABASE",
            "rc_project"
        ),

        connection_timeout=10
    )


# ============================================================
# IMAGE VALIDATION
# ============================================================

def allowed_image(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in {
            "jpg",
            "jpeg",
            "png",
            "gif",
            "webp"
        }
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "landingpage.html"
    )


# ============================================================
# SIGN UP
# ============================================================

@app.route(
    "/sign_up",
    methods=["GET", "POST"]
)
def sign_up():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not email or not password:

            flash(
                _("Please fill in all fields."),
                "danger"
            )

            return render_template(
                "sign_up.html"
            )

        db = None

        try:

            db = get_db()

            cursor = db.cursor()

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            if cursor.fetchone():

                flash(
                    _("Email already registered."),
                    "danger"
                )

                return render_template(
                    "sign_up.html"
                )

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    username,
                    email,
                    generate_password_hash(
                        password
                    )
                )
            )

            db.commit()

            flash(
                _("Account created successfully!"),
                "success"
            )

            return redirect(
                url_for("sign_in")
            )

        except Error as err:

            if db:
                db.rollback()

            print(
                "Sign up database error:",
                err
            )

            flash(
                _(
                    "Unable to create account. "
                    "Check the database configuration."
                ),
                "danger"
            )

        finally:

            if db and db.is_connected():

                db.close()

    return render_template(
        "sign_up.html"
    )


# ============================================================
# SIGN IN
# ============================================================

@app.route(
    "/sign_in",
    methods=["GET", "POST"]
)
def sign_in():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                _("Please enter email and password."),
                "danger"
            )

            return render_template(
                "sign_in.html"
            )

        db = None

        try:

            db = get_db()

            cursor = db.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    password
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user[1],
                password
            ):

                session["user_id"] = user[0]

                flash(
                    _("Login successful!"),
                    "success"
                )

                return redirect(
                    url_for("homepage")
                )

            flash(
                _("Invalid email or password."),
                "danger"
            )

        except Error as err:

            print(
                "Login database error:",
                err
            )

            flash(
                _(
                    "Unable to login. "
                    "Check the database configuration."
                ),
                "danger"
            )

        finally:

            if db and db.is_connected():

                db.close()

    return render_template(
        "sign_in.html"
    )


# ============================================================
# HOMEPAGE
# ============================================================

@app.route("/homepage")
def homepage():

    return render_template(
        "homepage.html"
    )


# ============================================================
# REGISTER WORKER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        work_type = request.form.get(
            "work_type",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        contact = request.form.get(
            "contact",
            ""
        ).strip()

        availability = request.form.get(
            "availability",
            ""
        ).strip()

        rating = request.form.get(
            "rating",
            "5"
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not all(
            [
                name,
                work_type,
                location,
                contact,
                availability
            ]
        ):

            flash(
                _("Please fill in all required fields."),
                "danger"
            )

            return render_template(
                "register.html"
            )


        # ----------------------------------------------------
        # INITIAL RATING
        # ----------------------------------------------------

        try:

            rating_value = max(
                1,
                min(
                    5,
                    int(rating)
                )
            )

        except ValueError:

            rating_value = 5


        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        try:

            price_value = float(price)

            if price_value < 0:

                price_value = 0

        except ValueError:

            price_value = 0


        # ----------------------------------------------------
        # CLOUDINARY IMAGE
        # ----------------------------------------------------

        image_url = None

        image = request.files.get(
            "image"
        )

        if image and image.filename:

            if not allowed_image(
                image.filename
            ):

                flash(
                    _(
                        "Please upload a JPG, JPEG, "
                        "PNG, GIF or WEBP image."
                    ),
                    "danger"
                )

                return render_template(
                    "register.html"
                )

            try:

                upload_result = (
                    cloudinary
                    .uploader
                    .upload(
                        image,
                        folder="raithuconnect/workers"
                    )
                )

                image_url = (
                    upload_result["secure_url"]
                )

                print(
                    "Cloudinary image uploaded successfully:",
                    image_url
                )

            except Exception as err:

                print(
                    "Cloudinary upload error:",
                    err
                )

                flash(
                    _("Unable to upload worker image."),
                    "danger"
                )

                return render_template(
                    "register.html"
                )


        # ----------------------------------------------------
        # SAVE WORKER
        # ----------------------------------------------------

        db = None

        try:

            db = get_db()

            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO workers
                (
                    name,
                    work_type,
                    location,
                    contact,
                    availability,
                    rating,
                    image_filename,
                    price
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    work_type,
                    location,
                    contact,
                    availability,
                    rating_value,
                    image_url,
                    price_value
                )
            )

            db.commit()

            flash(
                _("Worker registered successfully!"),
                "success"
            )

            return redirect(
                url_for("display")
            )

        except Error as err:

            if db:

                db.rollback()

            print(
                "Worker registration error:",
                err
            )

            flash(
                _("Unable to register worker."),
                "danger"
            )

        finally:

            if db and db.is_connected():

                db.close()


    return render_template(
        "register.html"
    )


# ============================================================
# DISPLAY WORKERS
# ============================================================

@app.route("/display")
def display():

    work_type = request.args.get(
        "work_type",
        ""
    ).strip()

    location = request.args.get(
        "location",
        ""
    ).strip()

    availability = request.args.get(
        "availability",
        ""
    ).strip()


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Rating is now calculated from feedback table.
    #
    # AVG(feedback.rating)
    #
    # COUNT(feedback.id)
    #
    # This means the rating automatically changes when
    # users submit new feedback.
    # --------------------------------------------------------

    query = """
        SELECT
            w.id,
            w.name,
            w.work_type,
            w.location,
            w.contact,
            w.availability,

            COALESCE(
                ROUND(
                    AVG(f.rating),
                    1
                ),
                w.rating,
                0
            ) AS average_rating,

            w.image_filename,
            w.price,

            COUNT(f.id) AS review_count

        FROM workers w

        LEFT JOIN feedback f
            ON w.id = f.worker_id

        WHERE 1=1
    """


    params = []


    # --------------------------------------------------------
    # WORK TYPE FILTER
    # --------------------------------------------------------

    if work_type:

        query += """
            AND w.work_type = %s
        """

        params.append(
            work_type
        )


    # --------------------------------------------------------
    # LOCATION FILTER
    # --------------------------------------------------------

    if location:

        query += """
            AND w.location = %s
        """

        params.append(
            location
        )


    # --------------------------------------------------------
    # AVAILABILITY FILTER
    # --------------------------------------------------------

    if availability:

        query += """
            AND w.availability = %s
        """

        params.append(
            availability
        )


    # --------------------------------------------------------
    # GROUP BY
    # --------------------------------------------------------

    query += """
        GROUP BY
            w.id,
            w.name,
            w.work_type,
            w.location,
            w.contact,
            w.availability,
            w.rating,
            w.image_filename,
            w.price

        ORDER BY
            w.id DESC
    """


    db = None

    workers = []


    try:

        db = get_db()

        cursor = db.cursor()

        cursor.execute(
            query,
            params
        )

        workers = cursor.fetchall()

    except Error as err:

        print(
            "Display database error:",
            err
        )

        flash(
            _(
                "Unable to load workers. "
                "Check the database configuration."
            ),
            "danger"
        )

    finally:

        if db and db.is_connected():

            db.close()


    return render_template(
        "display.html",
        workers=workers
    )


# ============================================================
# WORKER PROFILE
# ============================================================

@app.route(
    "/profile/<int:id>"
)
def profile(id):

    db = None

    try:

        db = get_db()

        cursor = db.cursor()


        # ----------------------------------------------------
        # GET WORKER + REAL RATING
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT

                w.id,
                w.name,
                w.work_type,
                w.location,
                w.contact,
                w.availability,

                COALESCE(
                    ROUND(
                        AVG(f.rating),
                        1
                    ),
                    w.rating,
                    0
                ) AS average_rating,

                w.image_filename,
                w.price,

                COUNT(f.id) AS review_count

            FROM workers w

            LEFT JOIN feedback f
                ON w.id = f.worker_id

            WHERE w.id = %s

            GROUP BY
                w.id,
                w.name,
                w.work_type,
                w.location,
                w.contact,
                w.availability,
                w.rating,
                w.image_filename,
                w.price
            """,
            (id,)
        )


        worker = cursor.fetchone()


        if not worker:

            return "Worker not found", 404


        # ----------------------------------------------------
        # GET ALL REVIEWS FOR THIS WORKER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                rating,
                comment
            FROM feedback
            WHERE worker_id = %s
            ORDER BY id DESC
            """,
            (id,)
        )


        feedback_list = cursor.fetchall()


        return render_template(
            "profile.html",
            worker=worker,
            feedback_list=feedback_list
        )


    except Error as err:

        print(
            "Profile database error:",
            err
        )

        return "Database error", 500


    finally:

        if db and db.is_connected():

            db.close()


# ============================================================
# FEEDBACK
# ============================================================

@app.route(
    "/feedback/<int:id>",
    methods=["GET", "POST"]
)
def submit_feedback(id):

    db = None

    try:

        db = get_db()

        cursor = db.cursor()


        # ----------------------------------------------------
        # GET WORKER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                name
            FROM workers
            WHERE id = %s
            """,
            (id,)
        )


        worker = cursor.fetchone()


        if not worker:

            return "Worker not found", 404


        # ----------------------------------------------------
        # SUBMIT FEEDBACK
        # ----------------------------------------------------

        if request.method == "POST":

            rating = request.form.get(
                "rating",
                ""
            )

            comment = request.form.get(
                "comment",
                ""
            ).strip()


            try:

                rating_value = int(
                    rating
                )

            except ValueError:

                rating_value = 0


            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            if (
                rating_value not in range(1, 6)
                or not comment
            ):

                flash(
                    _(
                        "Please provide a valid "
                        "rating and feedback."
                    ),
                    "danger"
                )

                return render_template(
                    "feedback.html",
                    worker=worker
                )


            # ------------------------------------------------
            # INSERT REVIEW
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO feedback
                (
                    worker_id,
                    rating,
                    comment
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    id,
                    rating_value,
                    comment
                )
            )


            db.commit()


            # ------------------------------------------------
            # CALCULATE NEW AVERAGE
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    ROUND(
                        AVG(rating),
                        1
                    )
                FROM feedback
                WHERE worker_id = %s
                """,
                (id,)
            )


            result = cursor.fetchone()

            new_average = result[0]


            # ------------------------------------------------
            # UPDATE WORKERS TABLE
            #
            # This keeps workers.rating synchronized with
            # the real feedback average.
            # ------------------------------------------------

            cursor.execute(
                """
                UPDATE workers
                SET rating = %s
                WHERE id = %s
                """,
                (
                    new_average,
                    id
                )
            )


            db.commit()


            flash(
                _(
                    "Feedback submitted successfully!"
                ),
                "success"
            )


            return redirect(
                url_for(
                    "profile",
                    id=id
                )
            )


        # ----------------------------------------------------
        # SHOW FEEDBACK PAGE
        # ----------------------------------------------------

        return render_template(
            "feedback.html",
            worker=worker
        )


    except Error as err:

        if db:

            db.rollback()


        print(
            "Feedback database error:",
            err
        )


        flash(
            _("Unable to submit feedback."),
            "danger"
        )


        return redirect(
            url_for(
                "profile",
                id=id
            )
        )


    finally:

        if db and db.is_connected():

            db.close()


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# CONTACT
# ============================================================

@app.route(
    "/contact",
    methods=["GET", "POST"]
)
@app.route(
    "/contact_us",
    methods=["GET", "POST"]
)
def contact():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()


        if not name or not email or not message:

            flash(
                _("Please fill in all fields."),
                "danger"
            )

            return render_template(
                "contact.html"
            )


        db = None


        try:

            db = get_db()

            cursor = db.cursor()


            cursor.execute(
                """
                INSERT INTO contact_messages
                (
                    name,
                    email,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    email,
                    message
                )
            )


            db.commit()


            flash(
                _(
                    "Your message has been "
                    "sent successfully!"
                ),
                "success"
            )


        except Error as err:

            if db:

                db.rollback()


            print(
                "Contact database error:",
                err
            )


            flash(
                _("Unable to send your message."),
                "danger"
            )


        finally:

            if db and db.is_connected():

                db.close()


    return render_template(
        "contact.html"
    )


# ============================================================
# SERVICE WORKER
# ============================================================

@app.route("/sw.js")
def service_worker():

    return send_from_directory(
        os.path.join(
            app.root_path,
            "static"
        ),
        "sw.js",
        mimetype="application/javascript"
    )


# ============================================================
# LANGUAGE
# ============================================================

@app.route(
    "/set_language/<language>"
)
def set_language(language):

    session["lang"] = language

    return redirect(
        request.referrer
        or url_for("home")
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )


    app.run(
        host="0.0.0.0",
        port=port,

        debug=(
            os.environ.get(
                "FLASK_DEBUG",
                "0"
            ) == "1"
        )
    )

import os
import pytz
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt

load_dotenv()

# Set up Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

# Set up database configurations
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'BlogPost.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize DB
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Initialize Bcrypt
bcrypt = Bcrypt(app)  # To hash passwords

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# UTC = pytz.utc
IST = pytz.timezone('Asia/Kolkata')

# Function to get current IST time
def get_ist_time():
    return datetime.now(IST)

# User Model Class
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Model
class Blog(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=get_ist_time)
    update_date = db.Column(db.DateTime, default=get_ist_time, onupdate=get_ist_time)

    def __repr__(self):
        return f'<Blog {self.title}>'


# Create tables in the database
with app.app_context():
    db.create_all()
    print("Database tables created successfully")


# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register API
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Gets form input for username, email, and password.
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or email already exists. Please choose another.", 'danger')
            return redirect(url_for('register'))

        # Hash the password
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create the user
        new_user = User(
            username=username,
            email=email,
            password=hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!", 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login API
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Accepts username and password.
        username = request.form['username']
        password = request.form['password']
        # Retrieves the user from the database.
        user = User.query.filter_by(username=username).first()

        # Verifies the password with Bcrypt.
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html')

# Logout API
@app.route('/logout')
@login_required
def logout():
    # Logs the user out of the session.
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# Homepage - list of blogs and create form
@app.route('/')
def home():
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('home.html', blogs=blogs)


# Protect routes with Authentication
@app.route('/createblog')
def create():
    return render_template('createblog.html')


# Detail page - shows a specific blog post
@app.route('/blog/<int:id>')
def detail(id):
    blog = Blog.query.get_or_404(id)
    return render_template('detail.html', blog=blog)

@app.route('/listblogs')
def listblogs():
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('listblogs.html', blogs=blogs)

@app.route('/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Blog.query.get_or_404(id)

    try:
        # Delete photo from the static folder
        if post_to_delete.image_filename:
            # join (static folder path, the uploads directory, and the image filename).
            photo_path = os.path.join(current_app.static_folder, 'uploads', post_to_delete.image_filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)

        # Delete the blog post from the database
        db.session.delete(post_to_delete)
        db.session.commit()

        # Return a message
        flash('Blog Post Was Deleted!')
        return redirect(url_for('listblogs'))

    except Exception as e:
        print(f"Error deleting post: {e}")
        flash("Oops there is some problem deleting posts")
        return redirect(url_for('listblogs'))

@app.route('/posts/edits/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_blog(id):
    blog = Blog.query.get_or_404(id)

    if request.method == 'POST':
        blog.title = request.form['title']
        blog.body = request.form['body']

        # Edit Image
        file = request.files.get('file')  # Getting the uploaded file
        if file and file.filename:  # Checking if a new file is uploaded
            # Delete the old image if exists
            if blog.image_filename:
                old_photo_path = os.path.join(current_app.static_folder, 'uploads', blog.image_filename)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)

            # Save the new image
            new_filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)
            blog.image_filename = new_filename  # Update the blog's image filename

        # Remove existing Image (Optional)
        elif 'remove_image' in request.form:
            if blog.image_filename:
                old_photo_path = os.path.join(current_app.static_folder, 'uploads', blog.image_filename)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)
                blog.image_filename = None

        # Commit the changes to the database
        db.session.commit()
        flash('Blog post updated successfully')
        return redirect(url_for('listblogs'))
    else:
        return render_template('edit.html', blog=blog, current_image=blog.image_filename)

# Handle form submission
@app.route('/submit', methods=['POST'])
@login_required
def submit():
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()

    if not title or not body:
        flash('Title and body are required')
        return redirect(url_for('create'))

    file = request.files.get('file')
    image_filename = None

    # Handle file upload
    if file and file.filename:
        filename = secure_filename(file.filename)
        if filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_filename = filename
        else:
            flash('File type not allowed')
            return redirect(url_for('create'))

    # Save blog to database
    new_blog = Blog(
        title=title,
        body=body,
        image_filename=image_filename
    )
    db.session.add(new_blog)
    db.session.commit()

    flash('Blog post created successfully')
    return redirect(url_for('success', blog_id=new_blog.id))

# Success page - shows confirmation and link to detail
@app.route('/success/<int:blog_id>')
def success(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template('success.html', blog=blog)

# Main
if __name__ == '__main__':
    app.run(debug=True)

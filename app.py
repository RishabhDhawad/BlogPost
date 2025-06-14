import os
import pytz
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application and configure basic settings
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

# Configure database and file upload settings
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'BlogPost.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db = SQLAlchemy(app)

# Configure Flask-Login for user authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set timezone to Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    """Returns current time in Indian Standard Time (IST)"""
    return datetime.now(IST)

# User Model for authentication and user management
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Blog Model for storing blog posts
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

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully")

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback to load user from database"""
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration
    GET: Display registration form
    POST: Process registration form and create new user
    """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check for existing user
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or email already exists. Please choose another.", 'danger')
            return redirect(url_for('register'))

        # Create new user with hashed password
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!", 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login
    GET: Display login form
    POST: Process login form and authenticate user
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout and redirect to home page"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/')
def home():
    """Display homepage with list of all blog posts"""
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('home.html', blogs=blogs)

@app.route('/createblog')
def create():
    """Display blog creation form"""
    return render_template('createblog.html')

@app.route('/blog/<int:id>')
def detail(id):
    """Display detailed view of a specific blog post"""
    blog = Blog.query.get_or_404(id)
    return render_template('detail.html', blog=blog)

@app.route('/listblogs')
def listblogs():
    """Display list of all blog posts"""
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('listblogs.html', blogs=blogs)

@app.route('/delete/<int:id>')
@login_required
def delete_post(id):
    """
    Delete a blog post and its associated image
    Requires user authentication
    """
    post_to_delete = Blog.query.get_or_404(id)

    try:
        # Delete associated image file
        if post_to_delete.image_filename:
            photo_path = os.path.join(current_app.static_folder, 'uploads', post_to_delete.image_filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)

        # Delete blog post from database
        db.session.delete(post_to_delete)
        db.session.commit()
        flash('Blog Post Was Deleted!')
        return redirect(url_for('listblogs'))

    except Exception as e:
        print(f"Error deleting post: {e}")
        flash("Oops there is some problem deleting posts")
        return redirect(url_for('listblogs'))

@app.route('/posts/edits/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_blog(id):
    """
    Handle blog post editing
    GET: Display edit form
    POST: Process edit form and update blog post
    Requires user authentication
    """
    blog = Blog.query.get_or_404(id)

    if request.method == 'POST':
        blog.title = request.form['title']
        blog.body = request.form['body']

        # Handle image updates
        file = request.files.get('file')
        if file and file.filename:
            # Remove old image if exists
            if blog.image_filename:
                old_photo_path = os.path.join(current_app.static_folder, 'uploads', blog.image_filename)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)

            # Save new image
            new_filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)
            blog.image_filename = new_filename

        # Handle image removal
        elif 'remove_image' in request.form:
            if blog.image_filename:
                old_photo_path = os.path.join(current_app.static_folder, 'uploads', blog.image_filename)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)
                blog.image_filename = None

        db.session.commit()
        flash('Blog post updated successfully')
        return redirect(url_for('listblogs'))
    else:
        return render_template('edit.html', blog=blog, current_image=blog.image_filename)

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    """
    Handle new blog post submission
    Processes form data and saves new blog post
    Requires user authentication
    """
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()

    if not title or not body:
        flash('Title and body are required')
        return redirect(url_for('create'))

    file = request.files.get('file')
    image_filename = None

    # Handle image upload
    if file and file.filename:
        filename = secure_filename(file.filename)
        if filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_filename = filename
        else:
            flash('File type not allowed')
            return redirect(url_for('create'))

    # Create and save new blog post
    new_blog = Blog(
        title=title,
        body=body,
        image_filename=image_filename
    )
    db.session.add(new_blog)
    db.session.commit()

    flash('Blog post created successfully')
    return redirect(url_for('success', blog_id=new_blog.id))

@app.route('/success/<int:blog_id>')
def success(blog_id):
    """Display success message after blog post creation"""
    blog = Blog.query.get_or_404(blog_id)
    return render_template('success.html', blog=blog)

if __name__ == '__main__':
    app.run(debug=True)

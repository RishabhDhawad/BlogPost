import os
from multiprocessing.spawn import old_main_modules

import pytz
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# Set up Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
basedir = os.path.abspath(os.path.dirname(__file__))

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'BlogPost.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize DB
db = SQLAlchemy(app)

# Create tables in the database
with app.app_context():
    db.create_all()

# UTC = pytz.utc
IST = pytz.timezone('Asia/Kolkata')
datetime_ist = datetime.now(IST)


# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Model
class Blog(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime_ist)
    update_date = db.Column(db.DateTime, default=datetime_ist, onupdate=datetime_ist)

    def __repr__(self):
        return f'<User {self.title}>'


# Homepage - list of blogs and create form
@app.route('/')
def home():
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('home.html', blogs=blogs)


# Detail page - shows a specific blog post
@app.route('/blog/<int:id>')
def detail(id):
    blog = Blog.query.get_or_404(id)
    return render_template('detail.html', blog=blog)


@app.route('/create')
def create():
    # blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('createblog.html')


@app.route('/listblogs')
def listblogs():
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('listblogs.html', blogs=blogs)


@app.route('/delete/<int:id>')
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
def edit_blog(id):
    blog = Blog.query.get_or_404(id)

    if request.method == 'POST':
        blog.title = request.form['title']
        blog.body = request.form['body']

        # Edit Image
        file = request.files.get('file') # Getting the uploaded file
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
            blog.image_filename = new_filename # Update the blog's image filename

        # Remove existing Image (Optional)
        elif 'remove_image' in request.form:
            if blog.image_filename:
                old_photo_path = os.path.join(current_app.static_folder, 'uploads', blog.image_filename)
                if os.path.exists(old_photo_path):
                    os.remove(old_photo_path)
                blog.image_filename = None


        # Commit the changes to the database
        db.session.commit()
        flash('blog post updated successfully')
        return redirect(url_for('listblogs'))
    else:
        return render_template('edit.html', blog=blog)


# Handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()

    if not title or not body:
        flash('Title and body are required')
        return redirect(url_for('home'))

    file = request.files.get('file')
    image_filename = None

    # Handle file upload
    if file and file.filename:
        filename = secure_filename(file.filename)
        # if filename and allowed_file(filename):
        if filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_filename = filename
        elif filename:
            flash('File type not allowed')
            return redirect(url_for('home'))

    # Save blog to database
    new_blog = Blog(
        title=title,
        body=body,
        image_filename=image_filename
    )
    db.session.add(new_blog)
    db.session.commit()

    # Redirect to success page with the new user's ID
    flash('Blog post created successfully')
    return redirect(url_for('success', blog_id=new_blog.id))


# Success page - shows confirmation and link to detail
@app.route('/success/<int:blog_id>')
def success(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template('success.html', blog=blog)


# Main
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

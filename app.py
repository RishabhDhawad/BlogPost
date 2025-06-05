import os
from datetime import datetime, UTC
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Set up Flask app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'BlogPost.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize DB
db = SQLAlchemy(app)

# Model
class Blog(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    imagePath = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    update_date = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def __repr__(self):
        return f'<User {self.title}>'

# Homepage - list of blogs
@app.route('/')
def index():
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('index.html', blogs=blogs)

# Detail page - shows a specific blog post
@app.route('/detail/<int:id>')
def detail(id):
    blog = Blog.query.get_or_404(id)
    return render_template('detail.html', blog=blog)

# Handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    title = request.form['title']
    body = request.form['body']
    file = request.files.get('file')

    image_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f'static/uploads/{filename}'

    # Save blog
    new_blog = Blog(title=title, body=body, imagePath=image_path)
    db.session.add(new_blog)
    db.session.commit()

    # Redirect to success page with the new user's ID
    return redirect(url_for('success', blog_id=new_blog.id))

# Success page - shows confirmation and link to detail
@app.route('/success/<int:blog_id>')
def success(blog_id):
    return render_template('success.html', blog_id=blog_id)

# Serve uploaded files (not always needed if using static URL)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Main
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

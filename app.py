import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Set up Flask app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'BlogPost.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy
db = SQLAlchemy(app)


# Define user (blog post) model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255), nullable = False)
    body = db.Column(db.Text, nullable = False)
    imagePath = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    update_date = db.Column(db.DateTime, default = datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.title}>'

# Create route that renders template
@app.route('/')
def index():
    users = User.query.order_by(User.created_date.desc()).all()
    return render_template('index.html', users=users)

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

    new_user = User(title=title, body=body, imagePath=image_path)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('index'))

# Serve uploaded files (optional if using /static/uploads)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

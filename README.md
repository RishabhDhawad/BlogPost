# 📝 Flask Blog Application

A simple and functional blog web app built with **Flask**, **SQLite**, and **SQLAlchemy**, allowing users to create blog posts with optional image uploads.

---

## 🚀 Features

- 🖋️ Create and submit blog posts
- 🖼️ Upload and display images (JPG, PNG, GIF, etc.)
- 🕒 Auto-generated timestamps (created & updated)
- 💾 SQLite database with SQLAlchemy ORM
- ⚡ Flash messages for user feedback
- 📄 Blog listing and individual detail pages

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite, SQLAlchemy
- **Frontend:** HTML, CSS (via templates)
- **Others:** Jinja2, Werkzeug

---

## 📂 Project Structure
    Flask_Blog/
    │
    ├── static/
    │ └── uploads/ # Uploaded images
    │
    ├── templates/
    │ ├── index.html # Homepage (blog list)
    │ ├── detail.html # Blog detail page
    │ └── success.html # Confirmation page
    │
    ├── BlogPost.db # SQLite database
    ├── app.py # Main Flask app
    └── README.md


---

## ▶️ Getting Started

### 1. Clone the repo
    
    git clone https://github.com/your-username/flask-blog-app.git
    cd flask-blog-app

### 2. Set up a virtual environment

    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows

### 3. Install dependencies

    pip install flask flask_sqlalchemy

### 4. Run the app

    python app.py

Visit http://127.0.0.1:5000/ in your browser.

## 📜 License
This project is licensed under the MIT License.

## 🙌 Acknowledgements

- Flask Documentation
- SQLAlchemy ORM
- Jinja2 Template Engine

## 💡 Author

Rishabh Dhawad


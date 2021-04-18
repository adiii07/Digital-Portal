from datetime import datetime
from portal import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id        = db.Column(db.Integer, primary_key=True)
    login_id  = db.Column(db.String, unique=True, nullable=False)
    user_type = db.Column(db.String, nullable=False)
    name      = db.Column(db.String, nullable=False)
    email     = db.Column(db.String, unique=True, nullable=False)
    school    = db.Column(db.String, nullable=False)
    password  = db.Column(db.String(60), nullable=False)
    posts     = db.relationship('Post', backref='author', lazy=True)
    replies   = db.relationship('Reply', backref='replier', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.login_id}', '{self.email}')"

class Post(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    title             = db.Column(db.String(100), nullable=False)
    date_posted       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content           = db.Column(db.Text, nullable=False)
    doc               = db.Column(db.String, nullable=True)
    assigned_doc_name = db.Column(db.String, nullable=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class Reply(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    date    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=True)
    post_id = db.Column(db.Integer, nullable=False)
    u_name  = db.Column(db.String, db.ForeignKey('user.name'), nullable=False)

    def __repr__(self):
        return f"Post('{self.user}', '{self.date}', '{self.post_id}')"

class Assignment(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    date_posted   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submitted_doc = db.Column(db.String, nullable=True)
    doc_name      = db.Column(db.String, nullable=True)
    post          = db.Column(db.Integer, nullable=False)
    st_name       = db.Column(db.String, db.ForeignKey('user.name'), nullable=False)

    def __repr__(self):
        return f"Post('{self.st_name}', '{self.date_posted}')"


from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class SkillAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    skills = db.Column(db.Text)
    domain = db.Column(db.String(100))
    status = db.Column(db.String(100))
    role = db.Column(db.String(100))

class RoadmapProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    domain = db.Column(db.String(100))
    step = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)

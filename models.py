from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Lecturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    room_id = db.Column(db.String(50))

    aliases = db.relationship('LecturerAlias', backref='lecturer', lazy=True)
    visits = db.relationship('VisitLog', backref='lecturer', lazy=True)


class LecturerAlias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(100), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), nullable=False)


class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="Unknown")
    matric_number = db.Column(db.String(20))
    encoding = db.Column(db.PickleType, nullable=False)

    visits = db.relationship('VisitLog', backref='visitor', lazy=True)


class VisitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor.id'), nullable=True)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), nullable=True)

    # Snapshot data
    lecturer_name_snapshot = db.Column(db.String(100))
    reason = db.Column(db.Text)
    image_path = db.Column(db.String(200))

    # STATUS COLUMN
    status = db.Column(db.String(20), default='Open', nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

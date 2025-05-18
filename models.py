from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    car_color = db.Column(db.String(50))
    car_type = db.Column(db.String(50))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    qr_code_path = db.Column(db.String(200))
    driver_photo_path = db.Column(db.String(200))

    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'driver_name': self.driver_name,
            'car_color': self.car_color,
            'car_type': self.car_type,
            'registration_date': self.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
            'qr_code_path': self.qr_code_path,
            'driver_photo_path': self.driver_photo_path
        }

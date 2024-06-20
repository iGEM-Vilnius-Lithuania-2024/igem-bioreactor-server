import os

from flask import Flask, request, jsonify
from sqlalchemy import CheckConstraint
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

DB_HOST = "dpg-cpq8g7ks1f4s73cgl3ug-a.frankfurt-postgres.render.com"
DB_NAME = "igem_bioreactor_db"
DB_USER = "ingvaras"
DB_PASS = os.getenv('DB_PASS')
DB_PORT = "5432"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Control(db.Model):
    __tablename__ = 'control'
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    mixing_speed = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        CheckConstraint('temperature > 0', name='check_temperature_positive'),
        CheckConstraint('mixing_speed >= 0 AND mixing_speed <= 255', name='check_mixing_speed_range'),
    )

with app.app_context():
    db.create_all()


@app.route('/control', methods=['GET'])
def get_control():
    control = Control.query.first()
    return jsonify({'temperature': control.temperature, 'mixing_speed': control.mixing_speed})


@app.route('/control/temperature', methods=['PUT'])
def update_temperature():
    data = request.get_json()
    temperature = data.get('temperature')
    if temperature is None or temperature <= 0:
        return jsonify({'error': 'Invalid temperature value'}), 400

    control = Control.query.first()
    control.temperature = temperature
    db.session.commit()
    return '', 204


@app.route('/control/mixing_speed', methods=['PUT'])
def update_mixing_speed():
    data = request.get_json()
    mixing_speed = data.get('mixing_speed')
    if mixing_speed is None or not (0 <= mixing_speed <= 255):
        return jsonify({'error': 'Invalid mixing speed value'}), 400

    control = Control.query.first()
    control.mixing_speed = mixing_speed
    db.session.commit()
    return '', 204


if __name__ == '__main__':
    app.run('0.0.0.0', 80)

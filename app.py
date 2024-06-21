import io

from flask import Flask, request, jsonify, send_file
from sqlalchemy import CheckConstraint
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from config import Config
from models.MesurementType import MeasurementType
from models.constants import get_measurement_attribute, YLABEL_DICT, TITLE_DICT

app = Flask(__name__)
app.config.from_object(Config)

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

class Measurement(db.Model):
    __tablename__ = 'measurement'
    timestamp = db.Column(db.DateTime, nullable=False, primary_key=True, index=True)
    temperature = db.Column(db.Float, nullable=False)
    ph = db.Column(db.Float, nullable=False)


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

@app.route('/measurement/insert_mock_data', methods=['POST'])
def insert_mock_data():
    start_time = datetime.now() - timedelta(hours=12)
    temperature = 37
    ph = 7.2
    for _ in range(720):
        timestamp = start_time + timedelta(minutes=_)
        temperature += random.uniform(-0.1, 0.1)
        ph += random.uniform(-0.05, 0.05)
        measurement = Measurement(timestamp=timestamp, temperature=temperature, ph=ph)
        db.session.add(measurement)
        db.session.commit()

    return '', 204


@app.route('/measurement', methods=['POST'])
def add_measurement():
    data = request.json

    timestamp_str = data.get('timestamp')
    temperature = data.get('temperature')
    ph = data.get('ph')

    if timestamp_str is None or temperature is None or ph is None:
        return jsonify({'error': 'timestamp, temperature, and ph are required fields'}), 400

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        return jsonify({'error': 'Invalid timestamp format'}), 400

    new_measurement = Measurement(timestamp=timestamp, temperature=temperature, ph=ph)
    db.session.add(new_measurement)

    try:
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.session.close()

@app.route('/measurement/<measurement_type>/png', methods=['GET'])
def get_measurement(measurement_type):
    try:
        measurement_type = MeasurementType(measurement_type)
    except ValueError:
        return jsonify({'error': 'Invalid measurement type'}), 400

    time_from = request.args.get('from')
    time_to = request.args.get('to')
    if time_from is None or time_to is None:
        return jsonify({'error': 'from and to query parameters are required'}), 400

    try:
        time_from = datetime.fromisoformat(time_from)
        time_to = datetime.fromisoformat(time_to)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    measurements = (Measurement.query
                    .filter(Measurement.timestamp >= time_from, Measurement.timestamp <= time_to)
                    .order_by(Measurement.timestamp)
                    .all())

    if not measurements:
        return jsonify({'error': 'No measurements found for the given time range'}), 404

    timestamps = [measurement.timestamp for measurement in measurements]
    values = [get_measurement_attribute(measurement_type)(measurement) for measurement in measurements]

    time_from_str = time_from.strftime('%m-%d %H:%M')
    time_to_str = time_to.strftime('%m-%d %H:%M')
    title = f'{TITLE_DICT[measurement_type]} from {time_from_str} to {time_to_str}'

    plt.figure()
    plt.plot(timestamps, values, linestyle='-', color='blue')
    plt.scatter(timestamps, values, color='blue', s=10)
    plt.xlabel('Time')
    plt.ylabel(YLABEL_DICT[measurement_type])
    plt.title(title)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.3)

    plt.xlim(min(timestamps) - (max(timestamps) - min(timestamps)) * 0.01)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')


if __name__ == '__main__':
    app.run('0.0.0.0', 80)

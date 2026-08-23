import logging
import os
import sqlite3
from datetime import datetime

import cv2
import face_recognition
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from ultralytics import YOLO

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(BASE_DIR, 'attendance.db'))
MODEL_PATH = os.getenv('YOLO_MODEL_PATH', os.path.join(BASE_DIR, 'yolov8n.pt'))
FACES_DIR = os.path.join(BASE_DIR, 'faces')
CSV_PATH = os.path.join(BASE_DIR, 'attendance.csv')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)
CORS(app)

os.makedirs(FACES_DIR, exist_ok=True)


def build_connection():
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.isolation_level = None  # autocommit
    return connection


db = build_connection()
cursor = db.cursor()

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )'''
)

try:
    model = YOLO(MODEL_PATH)
    logging.info('Loaded YOLO model from %s', MODEL_PATH)
except Exception as exc:
    logging.error('Failed to load YOLO model: %s', exc)
    raise

known_face_encodings = []
known_face_names = []


def load_known_faces():
    known_face_encodings.clear()
    known_face_names.clear()

    for file_name in sorted(os.listdir(FACES_DIR)):
        if not file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        label = os.path.splitext(file_name)[0]
        path = os.path.join(FACES_DIR, file_name)
        try:
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                logging.warning('No face encoding found in %s', path)
                continue
            known_face_encodings.append(encodings[0])
            known_face_names.append(label)
            logging.info('Loaded known face: %s', label)
        except Exception as exc:
            logging.warning('Skipping file %s: %s', path, exc)


load_known_faces()


def save_attendance_record(name: str):
    timestamp = datetime.now()
    cursor.execute('INSERT INTO attendance (name, timestamp) VALUES (?, ?)', (name, timestamp.isoformat(sep=' ')))
    df = pd.DataFrame({'name': [name], 'timestamp': [timestamp]})
    if os.path.exists(CSV_PATH):
        df.to_csv(CSV_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(CSV_PATH, index=False)


@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'service': 'Face Attendance System'})


@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file received.'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return jsonify({'error': 'Unable to decode the image.'}), 400

    height, width = image.shape[:2]
    try:
        # class 0 = 'person' in the COCO-pretrained model. YOLO is used here as a
        # fast coarse person localizer; face_recognition does the actual face
        # detection and matching within each person crop.
        results = model(image, classes=[0])
    except Exception:
        logging.exception('YOLO detection failed')
        return jsonify({'error': 'Face detection failed.'}), 500

    faces = []
    for result in results:
        for box in result.boxes:
            coords = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = coords
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width - 1, x2), min(height - 1, y2)
            face_crop = image[y1:y2, x1:x2]
            if face_crop.size:
                faces.append(face_crop)

    attendance_results = []
    for face_crop in faces:
        rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_face)
        if not encodings:
            attendance_results.append('Unknown')
            save_attendance_record('Unknown')
            continue

        matches = face_recognition.compare_faces(known_face_encodings, encodings[0], tolerance=0.55)
        name = 'Unknown'
        if True in matches:
            name = known_face_names[matches.index(True)]

        attendance_results.append(name)
        save_attendance_record(name)

    return jsonify({'attendance': attendance_results, 'detected_faces': len(faces)})


@app.route('/attendance', methods=['GET'])
def attendance_history():
    cursor.execute('SELECT name, timestamp FROM attendance ORDER BY timestamp DESC LIMIT 50')
    records = [{'name': row[0], 'timestamp': row[1]} for row in cursor.fetchall()]
    return jsonify({'records': records})


@app.route('/known', methods=['GET'])
def known_faces():
    return jsonify({'known_faces': known_face_names})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

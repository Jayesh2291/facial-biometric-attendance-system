# Face Attendance System

A working attendance application with a React frontend and Flask API backend.

## Key Features

- Person localization using YOLOv8, face detection/recognition using `face_recognition`
- Attendance persistence in SQLite and CSV
- Image upload UI with scan status and detected names
- API endpoints for detection, history, and known faces

## Setup

### Backend

1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   pip install -r requirements.txt
   ```

2. Optionally copy `.env.example` to `.env` at the repo root and adjust paths — the
   defaults (a local `attendance.db` SQLite file next to `app.py`) work out of the box,
   no database server required.

3. Place known face images in `backend/faces/`. Use file names such as `john.jpg` or
   `jane.png` — the file name (without extension) becomes the recognized name.

4. Start the backend:
   ```bash
   python app.py
   ```
   Runs on `http://localhost:5000`.

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the dev server:
   ```bash
   npm run dev
   ```

3. Open the app at `http://localhost:3000`

The frontend talks to `http://localhost:5000` by default; override with a
`VITE_API_BASE_URL` env var if your backend runs elsewhere.

## API Endpoints

- `POST /detect` — upload a face image (`image` field) and return recognized attendance
  names
- `GET /attendance` — return recent attendance records
- `GET /known` — list registered face names

## How detection works

YOLOv8 (the stock COCO-pretrained model) is used as a fast coarse localizer restricted
to the `person` class, then `face_recognition` does the actual face detection and
matching within each person crop. This two-stage approach avoids running full face
detection across an entire high-resolution frame when there's no one in most of it.

## Production Notes

- Use the React production build: `npm run build`
- Serve Flask with a production WSGI server such as Gunicorn for Linux deployments
- For multi-instance/concurrent-write deployments, swap SQLite for a real database
  server (the SQL used is simple and portable)
- Keep `backend/.env` secure and do not commit it
- Add more face images to `backend/faces/` for new users

## Troubleshooting

- If the backend cannot load the YOLO model, ensure `yolov8n.pt` is available in
  `backend/` and is readable.
- If image upload fails, use a JPEG or PNG file smaller than a few megabytes.
- `face_recognition`'s transitive dependency `face_recognition_models` is unmaintained
  and still imports the deprecated `pkg_resources` API — `requirements.txt` pins
  `setuptools<81` to keep it working. If you see a `ModuleNotFoundError: No module
  named 'pkg_resources'`, reinstall with that pin.

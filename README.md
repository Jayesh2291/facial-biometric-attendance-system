# Face Attendance System

A production-ready attendance application with a React frontend and Flask API backend.

## Key Features

- Face detection using YOLOv8
- Face recognition using `face_recognition`
- Attendance persistence in MySQL and CSV
- Image upload UI with scan status and detected names
- API endpoints for detection, history, and known faces

## Setup

### Backend

1. Install dependencies:
   ```bash
   cd backend
   python -m pip install -r requirements.txt
   ```

2. Create a `.env` file by copying `.env.example` and updating values:
   ```bash
   cd backend
   copy .env.example .env
   ```

3. Verify your MySQL server is running and credentials are correct. The backend will create the `attendance` database automatically if it does not exist.

4. Place known face images in `backend/faces/`. Use file names such as `john.jpg` or `jane.png`.

5. Start the backend:
   ```bash
   python app.py
   ```

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the React development server:
   ```bash
   npm start
   ```

3. Open the app at `http://localhost:3000`

## API Endpoints

- `POST /detect` — upload a face image and return recognized attendance names
- `GET /attendance` — return recent attendance records
- `GET /known` — list registered face names

## Production Notes

- Use the React production build: `npm run build`
- Serve Flask with a production WSGI server such as Gunicorn for Linux deployments
- Keep `backend/.env` secure and do not commit it
- Add more face images to `backend/faces/` for new users

## Troubleshooting

- If the backend cannot load the YOLO model, ensure `yolov8n.pt` is available in `backend/` and is readable.
- If image upload fails, use a JPEG or PNG file smaller than a few megabytes.
- For MySQL errors, confirm the credentials and database host in `.env`.

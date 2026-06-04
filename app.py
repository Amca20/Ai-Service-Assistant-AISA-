import cv2
import face_recognition
import numpy as np
import os
import json
import threading
import time
import re
import uuid 
import csv 
from io import StringIO 
from datetime import date 
from flask import make_response
from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from google import genai

# --- LOCAL IMPORTS ---
from models import db, Visitor, VisitLog, Lecturer, Admin, datetime
from utils import find_lecturer_by_fuzzy_name 

# ==========================================
# CONFIGURATION
# ==========================================
API_KEY = "AIzaSyCuK97tczg5RPo3PIerbv3CPGNxEd7tqUo"
client = genai.Client(api_key=API_KEY)

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this_in_prod"

# --- DATABASE CONFIG ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- MAIL CONFIG ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'danishbmohdrafid@gmail.com'
app.config['MAIL_PASSWORD'] = 'qnuu mwsd wzmk wxed' 
app.config['MAIL_DEFAULT_SENDER'] = ('AISA', 'danishbmohdrafid@gmail.com')

# Initialize Extensions
db.init_app(app)
mail = Mail(app)

CAPTURE_FOLDER = os.path.join('static', 'captures')
os.makedirs(CAPTURE_FOLDER, exist_ok=True)

# ==========================================
# 1. CRASH-PROOF CAMERA CLASS
# ==========================================
class VideoStream:
    def __init__(self, src=0, name="Camera"):
        self.name = name
        self.stream = cv2.VideoCapture(src)
        self.stopped = False
        self.lock = threading.Lock()
        
        # Check if camera opened
        if self.stream.isOpened():
            (self.grabbed, self.frame) = self.stream.read()
        else:
            self.grabbed = False
            self.frame = None
            print(f"!! WARNING: Could not open {name} (Source {src}) !!")

    def start(self):
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            if self.stream.isOpened():
                (grabbed, frame) = self.stream.read()
                with self.lock:
                    self.grabbed = grabbed
                    self.frame = frame
            time.sleep(0.01)

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.stopped = True
        self.stream.release()

# --- INITIALIZE CAMERAS ---
# Kiosk Camera (The one looking at the visitor)
kiosk_cam = VideoStream(src=0, name="Kiosk Cam").start()

# Room Camera (The one looking at the office/lecturer)
# Note: If this crashes, try changing src=1 to src=2
room_cam = VideoStream(src=1, name="Room Cam").start() 

# ==========================================
# 2. GLOBAL VARIABLES & HELPERS
# ==========================================
known_face_encodings = []
known_face_names = []

def load_faces():
    """Reloads known faces from the database."""
    global known_face_encodings, known_face_names
    with app.app_context():
        visitors = Visitor.query.all()
        known_face_encodings = [v.encoding for v in visitors]
        known_face_names = [v.name for v in visitors]
        print(f"--> System Loaded: {len(known_face_names)} known faces.")

def gen_frames():
    """Generates the feed for the Web UI (Kiosk Cam only)."""
    global known_face_encodings, known_face_names
    while True:
        frame = kiosk_cam.read()
        if frame is None:
            continue

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
            else:
                name = "Unregistered"
            face_names.append(name)

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            color = (0, 255, 0) if name != "Unregistered" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, bottom - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- ROOM CHECK FUNCTION ---
def check_room_availability():
    """
    Takes a snapshot from Room Cam (Cam 1) and counts faces.
    Returns: status_message, status_code
    """
    frame = room_cam.read()
    if frame is None:
        return "Camera Error (Check Connection)", "error"

    # Use standard HOG detection (fast enough for single frame)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Resize to speed up detection
    small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
    
    face_locs = face_recognition.face_locations(small_frame)
    count = len(face_locs)
    
    print(f"--> Room Cam Check: Found {count} faces.")
    
    if count == 0:
        return "Lecturer Not Currently in Office", "away"
    elif count == 1:
        return "Available and Notified. Please Wait.", "available"
    else:
        return "Currently Busy (Guest in Room). Notified.", "busy"

def send_notification_email(app, lecturer_email, lecturer_name, visitor_name, matric, reason, image_path):
    with app.app_context():
        if not lecturer_email:
            print("--> SKIP EMAIL: No email address found.")
            return
        try:
            msg = Message(subject=f"AISA Visitor: {visitor_name}", recipients=[lecturer_email])
            msg.body = f"""
            Hello {lecturer_name},
            
            A visitor has arrived at the kiosk:
            --------------------------------
            Name:   {visitor_name}
            Matric: {matric}
            Reason: {reason}
            --------------------------------
            
            Please attend to them or check the dashboard.
            """
            if image_path:
                full_path = os.path.join(app.root_path, 'static', image_path)
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as fp:
                        msg.attach("visitor.jpg", "image/jpeg", fp.read())
            
            mail.send(msg)
            print(f"--> EMAIL SENT SUCCESSFULLY to {lecturer_email}")
        except Exception as e:
            print(f"--> EMAIL FAILED: {e}")

# ==========================================
# 3. ROUTES
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/process_visit', methods=['POST'])
def process_visit():
    global known_face_encodings, known_face_names

    print("\n--- PROCESSING VISIT START ---")

    # 1. Get Text
    try:
        req_data = request.get_json()
        transcript = req_data.get('transcript', '')
        print(f"1. User said: {transcript}")
        
        if not transcript:
            return jsonify({"status": "error", "message": "No speech detected"}), 400
    except Exception as e:
        print(f"Error reading request: {e}")
        return jsonify({"status": "error", "message": "Bad Request"}), 400

    # 2. Capture Frame from KIOSK CAM
    frame_snapshot = None
    try:
        frame_snapshot = kiosk_cam.read() 
    except Exception as e:
        print(f"Camera Error: {e}")

    # 3. Process Face & Save Image (Temporarily)
    new_encoding = None
    image_filename = None
    
    if frame_snapshot is not None:
        try:
            filename = f"visit_{uuid.uuid4().hex[:8]}.jpg"
            save_path = os.path.join(CAPTURE_FOLDER, filename)
            cv2.imwrite(save_path, frame_snapshot)
            image_filename = f"captures/{filename}"
            print(f"   Image saved to: {image_filename}")

            small_frame = cv2.resize(frame_snapshot, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            rgb_small_frame = np.ascontiguousarray(rgb_small_frame)

            boxes = face_recognition.face_locations(rgb_small_frame)
            encodings = face_recognition.face_encodings(rgb_small_frame, boxes)

            if encodings:
                new_encoding = encodings[0]
        except Exception as e:
            print(f"   Face Rec/Save Error: {e}")

    # 4. Ask Gemini
    try:
        prompt = f"""
        Extract data from this visitor statement: "{transcript}"
        Fields needed: 'name', 'matric_number', 'host_name', 'reason'.
        If a field is missing, use "Unknown" or "".
        Return ONLY valid JSON.
        """
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=prompt
        )
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            return jsonify({"status": "error", "message": "AI could not understand you."})
    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({"status": "error", "message": "AI Processing Failed"})

    # --- NEW: VALIDATION STEP ---
    # Check if any required field is missing
    missing_fields = []
    
    # Check Name
    if data.get('name') in ["Unknown", "", None]: 
        missing_fields.append("Your Name")
        
    # Check Matric
    if data.get('matric_number') in ["Unknown", "", None]: 
        missing_fields.append("Matric Number")
        
    # Check Host (Who they want to meet)
    if data.get('host_name') in ["Unknown", "", None]: 
        missing_fields.append("Who to meet")
        
    # Check Reason
    if data.get('reason') in ["Unknown", "", None]: 
        missing_fields.append("Reason")

    # If ANYTHING is missing, STOP here!
    if missing_fields:
        error_msg = f"Please state: {', '.join(missing_fields)}"
        print(f"--> VALIDATION FAILED: {error_msg}")
        # Note: We do NOT delete the image or rollback, we just return error.
        # The user must try speaking again.
        return jsonify({"status": "validation_error", "message": error_msg})
    # ----------------------------

    # 5. Database & Logic (Only runs if validation passes)
    try:
        v_name = data.get('name')
        v_matric = data.get('matric_number')
        v_host_raw = data.get('host_name')
        v_reason = data.get('reason')

        lecturer_obj = find_lecturer_by_fuzzy_name(v_host_raw)
        final_host_name = lecturer_obj.name if lecturer_obj else v_host_raw
        data['host_name'] = final_host_name 

        # Check Room Availability
        room_msg, room_status = "Lecturer Not Found", "unknown"
        if lecturer_obj:
            room_msg, room_status = check_room_availability()
        
        data['room_message'] = room_msg
        data['room_status'] = room_status

        # Handle Visitor (Save/Update)
        visitor_id = None
        if new_encoding is not None:
            existing = Visitor.query.filter_by(matric_number=v_matric).first()
            if existing:
                existing.encoding = new_encoding
                existing.name = v_name
                visitor_id = existing.id
            else:
                new_v = Visitor(name=v_name, matric_number=v_matric, encoding=new_encoding)
                db.session.add(new_v)
                db.session.commit()
                visitor_id = new_v.id
        
        # Save Log
        new_log = VisitLog(
            visitor_id=visitor_id, 
            lecturer_id=lecturer_obj.id if lecturer_obj else None,
            lecturer_name_snapshot=final_host_name,
            reason=v_reason,
            image_path=image_filename
        )
        db.session.add(new_log)
        db.session.commit()

        # Send Email
        if lecturer_obj and lecturer_obj.email:
            email_thread = threading.Thread(
                target=send_notification_email, 
                args=(app, lecturer_obj.email, lecturer_obj.name, v_name, v_matric, v_reason, image_filename)
            )
            email_thread.start()

        if new_encoding is not None:
            load_faces()
            
        return jsonify({"status": "success", "data": data})

    except Exception as e:
        print(f"Database Error: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": "Database Save Failed"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid Credentials"
    return render_template('login.html', error=error)

# --- UPDATED ADMIN ROUTE (Includes Visitor Count) ---
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    # 1. Get all logs
    logs = VisitLog.query.order_by(VisitLog.timestamp.desc()).all()
    
    # 2. Calculate "Visitors Today"
    today_date = date.today()
    daily_count = sum(1 for log in logs if log.timestamp.date() == today_date)
    
    return render_template('admin.html', logs=logs, daily_count=daily_count)

# --- ROUTE FOR UPDATING STATUS ---
@app.route('/update_log_status', methods=['POST'])
def update_log_status():
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    log_id = data.get('log_id')
    new_status = data.get('status')
    
    log = VisitLog.query.get(log_id)
    if log:
        log.status = new_status
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Log not found'}), 404

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

# ==========================================
# DEBUGGING: VIEW ROOM CAMERA
# ==========================================
def gen_room_frames():
    while True:
        frame = room_cam.read()
        if frame is None: continue
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/check_cam')
def check_cam():
    """Go to http://127.0.0.1:5000/check_cam to see what Camera 2 sees"""
    return Response(gen_room_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/export_logs')
def export_logs():
    """Generates a CSV file of all logs for Excel."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    # 1. Query all logs
    logs = VisitLog.query.order_by(VisitLog.timestamp.desc()).all()
    
    # 2. Create CSV in memory
    si = StringIO()
    cw = csv.writer(si)
    
    # Header Row
    cw.writerow(['Status', 'Date', 'Time', 'Visitor Name', 'Matric Number', 'Meeting With', 'Reason', 'Image File'])
    
    # Data Rows
    for log in logs:
        # Handle cases where visitor/lecturer might be deleted or null
        v_name = log.visitor.name if log.visitor else "Unknown"
        v_matric = log.visitor.matric_number if log.visitor else "Unknown"
        host_name = log.lecturer.name if log.lecturer else log.lecturer_name_snapshot
        
        cw.writerow([
            log.status, 
            log.timestamp.strftime('%Y-%m-%d'),
            log.timestamp.strftime('%H:%M:%S'),
            v_name,
            v_matric,
            host_name,
            log.reason,
            log.image_path
        ])
        
    # 3. Create Response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=aisa_logs.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    with app.app_context(): load_faces()
    app.run(debug=True, use_reloader=False)
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, Vehicle
import cv2
import numpy as np
import easyocr
from ultralytics import YOLO
import qrcode
from datetime import datetime
import os
import json
from PIL import Image
from sklearn.cluster import KMeans
import logging
from main import detect_and_read_plate_with_yolo, get_dominant_color, closest_color

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5000",
            "http://localhost:5001",
            "https://your-username.github.io"  # Replace with your GitHub Pages domain
        ]
    }
})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/abualhassanbasim/Desktop/CVS/car-attendance-system/database/vehicles.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Initialize YOLO and EasyOCR
yolo_model = YOLO('yolov8n.pt')
reader = easyocr.Reader(['en'])

def generate_qr_code(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(json.dumps(data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    search_term = request.args.get('search', '')
    query = Vehicle.query
    if search_term:
        query = query.filter(
            (Vehicle.driver_name.ilike(f'%{search_term}%')) |
            (Vehicle.plate_number.ilike(f'%{search_term}%'))
        )
    vehicles = query.order_by(Vehicle.registration_date.desc()).all()
    return jsonify([vehicle.to_dict() for vehicle in vehicles])

@app.route('/api/detect_plate', methods=['POST'])
def detect_plate():
    try:
        # Input validation
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if not file:
            return jsonify({'error': 'Empty image file'}), 400

        # Save the uploaded image temporarily
        temp_image_path = os.path.join('static', 'temp_upload.jpg')
        file.save(temp_image_path)
        
        # Read the image for processing
        frame = cv2.imread(temp_image_path)
        if frame is None:
            return jsonify({'error': 'Could not read image file'}), 400

        # Initialize YOLO and EasyOCR
        model = YOLO('yolov8n.pt')
        reader = easyocr.Reader(['en'])
        vehicles = []

        results = model(frame)
        
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]

                if label in ['car', 'truck', 'bus', 'motorbike']:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cropped = frame[y1:y2, x1:x2]

                    # Detect dominant color
                    color_rgb = get_dominant_color(cropped)
                    color_name = closest_color(color_rgb)

                    # OCR with improved preprocessing
                    # Convert to grayscale
                    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
                    # Apply bilateral filter
                    denoised = cv2.bilateralFilter(gray, 11, 17, 17)
                    # Apply adaptive thresholding
                    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

                    # OCR with multiple preprocessing attempts
                    attempts = [
                        thresh,           # Binary threshold
                        denoised,         # Just denoised
                        gray,             # Just grayscale
                        cropped           # Original crop
                    ]

                    best_result = None
                    best_confidence = 0

                    for img in attempts:
                        ocr_result = reader.readtext(img, 
                                                   allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-',
                                                   decoder='beamsearch',
                                                   batch_size=1)
                        if ocr_result:
                            # Get result with highest confidence
                            result = max(ocr_result, key=lambda x: x[2])
                            if result[2] > best_confidence:
                                best_result = result
                                best_confidence = result[2]

                    if best_result and best_confidence > 0.5:
                        plate_text = ''.join(c for c in best_result[1] if c.isalnum() or c == '-')
                        vehicles.append({
                            'plate_number': plate_text,
                            'color': color_name,
                            'type': label,
                            'confidence': float(best_confidence),
                            'detection_score': float(box.conf[0])
                        })

                        app.logger.debug(f"Detected plate: {plate_text} with confidence: {best_confidence:.2f}")

        # Clean up temporary file
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

        if not vehicles:
            return jsonify({'error': 'No license plates detected with sufficient confidence. Please ensure the plate is clearly visible and try again.'}), 400

        return jsonify(vehicles)

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/api/register_vehicle', methods=['POST'])
def register_vehicle():
    try:
        # Get form data
        plate_number = request.form.get('plate_number')
        driver_name = request.form.get('driver_name')
        car_color = request.form.get('car_color')
        car_type = request.form.get('car_type')
        
        # Check if vehicle already exists
        existing_vehicle = Vehicle.query.filter_by(plate_number=plate_number).first()
        if existing_vehicle:
            return jsonify({'error': 'Vehicle already registered'}), 400
            
        # Handle photo upload
        photo = request.files.get('driver_photo')
        if not photo:
            return jsonify({'error': 'Driver photo is required'}), 400
            
        # Save driver photo
        photo_filename = f"static/driver_photos/{plate_number}_{secure_filename(photo.filename)}"
        os.makedirs(os.path.dirname(photo_filename), exist_ok=True)
        photo.save(photo_filename)
        
        # Generate QR code
        data = {
            'plate_number': plate_number,
            'driver_name': driver_name,
            'car_color': car_color,
            'car_type': car_type
        }
        qr_filename = f"static/qr_codes/{plate_number}.png"
        os.makedirs(os.path.dirname(qr_filename), exist_ok=True)
        generate_qr_code(data, qr_filename)
        
        # Create new vehicle record
        new_vehicle = Vehicle(
            plate_number=plate_number,
            driver_name=driver_name,
            car_color=car_color,
            car_type=car_type,
            qr_code_path=qr_filename,
            driver_photo_path=photo_filename
        )
        
        db.session.add(new_vehicle)
        db.session.commit()
        
        return jsonify(new_vehicle.to_dict())
        
    except Exception as e:
        app.logger.error(f"Error registering vehicle: {str(e)}")
        return jsonify({'error': f'Error registering vehicle: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5002)
